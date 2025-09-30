import asyncio
import time
from nonebot import get_driver
from settings import get_config
from utils import logger, send_onebot_message
from database import get_db
from models import ServerStatus
import datetime

# 获取配置
config = get_config()

# 监控状态
class ServerMonitor:
    _instance = None
    _initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ServerMonitor, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not self._initialized:
            self.is_running = False
            self.last_status = None
            self.monitor_task = None
            self._initialized = True
    
    async def start(self):
        if not self.is_running and config.MONITOR_ENABLED:
            self.is_running = True
            self.monitor_task = asyncio.create_task(self._monitor_loop())
            logger.info("服务器监控已启动")
    
    async def stop(self):
        if self.is_running:
            self.is_running = False
            if self.monitor_task:
                self.monitor_task.cancel()
                try:
                    await self.monitor_task
                except asyncio.CancelledError:
                    pass
                self.monitor_task = None
            logger.info("服务器监控已停止")
    
    async def _monitor_loop(self):
        while self.is_running:
            try:
                await self._check_server_status()
            except Exception as e:
                logger.error(f"服务器监控出错: {str(e)}")
            
            # 等待下一次检查
            await asyncio.sleep(config.MONITOR_INTERVAL)
    
    async def _check_server_status(self):
        # 获取服务器状态
        status = await self._query_server_status()
        
        # 保存状态到数据库
        self._save_status_to_db(status)
        
        # 检查状态变化并发送通知
        if self.last_status is not None and config.NOTIFY_STATUS_CHANGE:
            if self.last_status["is_online"] != status["is_online"]:
                await self._send_status_change_notification(status)
        
        # 更新上次状态
        self.last_status = status.copy()
    
    async def _query_server_status(self):
        # 默认状态（离线）
        status = {
            "is_online": False,
            "players": 0,
            "max_players": config.DEFAULT_MAX_PLAYERS,
            "map": config.DEFAULT_MAP_NAME,
            "players_list": [],
            "message": "服务器查询失败"
        }
        
        try:
            # 这里应该是实际的服务器查询逻辑
            # 由于没有具体的Unturned服务器查询库，这里使用模拟数据
            # 在实际使用中，应该使用类似python-valve或其他游戏服务器查询库
            
            # 模拟服务器在线（80%概率）
            import random
            if random.random() < 0.8:
                status["is_online"] = True
                status["players"] = random.randint(0, status["max_players"])
                status["message"] = "服务器运行正常"
                
                # 生成模拟玩家列表
                if status["players"] > 0:
                    status["players_list"] = [f"Player{i}" for i in range(1, status["players"] + 1)]
            
            logger.debug(f"查询服务器状态: {status}")
        except Exception as e:
            logger.error(f"服务器查询出错: {str(e)}")
        
        return status
    
    def _save_status_to_db(self, status):
        try:
            db = next(get_db())
            status_record = ServerStatus(
                is_online=status["is_online"],
                players=status["players"],
                max_players=status["max_players"],
                map=status["map"],
                message=status["message"]
            )
            db.add(status_record)
            db.commit()
        except Exception as e:
            logger.error(f"保存服务器状态到数据库失败: {str(e)}")
        finally:
            db.close()
    
    async def _send_status_change_notification(self, status):
        # 构建通知消息
        if status["is_online"]:
            message = [
                "🟢 服务器已上线！",
                f"服务器地址: {config.SERVER_IP}:{config.SERVER_PORT}",
                f"当前状态: 运行正常",
                f"可容纳玩家: {status['max_players']}人"
            ]
        else:
            message = [
                "🔴 服务器已离线！",
                f"服务器地址: {config.SERVER_IP}:{config.SERVER_PORT}",
                f"离线原因: {status['message']}"
            ]
        
        # 发送通知到所有监控群
        for group_id in config.MONITOR_GROUPS:
            await send_onebot_message(
                "group",
                group_id=group_id,
                message="\n".join(message)
            )

# 创建全局监控实例
server_monitor = ServerMonitor()

# 注册驱动事件
driver = get_driver()

@driver.on_startup
async def on_startup():
    await server_monitor.start()

@driver.on_shutdown
async def on_shutdown():
    await server_monitor.stop()

# 获取服务器状态
def get_server_status():
    if server_monitor.last_status:
        return server_monitor.last_status
    else:
        # 返回默认状态
        return {
            "is_online": False,
            "players": 0,
            "max_players": config.DEFAULT_MAX_PLAYERS,
            "map": config.DEFAULT_MAP_NAME,
            "players_list": [],
            "message": "服务器状态未知"
        }

# 手动触发服务器检查
async def trigger_server_check():
    if server_monitor.is_running:
        await server_monitor._check_server_status()
        return True
    return False