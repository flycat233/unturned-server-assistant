"""
Unturned服务器助手机器人核心模块
包含全局配置、数据库连接和基础工具函数
"""
import os
import logging
from pathlib import Path
from typing import Optional, Dict, Any
import nonebot
from pydantic import BaseModel, Field
import sqlite3
import asyncio
import aiohttp
import hmac
import hashlib

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("UnturnedBot")

# 获取环境变量配置
class Config(BaseModel):
    superusers: list = Field(default_factory=list, alias="SUPERUSERS")
    api_key: str = Field(default="", alias="API_KEY")
    database_url: str = Field(default="sqlite:///data/unturned_bot.db", alias="DATABASE_URL")
    server_ip: str = Field(default="127.0.0.1", alias="SERVER_IP")
    server_port: int = Field(default=27015, alias="SERVER_PORT")
    monitor_interval: int = Field(default=60, alias="MONITOR_INTERVAL")
    onebot_secret: str = Field(default="", alias="ONEBOT_SECRET")
    daily_sign_in_reward: int = Field(default=1000, alias="DAILY_SIGN_IN_REWARD")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        allow_population_by_field_name = True

# 全局配置实例
config = Config()

# 数据目录路径
data_dir = Path("f:\\UnturnedServer\\NoneBot2Plugin\\data")

def init_data_dir():
    """初始化数据目录"""
    if not data_dir.exists():
        data_dir.mkdir(parents=True)

# 数据库连接管理
class DatabaseManager:
    _instance = None
    _conn = None
    _lock = asyncio.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(DatabaseManager, cls).__new__(cls)
        return cls._instance
    
    def connect(self):
        """建立数据库连接"""
        if self._conn is None or self._conn.close:
            # 确保数据目录存在
            init_data_dir()
            # 解析数据库URL（简单处理sqlite情况）
            if config.database_url.startswith("sqlite:///"):
                db_path = config.database_url[9:]
                self._conn = sqlite3.connect(db_path)
            else:
                raise ValueError(f"不支持的数据库URL格式: {config.database_url}")
        return self._conn
    
    def close(self):
        """关闭数据库连接"""
        if self._conn is not None:
            self._conn.close()
            self._conn = None

# 全局数据库管理器实例
db_manager = DatabaseManager()

# 基础工具函数
def is_superuser(user_id: str) -> bool:
    """检查用户是否为超级用户"""
    return str(user_id) in config.superusers

async def check_server_status(ip: str, port: int) -> Dict[str, Any]:
    """检查Unturned服务器状态
    注意：这是一个模拟实现，实际应该使用Unturned服务器提供的查询接口
    """
    try:
        # 这里应该实现与Unturned服务器的实际通信
        # 为了演示，我们返回一个模拟的状态
        return {
            "online": True,
            "players": 10,
            "max_players": 50,
            "name": "Unturned服务器",
            "map": "PEI",
            "version": "3.23.15.0"
        }
    except Exception as e:
        logger.error(f"检查服务器状态失败: {e}")
        return {"online": False, "error": str(e)}

def verify_onebot_signature(data: bytes, signature: str) -> bool:
    """验证OneBot事件上报的签名"""
    if not config.onebot_secret:
        # 如果没有配置密钥，则跳过验证
        return True
    
    # 检查签名格式
    if not signature.startswith("sha1="):
        return False
    
    # 计算HMAC SHA1签名
    hmac_obj = hmac.new(config.onebot_secret.encode(), data, hashlib.sha1)
    expected_signature = f"sha1={hmac_obj.hexdigest()}"
    
    return signature == expected_signature

async def send_request(url: str, method: str = "GET", **kwargs) -> Optional[Dict[str, Any]]:
    """发送HTTP请求的封装函数"""
    try:
        async with aiohttp.ClientSession() as session:
            request_method = getattr(session, method.lower())
            async with request_method(url, **kwargs) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    logger.error(f"请求失败: {response.status}, URL: {url}")
                    return None
    except Exception as e:
        logger.error(f"请求异常: {e}, URL: {url}")
        return None

# 初始化函数
def init_bot():
    """初始化机器人"""
    init_data_dir()
    logger.info("Unturned服务器助手机器人初始化完成")

# 当模块被加载时执行初始化
init_bot()