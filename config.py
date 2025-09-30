import os
from typing import Set
from pydantic import BaseSettings, Field

class Config(BaseSettings):
    # 超级用户配置
    # 使用特殊处理确保SUPERUSERS被正确解析为Set类型
    superusers: Set[str] = Field(default_factory=set, alias="SUPERUSERS")
    
    # 机器人基本配置
    nickname: list = Field(default_factory=list, alias="NICKNAME")
    command_start: list = Field(default_factory=lambda: ["/", "!", "！"], alias="COMMAND_START")
    command_sep: list = Field(default_factory=lambda: ["|"], alias="COMMAND_SEP")
    debug: bool = Field(default=False, alias="DEBUG")
    
    # API服务配置
    api_enabled: bool = Field(default=True, alias="API_ENABLED")
    api_host: str = Field(default="127.0.0.1", alias="API_HOST")
    api_port: int = Field(default=8080, alias="API_PORT")
    api_debug: bool = Field(default=False, alias="API_DEBUG")
    
    # 数据库配置
    database_url: str = Field(default="sqlite:///./unturned_bot.db", alias="DATABASE_URL")
    
    # 监控配置
    monitor_interval: int = Field(default=60, alias="MONITOR_INTERVAL")
    notify_on_startup: bool = Field(default=True, alias="NOTIFY_ON_STARTUP")
    notify_on_shutdown: bool = Field(default=True, alias="NOTIFY_ON_SHUTDOWN")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        
        # 自定义字段验证和转换
        @classmethod
        def parse_env_var(cls, field_name, raw_val):
            # 特别处理SUPERUSERS字段，确保它始终是字符串并正确转换为集合
            if field_name == "superusers":
                # 确保值是字符串格式
                raw_str = str(raw_val)
                # 去除可能存在的引号
                if raw_str.startswith('"') and raw_str.endswith('"'):
                    raw_str = raw_str[1:-1]
                elif raw_str.startswith("'") and raw_str.endswith("'"):
                    raw_str = raw_str[1:-1]
                # 分割并转换为字符串集合
                return set(user_id.strip() for user_id in raw_str.split(',') if user_id.strip())
            return raw_val

# 创建全局配置实例
config = Config()