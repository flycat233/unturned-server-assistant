import os
import logging
from typing import Set, List, Dict, Any, Optional
from pathlib import Path
from pydantic import BaseSettings, Field

# 确保正确的工作目录
current_dir = Path(__file__).parent.resolve()

# 全局配置类
class GlobalConfig(BaseSettings):
    # 超级用户配置 - 使用List类型更灵活，避免Set类型转换问题
    superusers: List[str] = Field(default_factory=list, alias="SUPERUSERS")
    
    # 机器人基本配置
    nickname: list = Field(default_factory=lambda: ["Unturned助手"], alias="NICKNAME")
    command_start: list = Field(default_factory=lambda: ["/", "!", "！"], alias="COMMAND_START")
    command_sep: list = Field(default_factory=lambda: ["|"], alias="COMMAND_SEP")
    debug: bool = Field(default=False, alias="DEBUG")
    
    # API服务配置
    api_enabled: bool = Field(default=True, alias="API_ENABLED")
    api_host: str = Field(default="127.0.0.1", alias="API_HOST")
    api_port: int = Field(default=8080, alias="API_PORT")
    api_debug: bool = Field(default=False, alias="API_DEBUG")
    
    # 数据库配置 - 默认使用MySQL
    database_url: str = Field(default="mysql+pymysql://root:password@localhost:3306/unturned_bot", alias="DATABASE_URL")
    
    # 监控配置
    monitor_interval: int = Field(default=60, alias="MONITOR_INTERVAL")
    notify_on_startup: bool = Field(default=True, alias="NOTIFY_ON_STARTUP")
    notify_on_shutdown: bool = Field(default=True, alias="NOTIFY_ON_SHUTDOWN")
    
    # 日志配置
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    log_file: str = Field(default="unturned_bot.log", alias="LOG_FILE")
    
    # 服务器配置（扩展）
    server_ip: str = Field(default="127.0.0.1", alias="SERVER_IP")
    server_port: int = Field(default=27015, alias="SERVER_PORT")
    server_query_port: int = Field(default=27016, alias="SERVER_QUERY_PORT")
    
    # 其他配置
    max_retry_times: int = Field(default=3, alias="MAX_RETRY_TIMES")
    retry_interval: int = Field(default=5, alias="RETRY_INTERVAL")
    
    class Config:
        env_file = str(current_dir / ".env")
        env_file_encoding = "utf-8"
        
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
            elif field_name in ["nickname", "command_start", "command_sep"]:
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
                        return ["/", "!", "！"]
                    elif field_name == "command_sep":
                        return ["|"]
            
            return raw_val

# 加载环境变量并特别处理SUPERUSERS配置
def load_and_fix_env():
    """加载环境变量并确保SUPERUSERS被正确处理"""
    try:
        from dotenv import load_dotenv
        dotenv_path = current_dir / ".env"
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
    logging.basicConfig(
        level=getattr(logging, config.log_level.upper(), logging.INFO),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler(config.log_file),
            logging.StreamHandler()
        ]
    )

# 检查依赖
def check_dependencies():
    """检查必要的依赖包是否已安装"""
    required_packages = ["nonebot2", "nonebot-adapter-onebot", "sqlalchemy", "fastapi", "uvicorn", "python-dotenv"]
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