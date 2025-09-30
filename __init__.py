"""
UnturnedServer 插件包
"""
from nonebot import get_driver
from nonebot.adapters.onebot.v11 import Adapter as OneBotV11Adapter

# 注册 OneBot V11 适配器
driver = get_driver()
driver.register_adapter(OneBotV11Adapter)

# 加载插件组件
from . import commands
from . import startup_notify
from . import api
from . import monitor
from . import onebot_http
from .database import init_db
from .settings import get_config

# 全局配置对象
config = get_config()

# 启动时执行的初始化任务
@driver.on_startup
async def startup():
    import logging
    import asyncio
    from nonebot.log import logger
    
    try:
        # 初始化数据库
        init_db()
        logger.info("✅ 数据库初始化完成")
        
        # 初始化 API 服务
        if hasattr(config, 'API_ENABLED') and config.API_ENABLED:
            await api.init_api_server()
            logger.info(f"✅ API 服务已启动: http://{config.API_HOST}:{config.API_PORT}")
        else:
            logger.info("ℹ️ API 服务已禁用")
        
        # 初始化服务器监控
        if hasattr(config, 'MONITOR_ENABLED') and config.MONITOR_ENABLED:
            await monitor.start_monitoring()
            logger.info(f"✅ 服务器监控已启动，检查间隔: {config.MONITOR_INTERVAL}秒")
        else:
            logger.info("ℹ️ 服务器监控已禁用")
        
        # 记录插件启动成功信息
        logger.info(f"🚀 Unturned服务器助手机器人插件已成功加载!")
        logger.info(f"📊 插件信息: 版本 {getattr(config, 'VERSION', '1.0.0')} | 超级用户数: {len(config.SUPERUSERS) if hasattr(config, 'SUPERUSERS') else 0} | 监控群数: {len(config.MONITOR_GROUPS) if hasattr(config, 'MONITOR_GROUPS') and config.MONITOR_GROUPS else 0}")
        
    except Exception as e:
        logger.error(f"❌ 插件启动失败: {str(e)}")
        raise

# 关闭时执行的清理任务
@driver.on_shutdown
async def shutdown():
    from nonebot.log import logger
    
    try:
        # 停止服务器监控
        if hasattr(config, 'MONITOR_ENABLED') and config.MONITOR_ENABLED:
            await monitor.stop_monitoring()
            logger.info("✅ 服务器监控已停止")
        
        # 停止 API 服务
        if hasattr(config, 'API_ENABLED') and config.API_ENABLED:
            await api.shutdown_api_server()
            logger.info("✅ API 服务已停止")
        
        logger.info("🛑 Unturned服务器助手机器人插件已关闭")
    except Exception as e:
        logger.error(f"❌ 插件关闭过程中发生错误: {str(e)}")

# 导出插件的公共接口
def get_plugin_version():
    """获取插件版本"""
    return getattr(config, 'VERSION', '1.0.0')

def is_monitoring_enabled():
    """检查监控是否启用"""
    return hasattr(config, 'MONITOR_ENABLED') and config.MONITOR_ENABLED

def is_api_enabled():
    """检查API服务是否启用"""
    return hasattr(config, 'API_ENABLED') and config.API_ENABLED