import os
import logging
from typing import Set, List, Dict, Any, Optional
from pathlib import Path
from pydantic import BaseSettings, Field, SecretStr
import datetime

# 确保正确的工作目录
current_dir = Path(__file__).parent.resolve()

# 全局配置类
class GlobalConfig(BaseSettings):
    # 基础配置
    VERSION: str = Field(default="1.0.0", alias="VERSION")
    
    # 超级用户配置 - 使用List类型更灵活，避免Set类型转换问题
    superusers: List[str] = Field(default_factory=lambda: ["123456789"], alias="SUPERUSERS")
    
    # 机器人基本配置
    nickname: list = Field(default_factory=lambda: ["Unturned助手"], alias="NICKNAME")
    command_start: list = Field(default_factory=lambda: ["/"], alias="COMMAND_START")
    command_sep: list = Field(default_factory=lambda: [" "], alias="COMMAND_SEP")
    debug: bool = Field(default=False, alias="DEBUG")
    
    # API服务配置
    api_enabled: bool = Field(default=True, alias="API_ENABLED")
    api_host: str = Field(default="127.0.0.1", alias="API_HOST")
    api_port: int = Field(default=8000, alias="API_PORT")
    api_debug: bool = Field(default=False, alias="API_DEBUG")
    api_key: SecretStr = Field(default="your-api-key-here", alias="API_KEY")
    
    # 数据库配置 - 默认使用MySQL
    database_url: str = Field(default="mysql+pymysql://root:password@localhost:3306/unturned_bot", alias="DATABASE_URL")
    db_pool_size: int = Field(default=20, alias="DB_POOL_SIZE")
    
    # OneBot适配器配置
    one_bot_url: str = Field(default="http://127.0.0.1:5700", alias="ONE_BOT_URL")
    one_bot_access_token: Optional[SecretStr] = Field(default=None, alias="ONE_BOT_ACCESS_TOKEN")
    
    # 服务器监控配置
    monitor_enabled: bool = Field(default=True, alias="MONITOR_ENABLED")
    monitor_interval: int = Field(default=60, alias="MONITOR_INTERVAL")
    server_ip: str = Field(default="127.0.0.1", alias="SERVER_IP")
    server_port: int = Field(default=27015, alias="SERVER_PORT")
    server_query_port: int = Field(default=27016, alias="SERVER_QUERY_PORT")
    server_timeout: int = Field(default=5, alias="SERVER_TIMEOUT")  # 连接超时时间
    
    # 通知配置
    monitor_groups: List[str] = Field(default_factory=lambda: ["123456789"], alias="MONITOR_GROUPS")
    notify_on_startup: bool = Field(default=True, alias="NOTIFY_ON_STARTUP")
    notify_on_shutdown: bool = Field(default=True, alias="NOTIFY_ON_SHUTDOWN")
    notify_status_change: bool = Field(default=True, alias="NOTIFY_STATUS_CHANGE")
    
    # 命令配置
    enable_help_command: bool = Field(default=True, alias="ENABLE_HELP_COMMAND")
    enable_bind_command: bool = Field(default=True, alias="ENABLE_BIND_COMMAND")
    enable_sign_command: bool = Field(default=True, alias="ENABLE_SIGN_COMMAND")
    enable_me_command: bool = Field(default=True, alias="ENABLE_ME_COMMAND")
    enable_server_command: bool = Field(default=True, alias="ENABLE_SERVER_COMMAND")
    enable_broadcast_command: bool = Field(default=True, alias="ENABLE_BROADCAST_COMMAND")
    
    # 签到奖励配置
    sign_in_reward_base: int = Field(default=100, alias="SIGN_IN_REWARD_BASE")
    sign_in_reward_7days: int = Field(default=1000, alias="SIGN_IN_REWARD_7DAYS")
    sign_in_reward_30days: int = Field(default=5000, alias="SIGN_IN_REWARD_30DAYS")
    
    # 日志配置
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    log_file: str = Field(default="unturned_bot.log", alias="LOG_FILE")
    log_to_file: bool = Field(default=True, alias="LOG_TO_FILE")
    
    # 其他配置
    max_retry_times: int = Field(default=3, alias="MAX_RETRY_TIMES")
    retry_interval: int = Field(default=5, alias="RETRY_INTERVAL")
    default_max_players: int = Field(default=24, alias="DEFAULT_MAX_PLAYERS")
    default_map_name: str = Field(default="Unknown", alias="DEFAULT_MAP_NAME")
    
    class Config:
        env_file = str(current_dir / ".env")
        env_file_encoding = "utf-8"
        case_sensitive = False
        
        # 自定义字段验证和转换
        @classmethod
        def parse_env_var(cls, field_name, raw_val):
            import json
            # 特别处理SUPERUSERS字段，确保它始终是字符串并正确转换为集合
            if field_name == "superusers":
                # 确保值是字符串格式
                raw_str = str(raw_val)
                # 去除可能存在的引号
                if raw_str.startswith('"') and raw_str.endswith('"'):
                    raw_str = raw_str[1:-1]
                elif raw_str.startswith("'") and raw_str.endswith("'"):
                    raw_str = raw_str[1:-1]
                # 分割并转换为字符串列表
                return [user_id.strip() for user_id in raw_str.split(',') if user_id.strip()]
            
            # 处理列表类型的字段，尝试JSON解析
            elif field_name in ["nickname", "command_start", "command_sep", "monitor_groups"]:
                try:
                    # 如果已经是列表，直接返回
                    if isinstance(raw_val, list):
                        return raw_val
                    # 尝试JSON解析
                    if isinstance(raw_val, str):
                        return json.loads(raw_val)
                except (json.JSONDecodeError, TypeError):
                    # 解析失败时返回默认值
                    if field_name == "nickname":
                        return ["Unturned助手"]
                    elif field_name == "command_start":
                        return ["/"]
                    elif field_name == "command_sep":
                        return [" "]
                    elif field_name == "monitor_groups":
                        return ["123456789"]
            
            return raw_val
    
    # 当前时间（只读属性）
    @property
    def current_time(self):
        return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # 获取API密钥的明文（用于验证）
    @property
    def api_key_plain(self) -> str:
        return self.api_key.get_secret_value() if self.api_key else ""
    
    # 获取OneBot访问令牌的明文
    @property
    def one_bot_token_plain(self) -> Optional[str]:
        return self.one_bot_access_token.get_secret_value() if self.one_bot_access_token else None

