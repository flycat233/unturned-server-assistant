from fastapi import FastAPI, Depends, HTTPException, Security
from fastapi.security import APIKeyHeader
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from settings import get_config
from utils import logger, is_superuser, send_onebot_message
from database import get_db
from models import QQBotPlayers, PlayerStats, DailySignIn, GroupManagement, Announcements
import uvicorn
import asyncio
import threading

# 获取配置
config = get_config()

# API密钥验证
API_KEY_HEADER = APIKeyHeader(name="Authorization", auto_error=False)

def verify_api_key(api_key: str = Security(API_KEY_HEADER)):
    # 空API密钥允许（如果配置中未设置API_KEY）
    if not config.API_KEY:
        return True
    
    # 验证API密钥格式
    if not api_key or not api_key.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="无效的API密钥格式")
    
    # 提取并验证密钥
    token = api_key[7:]  # 移除 "Bearer " 前缀
    if token != config.API_KEY:
        raise HTTPException(status_code=401, detail="无效的API密钥")
    
    return True

# 创建FastAPI应用
app = FastAPI(title="Unturned服务器助手API", version=config.VERSION)

# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 在生产环境中应该限制来源
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API模型定义
class PlayerInfo(BaseModel):
    qq_id: str
    steam_id: str
    nickname: Optional[str] = None
    points: int
    bind_time: Optional[str] = None
    last_login: Optional[str] = None

class ServerStatusResponse(BaseModel):
    is_online: bool
    players: int
    max_players: int
    map: str
    message: str

class BroadcastMessage(BaseModel):
    content: str
    target_groups: Optional[List[str]] = None

class AnnouncementCreate(BaseModel):
    title: str
    content: str
    created_by: str

# API路由
@app.get("/", tags=["根目录"])
def read_root():
    return {
        "name": "Unturned服务器助手API",
        "version": config.VERSION,
        "status": "running"
    }

@app.get("/api/status", tags=["状态"], dependencies=[Depends(verify_api_key)])
def get_status():
    """获取机器人状态"""
    from core import get_bot_status
    status = get_bot_status()
    
    # 添加API服务状态
    status["api_server"] = {
        "enabled": config.API_ENABLED,
        "host": config.API_HOST,
        "port": config.API_PORT
    }
    
    # 添加服务器监控状态
    from monitor import get_server_status
    status["server_status"] = get_server_status()
    
    return status

@app.get("/api/players", tags=["玩家"], dependencies=[Depends(verify_api_key)])
def get_players(qq_id: Optional[str] = None, steam_id: Optional[str] = None):
    """获取玩家列表或特定玩家信息"""
    db = next(get_db())
    try:
        query = db.query(QQBotPlayers)
        
        if qq_id:
            query = query.filter(QQBotPlayers.qq_id == qq_id)
        if steam_id:
            query = query.filter(QQBotPlayers.steam_id == steam_id)
        
        players = query.all()
        
        result = []
        for player in players:
            result.append({
                "id": player.id,
                "qq_id": player.qq_id,
                "steam_id": player.steam_id,
                "nickname": player.nickname,
                "points": player.points,
                "bind_time": str(player.bind_time),
                "last_login": str(player.last_login),
                "last_checkin_date": player.last_checkin_date,
                "created_at": player.created_at
            })
        
        return {"count": len(result), "players": result}
    except Exception as e:
        logger.error(f"获取玩家列表失败: {str(e)}")
        raise HTTPException(status_code=500, detail="获取玩家列表失败")
    finally:
        db.close()

@app.post("/api/players", tags=["玩家"], dependencies=[Depends(verify_api_key)])
def create_player(player: PlayerInfo):
    """创建或更新玩家信息"""
    db = next(get_db())
    try:
        # 检查玩家是否已存在
        existing_player = db.query(QQBotPlayers).filter(
            QQBotPlayers.qq_id == player.qq_id
        ).first()
        
        if existing_player:
            # 更新玩家信息
            existing_player.steam_id = player.steam_id
            if player.nickname:
                existing_player.nickname = player.nickname
            existing_player.points = player.points
            existing_player.last_login = player.last_login
            db.commit()
            return {"status": "success", "message": "玩家信息已更新", "player_id": existing_player.id}
        else:
            # 创建新玩家
            new_player = QQBotPlayers(
                qq_id=player.qq_id,
                steam_id=player.steam_id,
                nickname=player.nickname or f"玩家{player.qq_id[:4]}",
                points=player.points
            )
            db.add(new_player)
            db.flush()
            
            # 创建相关记录
            from models import PlayerStats, DailySignIn
            player_stats = PlayerStats(player_id=new_player.id)
            daily_signin = DailySignIn(player_id=new_player.id)
            db.add_all([player_stats, daily_signin])
            db.commit()
            
            return {"status": "success", "message": "玩家创建成功", "player_id": new_player.id}
    except Exception as e:
        db.rollback()
        logger.error(f"创建玩家失败: {str(e)}")
        raise HTTPException(status_code=500, detail="创建玩家失败")
    finally:
        db.close()

