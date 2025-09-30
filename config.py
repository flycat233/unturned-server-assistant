"""
Unturned服务器助手机器人配置模块
包含插件的默认配置信息
"""
import os
from typing import Dict, Any, List, Optional, Tuple

# 从环境变量获取配置，没有则使用默认值
def get_env_var(name: str, default: Any = None, var_type: type = str) -> Any:
    """从环境变量获取配置并转换为指定类型"""
    value = os.getenv(name)
    if value is None:
        return default
    
    try:
        if var_type == bool:
            return value.lower() in ('true', '1', 'yes', 'y')
        elif var_type == int:
            return int(value)
        elif var_type == float:
            return float(value)
        elif var_type == list:
            return value.split(',') if value else []
        elif var_type == dict:
            import json
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return default
        return var_type(value)
    except (ValueError, TypeError):
        return default

# 基础配置
class Config:
    """插件核心配置类"""
    # 基础信息
    PLUGIN_NAME = "UnturnedServerAssistant"
    PLUGIN_VERSION = "1.0.0"
    PLUGIN_AUTHOR = "NoneBot2 Community"
    PLUGIN_DESCRIPTION = "Unturned服务器助手机器人，提供API接口、服务器监控、玩家管理等功能"
    
    # 超级用户配置（从环境变量获取）
    SUPERUSERS: List[str] = get_env_var("SUPERUSERS", [], list)
    
    # API配置
    API_ENABLED: bool = get_env_var("API_ENABLED", True, bool)
    API_HOST: str = get_env_var("API_HOST", "127.0.0.1", str)
    API_PORT: int = get_env_var("API_PORT", 8000, int)
    API_KEY: str = get_env_var("API_KEY", "", str)
    API_DEBUG: bool = get_env_var("API_DEBUG", False, bool)
    API_ALLOWED_IPS: List[str] = get_env_var("API_ALLOWED_IPS", [], list)
    
    # 数据库配置
    DATABASE_URL: str = get_env_var("DATABASE_URL", "sqlite:///./unturned_bot.db", str)
    DATABASE_POOL_SIZE: int = get_env_var("DATABASE_POOL_SIZE", 5, int)
    DATABASE_MAX_OVERFLOW: int = get_env_var("DATABASE_MAX_OVERFLOW", 10, int)
    DATABASE_ECHO: bool = get_env_var("DATABASE_ECHO", False, bool)
    
    # 服务器监控配置
    MONITOR_ENABLED: bool = get_env_var("MONITOR_ENABLED", True, bool)
    MONITOR_INTERVAL: int = get_env_var("MONITOR_INTERVAL", 60, int)  # 监控间隔（秒）
    SERVER_QUERY_TIMEOUT: int = get_env_var("SERVER_QUERY_TIMEOUT", 5, int)  # 服务器查询超时时间（秒）
    SERVER_NOTIFY_ON_STATUS_CHANGE: bool = get_env_var("SERVER_NOTIFY_ON_STATUS_CHANGE", True, bool)
    
    # Unturned服务器配置（可以配置多个服务器）
    UNTURNED_SERVERS: List[Dict[str, Any]] = get_env_var(
        "UNTURNED_SERVERS", 
        [
            {
                "name": "主服务器",
                "host": "127.0.0.1",
                "port": 27015,
                "query_port": 27015,
                "rcon_port": 27016,
                "rcon_password": "",
                "notify_groups": [],
                "auto_reboot": False,
                "max_players": 32
            }
        ], 
        dict
    )
    
    # 签到系统配置
    SIGNIN_ENABLED: bool = get_env_var("SIGNIN_ENABLED", True, bool)
    SIGNIN_REWARD_ECONOMY: int = get_env_var("SIGNIN_REWARD_ECONOMY", 100, int)  # 签到奖励经济点
    SIGNIN_REWARD_EXP: int = get_env_var("SIGNIN_REWARD_EXP", 50, int)  # 签到奖励经验
    SIGNIN_REWARD_MESSAGE: str = get_env_var("SIGNIN_REWARD_MESSAGE", "签到成功！获得{economy}经济点和{exp}经验值", str)
    SIGNIN_MAX_STREAK_REWARD_MULTIPLIER: float = get_env_var("SIGNIN_MAX_STREAK_REWARD_MULTIPLIER", 3.0, float)  # 最大连续签到奖励倍数
    
    # 命令配置
    COMMAND_PREFIX: str = get_env_var("COMMAND_PREFIX", "un.", str)
    COMMAND_COOLDOWN: int = get_env_var("COMMAND_COOLDOWN", 3, int)  # 命令冷却时间（秒）
    COMMAND_MAX_RETRY: int = get_env_var("COMMAND_MAX_RETRY", 3, int)
    
    # 消息配置
    MESSAGE_MAX_LENGTH: int = get_env_var("MESSAGE_MAX_LENGTH", 2000, int)
    MESSAGE_SEND_TIMEOUT: int = get_env_var("MESSAGE_SEND_TIMEOUT", 10, int)
    MESSAGE_FORMAT: str = get_env_var("MESSAGE_FORMAT", "[Unturned助手] {content}", str)
    
    # 缓存配置
    CACHE_ENABLED: bool = get_env_var("CACHE_ENABLED", True, bool)
    CACHE_DEFAULT_TTL: int = get_env_var("CACHE_DEFAULT_TTL", 3600, int)  # 默认缓存时间（秒）
    
    # 日志配置
    LOG_LEVEL: str = get_env_var("LOG_LEVEL", "INFO", str)
    LOG_FILE: str = get_env_var("LOG_FILE", "unturned_bot.log", str)
    LOG_FORMAT: str = get_env_var(
        "LOG_FORMAT", 
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s", 
        str
    )
    
    # 功能开关配置
    FEATURE_PLAYER_MANAGEMENT: bool = get_env_var("FEATURE_PLAYER_MANAGEMENT", True, bool)
    FEATURE_ECONOMY_SYSTEM: bool = get_env_var("FEATURE_ECONOMY_SYSTEM", True, bool)
    FEATURE_SERVER_MONITORING: bool = get_env_var("FEATURE_SERVER_MONITORING", True, bool)
    FEATURE_API_INTERFACE: bool = get_env_var("FEATURE_API_INTERFACE", True, bool)
    FEATURE_SIGNIN_SYSTEM: bool = get_env_var("FEATURE_SIGNIN_SYSTEM", True, bool)
    FEATURE_BROADCAST: bool = get_env_var("FEATURE_BROADCAST", True, bool)
    
    # OneBot配置
    ONEBOT_API_URL: str = get_env_var("ONEBOT_API_URL", "", str)
    ONEBOT_ACCESS_TOKEN: str = get_env_var("ONEBOT_ACCESS_TOKEN", "", str)
    ONEBOT_SECRET: str = get_env_var("ONEBOT_SECRET", "", str)
    
    # 群管理配置
    GROUP_DEFAULT_ADMIN_PERMISSION: int = get_env_var("GROUP_DEFAULT_ADMIN_PERMISSION", 1, int)
    GROUP_DEFAULT_MEMBER_PERMISSION: int = get_env_var("GROUP_DEFAULT_MEMBER_PERMISSION", 0, int)
    
    # 数据同步配置
    DATA_SYNC_ENABLED: bool = get_env_var("DATA_SYNC_ENABLED", False, bool)
    DATA_SYNC_INTERVAL: int = get_env_var("DATA_SYNC_INTERVAL", 300, int)  # 数据同步间隔（秒）
    DATA_BACKUP_ENABLED: bool = get_env_var("DATA_BACKUP_ENABLED", True, bool)
    DATA_BACKUP_INTERVAL: int = get_env_var("DATA_BACKUP_INTERVAL", 86400, int)  # 数据备份间隔（秒）
    DATA_BACKUP_DIR: str = get_env_var("DATA_BACKUP_DIR", "./backups", str)
    
    # 其他配置
    ERROR_REPORT_CHANNEL: Optional[str] = get_env_var("ERROR_REPORT_CHANNEL", None, str)
    AUTO_STARTUP_NOTIFY: bool = get_env_var("AUTO_STARTUP_NOTIFY", True, bool)
    LANGUAGE: str = get_env_var("LANGUAGE", "zh-CN", str)
    
    @classmethod
    def get_server_by_name(cls, name: str) -> Optional[Dict[str, Any]]:
        """通过名称获取服务器配置"""
        for server in cls.UNTURNED_SERVERS:
            if server.get("name") == name:
                return server
        return None
    
    @classmethod
    def get_server_by_address(cls, host: str, port: int) -> Optional[Dict[str, Any]]:
        """通过地址获取服务器配置"""
        for server in cls.UNTURNED_SERVERS:
            if server.get("host") == host and server.get("port") == port:
                return server
        return None