# 加载环境变量并特别处理SUPERUSERS配置
def load_and_fix_env():
    """加载环境变量并确保SUPERUSERS被正确处理"""
    try:
        from dotenv import load_dotenv
        dotenv_path = current_dir / ".env"
        
        # 确保.env文件存在
        if not os.path.exists(dotenv_path):
            create_default_env_file(dotenv_path)
        
        load_dotenv(dotenv_path=dotenv_path)
        
        # 核心修复：确保SUPERUSERS始终被当作字符串处理，避免自动转换为整数
        superusers = os.getenv("SUPERUSERS")
        if superusers:
            # 确保值是字符串格式，添加额外的引号以防止被自动转换
            os.environ["SUPERUSERS"] = f'"{superusers}"' if not (superusers.startswith('"') and superusers.endswith('"')) else superusers
    except ImportError:
        logging.warning("未找到python-dotenv模块，跳过.env文件加载")
    except Exception as e:
        logging.error(f"加载.env文件失败: {e}")

# 创建默认的.env文件
def create_default_env_file(env_path):
    """创建默认的.env文件"""
    try:
        # 确保目录存在
        os.makedirs(os.path.dirname(env_path), exist_ok=True)
        
        default_env = """
# Unturned服务器助手机器人配置文件

# 基础配置
VERSION=1.0.0
DEBUG=False

# NoneBot基础配置
SUPERUSERS=["123456789"]  # 超级用户QQ号列表
NICKNAME=["Unturned助手", "unturnedbot"]  # 机器人昵称
COMMAND_START=["/"]  # 命令前缀
COMMAND_SEP=[" "]  # 命令分隔符

# API服务配置
API_ENABLED=True
API_HOST=127.0.0.1
API_PORT=8000
API_KEY=your-api-key-here

# 数据库配置
DATABASE_URL=mysql+pymysql://root:password@localhost:3306/unturned_bot
DB_POOL_SIZE=20

# OneBot适配器配置
ONE_BOT_URL=http://127.0.0.1:5700
# ONE_BOT_ACCESS_TOKEN=your-access-token-here

# 服务器监控配置
MONITOR_ENABLED=True
MONITOR_INTERVAL=60
SERVER_IP=127.0.0.1
SERVER_PORT=27015
SERVER_QUERY_PORT=27016
SERVER_TIMEOUT=5

# 通知配置
MONITOR_GROUPS=["123456789"]  # 监控群号列表
NOTIFY_ON_STARTUP=True
NOTIFY_ON_SHUTDOWN=True
NOTIFY_STATUS_CHANGE=True

# 命令配置
ENABLE_HELP_COMMAND=True
ENABLE_BIND_COMMAND=True
ENABLE_SIGN_COMMAND=True
ENABLE_ME_COMMAND=True
ENABLE_SERVER_COMMAND=True
ENABLE_BROADCAST_COMMAND=True

# 签到奖励配置
SIGN_IN_REWARD_BASE=100
SIGN_IN_REWARD_7DAYS=1000
SIGN_IN_REWARD_30DAYS=5000

# 日志配置
LOG_LEVEL=INFO
LOG_TO_FILE=True
LOG_FILE=unturned_bot.log

# 其他配置
MAX_RETRY_TIMES=3
RETRY_INTERVAL=5
DEFAULT_MAX_PLAYERS=24
DEFAULT_MAP_NAME=Unknown
        """
        
        with open(env_path, "w", encoding="utf-8") as f:
            f.write(default_env.strip())
        
        logging.info(f"已创建默认.env配置文件: {env_path}")
    except Exception as e:
        logging.warning(f"无法创建.env文件: {str(e)}")