@app.get("/api/server", tags=["服务器"], dependencies=[Depends(verify_api_key)])
def get_server_status_api():
    """获取服务器状态"""
    from monitor import get_server_status
    status = get_server_status()
    return status

@app.post("/api/broadcast", tags=["广播"], dependencies=[Depends(verify_api_key)])
async def send_broadcast(broadcast: BroadcastMessage):
    """发送广播消息"""
    # 确定目标群组
    target_groups = broadcast.target_groups or config.MONITOR_GROUPS
    
    if not target_groups:
        raise HTTPException(status_code=400, detail="没有指定目标群组")
    
    success_count = 0
    fail_count = 0
    
    for group_id in target_groups:
        if await send_onebot_message(
            "group",
            group_id=group_id,
            message=f"📢 系统广播\n{broadcast.content}\n\n-- API发送"
        ):
            success_count += 1
        else:
            fail_count += 1
    
    return {
        "status": "success",
        "message": "广播发送完成",
        "success_count": success_count,
        "fail_count": fail_count
    }

@app.get("/api/announcements", tags=["公告"], dependencies=[Depends(verify_api_key)])
def get_announcements(active_only: bool = True):
    """获取公告列表"""
    db = next(get_db())
    try:
        query = db.query(Announcements)
        
        if active_only:
            query = query.filter(Announcements.is_active == True)
        
        announcements = query.order_by(Announcements.created_at.desc()).all()
        
        result = []
        for announcement in announcements:
            result.append({
                "id": announcement.id,
                "title": announcement.title,
                "content": announcement.content,
                "created_at": str(announcement.created_at),
                "created_by": announcement.created_by,
                "is_active": announcement.is_active
            })
        
        return {"count": len(result), "announcements": result}
    except Exception as e:
        logger.error(f"获取公告列表失败: {str(e)}")
        raise HTTPException(status_code=500, detail="获取公告列表失败")
    finally:
        db.close()

@app.post("/api/announcements", tags=["公告"], dependencies=[Depends(verify_api_key)])
def create_announcement(announcement: AnnouncementCreate):
    """创建公告"""
    db = next(get_db())
    try:
        new_announcement = Announcements(
            title=announcement.title,
            content=announcement.content,
            created_by=announcement.created_by
        )
        db.add(new_announcement)
        db.commit()
        
        return {"status": "success", "message": "公告创建成功", "announcement_id": new_announcement.id}
    except Exception as e:
        db.rollback()
        logger.error(f"创建公告失败: {str(e)}")
        raise HTTPException(status_code=500, detail="创建公告失败")
    finally:
        db.close()

# API服务器管理
class APIServer:
    _instance = None
    _initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(APIServer, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not self._initialized:
            self.is_running = False
            self.server_thread = None
            self._initialized = True
    
    def start(self):
        if not self.is_running and config.API_ENABLED:
            self.is_running = True
            
            # 在单独的线程中启动UVicorn服务器
            self.server_thread = threading.Thread(
                target=self._run_server,
                daemon=True
            )
            self.server_thread.start()
            
            logger.info(f"API服务已启动，访问地址：http://{config.API_HOST}:{config.API_PORT}")
    
    def stop(self):
        if self.is_running:
            self.is_running = False
            # UVicorn服务器会自动停止，因为我们使用了daemon线程
            logger.info("API服务已停止")
    
    def _run_server(self):
        try:
            uvicorn.run(
                app, 
                host=config.API_HOST,
                port=config.API_PORT,
                log_level="info"
            )
        except Exception as e:
            logger.error(f"API服务器运行出错: {str(e)}")
            self.is_running = False

# 创建全局API服务器实例
api_server = APIServer()

# 注册驱动事件
def register_api_events(driver):
    @driver.on_startup
    async def on_startup():
        # 启动API服务
        api_server.start()
        
    @driver.on_shutdown
    async def on_shutdown():
        # 停止API服务
        api_server.stop()

# 如果直接运行此文件，则启动API服务
if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)