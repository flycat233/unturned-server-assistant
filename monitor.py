import asyncio
import time
from nonebot import get_driver, logger
from .settings import get_config

# 获取配置
config = get_config()

# 服务器状态数据
server_status = {
    "is_online": False,
    "players": 0,
    "max_players": 0,
    "map": "Unknown",
    "last_update": 0
}

# 监控任务标志
bot_monitoring = False
monitor_task = None

# 初始化监控
async def init_monitor():
    global monitor_task
    if config.monitor_interval > 0:
        logger.info(f"启动服务器监控，间隔：{config.monitor_interval}秒")
        monitor_task = asyncio.create_task(monitor_loop())

# 停止监控
async def stop_monitor():
    global monitor_task, bot_monitoring
    if monitor_task:
        monitor_task.cancel()
        try:
            await monitor_task
        except asyncio.CancelledError:
            pass
        monitor_task = None
        bot_monitoring = False
        logger.info("服务器监控已停止")

# 监控循环
async def monitor_loop():
    global bot_monitoring
    bot_monitoring = True
    
    try:
        while bot_monitoring:
            try:
                await update_server_status()
            except Exception as e:
                logger.error(f"更新服务器状态失败: {e}")
            
            await asyncio.sleep(config.monitor_interval)
    except asyncio.CancelledError:
        bot_monitoring = False
        raise

# 更新服务器状态
async def update_server_status():
    global server_status
    
    # 这里应该包含实际获取服务器状态的逻辑
    # 目前使用模拟数据
    current_time = time.time()
    
    # 模拟状态更新
    # 在实际应用中，这里应该通过查询Unturned服务器API或其他方式获取真实状态
    server_status.update({
        "is_online": True,  # 假设服务器始终在线
        "players": 0,      # 假设当前没有玩家
        "max_players": 24, # 假设最大玩家数为24
        "map": "Unknown",  # 假设地图未知
        "last_update": current_time
    })
    
    # 记录日志
    logger.debug(f"服务器状态已更新: 在线={server_status['is_online']}, 玩家={server_status['players']}/{server_status['max_players']}")

# 获取当前服务器状态
def get_current_status():
    return server_status.copy()

# 驱动启动时初始化监控
@get_driver().on_startup
async def on_startup():
    await init_monitor()

# 驱动关闭时停止监控
@get_driver().on_shutdown
async def on_shutdown():
    await stop_monitor()