# 初始化配置
def init_config():
    """初始化配置，先加载环境变量，然后创建配置实例"""
    # 加载并修复环境变量
    load_and_fix_env()
    
    # 创建配置实例
    config = GlobalConfig()
    
    # 设置日志
    setup_logger(config)
    
    return config

# 设置日志配置
def setup_logger(config: GlobalConfig):
    """根据配置设置日志"""
    # 设置日志级别
    log_level = getattr(logging, config.log_level.upper(), logging.INFO)
    
    # 创建日志器
    logger = logging.getLogger()
    logger.setLevel(log_level)
    
    # 清除已有的处理器
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    # 添加控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    
    # 定义日志格式
    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    formatter = logging.Formatter(log_format)
    console_handler.setFormatter(formatter)
    
    # 添加到日志器
    logger.addHandler(console_handler)
    
    # 如果需要记录到文件
    if config.log_to_file:
        try:
            # 确保日志目录存在
            log_dir = os.path.dirname(config.log_file)
            if log_dir:
                os.makedirs(log_dir, exist_ok=True)
            
            # 创建文件处理器
            file_handler = logging.FileHandler(config.log_file, encoding="utf-8")
            file_handler.setLevel(log_level)
            file_handler.setFormatter(formatter)
            
            # 添加到日志器
            logger.addHandler(file_handler)
        except Exception as e:
            logging.warning(f"无法创建日志文件处理器: {str(e)}")

# 检查依赖
def check_dependencies():
    """检查必要的依赖包是否已安装"""
    required_packages = ["nonebot2", "nonebot-adapter-onebot", "sqlalchemy", "fastapi", "uvicorn", "python-dotenv", "pymysql"]
    missing_packages = []
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing_packages.append(package)
    return missing_packages

# 全局配置实例
config = None

# 初始化配置实例
def get_config():
    """获取全局配置实例，如果不存在则初始化"""
    global config
    if config is None:
        config = init_config()
    return config

# 安全地获取配置项
def get_setting(key: str, default: Any = None) -> Any:
    """安全地获取配置项"""
    cfg = get_config()
    return getattr(cfg, key, default)

# 重新加载配置
def reload_config():
    """重新加载配置"""
    global config
    config = init_config()
    return config

# 默认导出配置实例和常用函数
__all__ = ["config", "GlobalConfig", "get_config", "get_setting", "reload_config", "check_dependencies"]