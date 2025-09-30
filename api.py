from fastapi import FastAPI, Depends, HTTPException
from typing import List, Dict, Any
from .settings import get_config
from database import get_db

# 获取配置
config = get_config()

# 创建FastAPI实例
app = FastAPI(title="Unturned Server Bot API", version="0.1.0")

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

# 示例API路由 - 获取服务器状态
@app.get("/server/status")
def get_server_status():
    # 这里可以添加获取服务器状态的逻辑
    return {
        "status": "running",
        "players": 0,
        "max_players": 24,
        "map": "Unknown"
    }

# 启动时初始化API数据
def init_api_data():
    # 可以在这里添加初始化API数据的代码
    pass

# 导入时初始化
init_api_data()