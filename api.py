from fastapi import FastAPI, Depends, HTTPException, Security
from fastapi.security import APIKeyHeader
from typing import List, Dict, Any
from .settings import get_config
from .database import get_db
from .models import QQBotPlayers, ServerStatus, Announcements
from .onebot_http import bot_http

# 获取配置
config = get_config()

# 创建FastAPI实例
app = FastAPI(title="Unturned Server Bot API", version="0.1.0")

# API密钥认证
API_KEY = APIKeyHeader(name="X-API-Key", auto_error=False)

async def get_api_key(api_key: str = Security(API_KEY)):
    if not api_key:
        raise HTTPException(status_code=401, detail="API密钥缺失")
    if api_key != config.api_key:
        raise HTTPException(status_code=403, detail="无效的API密钥")
    return api_key

# 根路由
@app.get("/")
def read_root():
    return {"status": "ok", "message": "Unturned Server Bot API is running"}

# 获取机器人信息
@app.get("/info")
def get_bot_info():
    return {
        "name": config.nickname[0] if config.nickname else "Unturned助手",
        "version": "0.1.0",
        "superusers": list(config.superusers),
        "debug": config.debug
    }

# 获取服务器状态
@app.get("/server/status")
def get_server_status():
    from .monitor import get_current_status
    return get_current_status()

# 发送私聊消息 (需要API密钥)
@app.post("/message/private", dependencies=[Depends(get_api_key)])
async def send_private_message(user_id: int, message: str):
    result = await bot_http.send_private_msg(user_id, message)
    if result:
        return {"status": "ok", "message_id": result.get("message_id")}
    else:
        raise HTTPException(status_code=500, detail="发送消息失败")

# 发送群消息 (需要API密钥)
@app.post("/message/group", dependencies=[Depends(get_api_key)])
async def send_group_message(group_id: int, message: str):
    result = await bot_http.send_group_msg(group_id, message)
    if result:
        return {"status": "ok", "message_id": result.get("message_id")}
    else:
        raise HTTPException(status_code=500, detail="发送消息失败")

# 获取所有玩家信息
@app.get("/players")
def get_players():
    db = next(get_db())
    try:
        players = db.query(QQBotPlayers).all()
        return [{"qq_id": p.qq_id, "steam_id": p.steam_id, "nickname": p.nickname} for p in players]
    finally:
        db.close()

# 启动时初始化API数据
def init_api_data():
    # 确保数据库表已创建
    from .database import init_db
    init_db()

# 导入时初始化
init_api_data()