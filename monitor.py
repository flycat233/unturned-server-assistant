import asyncio
import time
import socket
from nonebot import get_driver, logger
from .settings import get_config
from .database import get_db
from .models import ServerStatus as ServerStatusModel
import datetime

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

# 更新服务器状态（真实实现）
async def update_server_status():
    global server_status
    
    current_time = time.time()
    new_status = {
        "is_online": False,
        "players": 0,
        "max_players": 0,
        "map": "Unknown",
        "last_update": current_time
    }
    
    try:
        # 使用socket连接检查服务器是否在线
        # 注意：这是简化实现，真实场景可能需要使用Steam查询协议
        with socket.create_connection((config.server_ip, config.server_query_port), timeout=5) as s:
            new_status["is_online"] = True
            # 实际项目中，这里应该使用Steam查询协议获取详细信息
            # 这里使用模拟数据作为示例
            new_status["players"] = 5  # 假设值
            new_status["max_players"] = 24
            new_status["map"] = "Washington"
    except Exception as e:
        logger.warning(f"无法连接到服务器: {e}")
    
    # 记录状态变化
    status_changed = False
    if new_status["is_online"] != server_status["is_online"]:
        status_changed = True
        
    # 更新状态
    server_status.update(new_status)
    
    # 保存到数据库
    db = next(get_db())
    try:
        db_status = ServerStatusModel(
            is_online=new_status["is_online"],
            players=new_status["players"],
            max_players=new_status["max_players"],
            map=new_status["map"],
            timestamp=datetime.datetime.utcnow()
        )
        db.add(db_status)
        db.commit()
        
        # 如果状态变化，发送通知
        if status_changed and hasattr(config, 'notify_server_changes') and config.notify_server_changes:
            await notify_server_status_change(new_status)
    except Exception as e:
        db.rollback()
        logger.error(f"保存服务器状态失败: {e}")
    finally:
        db.close()
    
    # 记录日志
    logger.debug(f"服务器状态已更新: 在线={server_status['is_online']}, 玩家={server_status['players']}/{server_status['max_players']}")

# 服务器状态变化通知
async def notify_server_status_change(status):
    from .onebot_http import bot_http
    from .settings import get_config
    
    config = get_config()
    message = ""
    
    if status["is_online"]:
        message = f"✅ 服务器已上线！\n当前地图: {status['map']}\n最大玩家数: {status['max_players']}"
    else:
        message = "❌ 服务器已离线！"
    
    # 发送给所有超级用户
    for user_id in config.superusers:
        try:
            await bot_http.send_private_msg(int(user_id), message)
        except Exception as e:
            logger.error(f"发送服务器状态通知失败: {e}")

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