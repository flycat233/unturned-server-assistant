from pydantic import BaseSettings, Field
from typing import List, Optional
import os
from dotenv import load_dotenv

# 加载环境变量
base_dir = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(base_dir, '.env'))

class Settings(BaseSettings):
    # 基础配置
    VERSION: str = "1.0.0"
    DEBUG: bool = False
    
    # NoneBot基础配置
    SUPERUSERS: List[str] = Field(default_factory=lambda: ["1000000000"])
    NICKNAME: List[str] = Field(default_factory=lambda: ["Unturned助手", "unturnedbot"])
    COMMAND_START: List[str] = Field(default_factory=lambda: ["/"])
    COMMAND_SEP: List[str] = Field(default_factory=lambda: [" "])
    
    # API服务配置
    API_ENABLED: bool = True
    API_HOST: str = "127.0.0.1"
    API_PORT: int = 8000
    API_KEY: str = "your-api-key-here"
    
    # 数据库配置
    DATABASE_URL: str = "mysql+pymysql://root:password@localhost:3306/unturned_bot"
    DB_POOL_SIZE: int = 20
    
    # OneBot适配器配置
    ONE_BOT_URL: str = "http://127.0.0.1:5700"
    ONE_BOT_ACCESS_TOKEN: Optional[str] = None
    
    # 服务器监控配置
    MONITOR_ENABLED: bool = True
    MONITOR_INTERVAL: int = 60
    
    # Unturned服务器连接配置
    SERVER_IP: str = "127.0.0.1"
    SERVER_PORT: int = 27015
    SERVER_QUERY_PORT: int = 27016
    SERVER_TIMEOUT: int = 5
    
    # 通知配置
    MONITOR_GROUPS: List[str] = Field(default_factory=lambda: ["123456789"])
    NOTIFY_ON_STARTUP: bool = True
    NOTIFY_ON_SHUTDOWN: bool = True
    NOTIFY_STATUS_CHANGE: bool = True
    
    # 命令配置
    ENABLE_HELP_COMMAND: bool = True
    ENABLE_BIND_COMMAND: bool = True
    ENABLE_SIGN_COMMAND: bool = True
    ENABLE_ME_COMMAND: bool = True
    ENABLE_SERVER_COMMAND: bool = True
    ENABLE_BROADCAST_COMMAND: bool = True
    
    # 签到奖励配置
    SIGN_IN_REWARD_BASE: int = 100
    SIGN_IN_REWARD_7DAYS: int = 1000
    SIGN_IN_REWARD_30DAYS: int = 5000
    
    # 日志配置
    LOG_LEVEL: str = "INFO"
    LOG_TO_FILE: bool = True
    LOG_FILE: str = "unturned_bot.log"
    
    # 其他配置
    MAX_RETRY_TIMES: int = 3
    RETRY_INTERVAL: int = 5
    DEFAULT_MAX_PLAYERS: int = 24
    DEFAULT_MAP_NAME: str = "Unknown"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

# 创建全局设置实例
settings = Settings()

# 导出常用配置以便其他模块使用
def get_config():
    return settings