# 命令配置
class CommandConfig:
    """命令配置类"""
    # 命令权限配置
    COMMAND_PERMISSIONS: Dict[str, int] = {
        "help": 0,          # 所有用户可用
        "bind": 0,          # 所有用户可用
        "signin": 0,        # 所有用户可用
        "profile": 0,       # 所有用户可用
        "server_status": 0, # 所有用户可用
        "broadcast": 2,     # 管理员可用
        "add_admin": 2,     # 超级管理员可用
        "remove_admin": 2,  # 超级管理员可用
        "group_config": 1   # 群管理可用
    }
    
    # 命令描述
    COMMAND_DESCRIPTIONS: Dict[str, str] = {
        "help": "显示帮助信息",
        "bind": "绑定SteamID与QQ账号",
        "signin": "每日签到获取奖励",
        "profile": "查询个人信息",
        "server_status": "查询服务器状态",
        "broadcast": "发送广播消息",
        "add_admin": "添加管理员",
        "remove_admin": "移除管理员",
        "group_config": "配置群组设置"
    }
    
    # 命令使用说明
    COMMAND_USAGES: Dict[str, str] = {
        "help": "{prefix}help [命令]",
        "bind": "{prefix}bind <SteamID>",
        "signin": "{prefix}signin",
        "profile": "{prefix}profile [QQ号]",
        "server_status": "{prefix}server_status [服务器名称]",
        "broadcast": "{prefix}broadcast <消息>",
        "add_admin": "{prefix}add_admin <QQ号> <权限等级>",
        "remove_admin": "{prefix}remove_admin <QQ号>",
        "group_config": "{prefix}group_config <设置项> <值>"
    }
    
    @classmethod
    def get_permission_level(cls, command_name: str) -> int:
        """获取命令所需的权限等级"""
        return cls.COMMAND_PERMISSIONS.get(command_name, 1)
    
    @classmethod
    def get_description(cls, command_name: str) -> str:
        """获取命令描述"""
        return cls.COMMAND_DESCRIPTIONS.get(command_name, "未知命令")
    
    @classmethod
    def get_usage(cls, command_name: str, prefix: str = Config.COMMAND_PREFIX) -> str:
        """获取命令使用说明"""
        usage = cls.COMMAND_USAGES.get(command_name, "{prefix}{command}")
        return usage.format(prefix=prefix, command=command_name)

# 消息配置
class MessageConfig:
    """消息配置类"""
    # 通用消息
    COMMON_ERROR = "操作失败，请稍后重试"
    COMMON_SUCCESS = "操作成功"
    COMMON_PERMISSION_DENIED = "权限不足，无法执行此命令"
    COMMON_COOLDOWN = "命令冷却中，请等待{seconds}秒后再试"
    COMMON_NOT_FOUND = "未找到相关信息"
    
    # 绑定相关消息
    BIND_SUCCESS = "SteamID绑定成功！"
    BIND_ALREADY_BOUND = "您已经绑定了SteamID: {steam_id}"
    BIND_INVALID_STEAM_ID = "无效的SteamID，请重新输入"
    BIND_REQUIRED = "请先绑定SteamID，使用命令: {prefix}bind <SteamID>"
    
    # 签到相关消息
    SIGNIN_SUCCESS = "签到成功！获得{economy}经济点和{exp}经验值，连续签到{streak}天"
    SIGNIN_ALREADY_SIGNED = "您今天已经签到过了，明天再来吧！"
    SIGNIN_STREAK_REWARD = "连续签到{streak}天奖励！额外获得{bonus_economy}经济点和{bonus_exp}经验值"
    
    # 服务器监控相关消息
    SERVER_ONLINE = "服务器 {name} 已上线！\nIP: {host}:{port}\n当前在线人数: {players}/{max_players}\n延迟: {ping}ms"
    SERVER_OFFLINE = "服务器 {name} 已离线！\n上次在线时间: {last_online}\n离线原因: {reason}"
    SERVER_STATUS = "服务器状态 - {name}\n状态: {status}\nIP: {host}:{port}\n在线人数: {players}/{max_players}\n当前地图: {map}\n版本: {version}\n延迟: {ping}ms\n运行时间: {uptime}"
    SERVER_NOT_RESPONDING = "服务器 {name} 无响应，请检查服务器状态"
    
    # 个人信息相关消息
    PROFILE_INFO = "玩家信息\nQQ: {qq}\nSteamID: {steam_id}\n游戏时长: {playtime}\n签到次数: {signin_count}\n连续签到: {streak_days}天\n经济点: {economy}\n等级: {level}\n经验值: {exp}/{next_level_exp}\n上次登录: {last_login}\n注册时间: {register_time}"
    
    # 管理员相关消息
    ADMIN_ADD_SUCCESS = "已成功将QQ {qq} 添加为管理员，权限等级: {level}"
    ADMIN_REMOVE_SUCCESS = "已成功移除QQ {qq} 的管理员权限"
    ADMIN_ALREADY_EXISTS = "QQ {qq} 已经是管理员了"
    ADMIN_NOT_FOUND = "QQ {qq} 不是管理员"
    
    # 广播相关消息
    BROADCAST_SENT = "广播消息已发送"
    BROADCAST_REQUIRED = "请输入广播内容"
    
    # 群配置相关消息
    GROUP_CONFIG_SUCCESS = "群组配置已更新: {setting} = {value}"
    GROUP_CONFIG_INVALID = "无效的配置项或值"

# 权限配置
class PermissionConfig:
    """权限配置类"""
    # 权限等级定义
    PERMISSION_LEVELS: Dict[int, str] = {
        0: "普通用户",
        1: "群管理员",
        2: "超级管理员",
        3: "开发者"
    }
    
    # 最小权限等级
    MIN_PERMISSION_LEVEL = 0
    # 最大权限等级
    MAX_PERMISSION_LEVEL = 3
    
    @classmethod
    def get_level_name(cls, level: int) -> str:
        """获取权限等级名称"""
        return cls.PERMISSION_LEVELS.get(level, f"未知等级({level})")
    
    @classmethod
    def is_valid_level(cls, level: int) -> bool:
        """验证权限等级是否有效"""
        return cls.MIN_PERMISSION_LEVEL <= level <= cls.MAX_PERMISSION_LEVEL

# 配置实例导出
config = Config()
command_config = CommandConfig()
message_config = MessageConfig()
permission_config = PermissionConfig()