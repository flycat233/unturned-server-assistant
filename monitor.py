"""
Unturned服务器助手机器人监控模块
实现服务器监控逻辑和定时任务
"""
import asyncio
import time
from datetime import datetime
from typing import Optional, Dict, List, Any

from nonebot import get_bot, on_command
from nonebot.adapters.onebot.v11 import Bot, MessageSegment
from nonebot.permission import SUPERUSER

from core import config, logger, check_server_status, is_superuser
from database import database

# 全局变量记录上次服务器状态
_last_server_status = None
_is_monitoring = False
_monitor_task = None

# 监控命令（管理员专用）
monitor_cmd = on_command("monitor", aliases={"监控", "服务器监控"}, priority=10, block=True, permission=SUPERUSER)

@monitor_cmd.handle()
async def handle_monitor(bot: Bot):
    """处理监控命令"""
    global _is_monitoring
    
    if _is_monitoring:
        await monitor_cmd.finish(f"✅ 服务器监控已在运行中\n" +
                               f"监控间隔：{config.monitor_interval}秒\n" +
                               f"监控目标：{config.server_ip}:{config.server_port}\n" +
                               f"使用 /stopmonitor 停止监控")
    else:
        # 启动监控
        await start_monitoring()
        await monitor_cmd.finish(f"✅ 服务器监控已启动\n" +
                               f"监控间隔：{config.monitor_interval}秒\n" +
                               f"监控目标：{config.server_ip}:{config.server_port}")

# 停止监控命令（管理员专用）
stop_monitor_cmd = on_command("stopmonitor", aliases={"停止监控", "关闭监控"}, priority=10, block=True, permission=SUPERUSER)

@stop_monitor_cmd.handle()
async def handle_stop_monitor(bot: Bot):
    """处理停止监控命令"""
    global _is_monitoring
    
    if not _is_monitoring:
        await stop_monitor_cmd.finish("❌ 服务器监控未运行")
    else:
        # 停止监控
        await stop_monitoring()
        await stop_monitor_cmd.finish(f"✅ 服务器监控已停止\n" +
                                    f"监控目标：{config.server_ip}:{config.server_port}")

# 手动检查服务器状态命令（管理员专用）
check_cmd = on_command("check", aliases={"检查服务器", "检查状态"}, priority=10, block=True, permission=SUPERUSER)

@check_cmd.handle()
async def handle_check(bot: Bot):
    """处理手动检查服务器状态命令"""
    # 立即检查服务器状态
    status = await check_server_status(config.server_ip, config.server_port)
    
    # 记录服务器状态到数据库
    database.record_server_status(status)
    
    # 发送检查结果
    if status.get("online", False):
        check_result = (
            f"【服务器检查结果】✅ 在线\n" +
            f"服务器名称：{status.get('name', 'Unturned服务器')}\n" +
            f"IP地址：{config.server_ip}:{config.server_port}\n" +
            f"当前地图：{status.get('map', '未知')}\n" +
            f"版本：{status.get('version', '未知')}\n" +
            f"当前在线：{status.get('players', 0)}/{status.get('max_players', 0)} 人\n"
        )
    else:
        check_result = (
            f"【服务器检查结果】❌ 离线\n" +
            f"服务器名称：{config.server_ip}:{config.server_port}\n" +
            f"错误信息：{status.get('error', '未知错误')}\n"
        )
    
    await check_cmd.finish(check_result)

async def start_monitoring():
    """启动服务器监控"""
    global _is_monitoring, _monitor_task
    
    if _is_monitoring:
        logger.info("服务器监控已经在运行中")
        return
    
    _is_monitoring = True
    
    # 创建监控任务
    _monitor_task = asyncio.create_task(monitoring_task())
    logger.info(f"服务器监控已启动，监控间隔：{config.monitor_interval}秒")

async def stop_monitoring():
    """停止服务器监控"""
    global _is_monitoring, _monitor_task
    
    if not _is_monitoring:
        logger.info("服务器监控未运行")
        return
    
    _is_monitoring = False
    
    # 取消监控任务
    if _monitor_task and not _monitor_task.done():
        _monitor_task.cancel()
        try:
            await _monitor_task
        except asyncio.CancelledError:
            pass
    
    _monitor_task = None
    logger.info("服务器监控已停止")

async def monitoring_task():
    """监控任务主函数"""
    global _last_server_status
    
    logger.info(f"开始监控Unturned服务器: {config.server_ip}:{config.server_port}")
    
    try:
        while _is_monitoring:
            try:
                # 检查服务器状态
                current_status = await check_server_status(config.server_ip, config.server_port)
                
                # 记录服务器状态到数据库
                database.record_server_status(current_status)
                
                # 检查状态变化
                await check_status_change(current_status)
                
                # 更新上次状态
                _last_server_status = current_status
                
            except Exception as e:
                logger.error(f"监控任务执行出错: {e}")
            
            # 等待下一次检查
            await asyncio.sleep(config.monitor_interval)
    except asyncio.CancelledError:
        logger.info("监控任务已取消")
        raise
    except Exception as e:
        logger.error(f"监控任务异常终止: {e}")
        _is_monitoring = False

async def check_status_change(current_status: Dict[str, Any]):
    """检查服务器状态变化并发送通知"""
    global _last_server_status
    
    # 如果是首次检查，不发送通知
    if _last_server_status is None:
        logger.info(f"首次检查服务器状态: {'在线' if current_status.get('online', False) else '离线'}")
        return
    
    # 检查状态变化
    last_online = _last_server_status.get('online', False)
    current_online = current_status.get('online', False)
    
    # 状态变化：离线 -> 在线
    if not last_online and current_online:
        logger.info("服务器状态变化：离线 -> 在线")
        await send_server_online_notification(current_status)
    
    # 状态变化：在线 -> 离线
    elif last_online and not current_online:
        logger.info("服务器状态变化：在线 -> 离线")
        await send_server_offline_notification(current_status)
    
    # 状态未变化，但可能需要发送性能警报（例如玩家数过多）
    else:
        # 检查是否需要发送性能警报
        await check_performance_alerts(current_status)

async def get_notification_groups():
    """获取需要接收通知的群组列表"""
    # TODO: 从数据库中获取配置了接收通知的群组
    # 这里简化处理，返回所有超级用户的群
    # 实际应该从GroupManagement表中获取enable_monitor为1的群组
    groups = []
    
    # 注意：实际实现时应该查询数据库
    return groups

async def send_server_online_notification(status: Dict[str, Any]):
    """发送服务器上线通知"""
    # 获取需要通知的群组
    groups = await get_notification_groups()
    
    # 构建通知消息
    notification_message = (
        f"【服务器通知】🎉 服务器已上线\n" +
        f"服务器名称：{status.get('name', 'Unturned服务器')}\n" +
        f"IP地址：{config.server_ip}:{config.server_port}\n" +
        f"当前地图：{status.get('map', '未知')}\n" +
        f"版本：{status.get('version', '未知')}\n" +
        f"\n" +
        f"🎮 服务器已经可以正常访问，欢迎加入游戏！"
    )
    
    # 发送通知
    await send_notification_to_groups(groups, notification_message, "online")

async def send_server_offline_notification(status: Dict[str, Any]):
    """发送服务器下线通知"""
    # 获取需要通知的群组
    groups = await get_notification_groups()
    
    # 构建通知消息
    notification_message = (
        f"【服务器通知】⚠️ 服务器已下线\n" +
        f"服务器名称：{config.server_ip}:{config.server_port}\n" +
        f"错误信息：{status.get('error', '未知错误')}\n" +
        f"\n" +
        f"管理员正在处理中，请稍后再试..."
    )
    
    # 发送通知
    await send_notification_to_groups(groups, notification_message, "offline")

async def check_performance_alerts(status: Dict[str, Any]):
    """检查服务器性能警报"""
    # 如果服务器不在线，不检查性能
    if not status.get('online', False):
        return
    
    # 检查玩家数量是否达到警报阈值（例如达到最大玩家数的80%）
    players = status.get('players', 0)
    max_players = status.get('max_players', 50)
    
    if max_players > 0 and players >= max_players * 0.8:
        # 获取需要通知的群组
        groups = await get_notification_groups()
        
        # 构建性能警报消息
        alert_message = (
            f"【服务器性能警报】⚠️ 玩家数量即将达到上限\n" +
            f"服务器名称：{status.get('name', 'Unturned服务器')}\n" +
            f"当前在线：{players}/{max_players} 人\n" +
            f"\n" +
            f"建议管理员关注服务器性能，必要时考虑扩容或清理服务器负载"
        )
        
        # 发送性能警报
        await send_notification_to_groups(groups, alert_message, "performance")

async def send_notification_to_groups(groups: List[str], message: str, notification_type: str):
    """向多个群组发送通知"""
    if not groups:
        logger.warning(f"没有需要发送{notification_type}通知的群组")
        return
    
    # 获取第一个可用的机器人
    try:
        bot = get_bot().bots[list(get_bot().bots.keys())[0]]
    except IndexError:
        logger.error("没有可用的机器人")
        return
    
    success_count = 0
    failed_count = 0
    
    for group_id in groups:
        try:
            # 检查群配置，确认是否需要发送该类型的通知
            group_config = database.get_group_config(group_id)
            
            if notification_type == "online" and not group_config.get("notify_online", 1):
                continue
            elif notification_type == "offline" and not group_config.get("notify_offline", 1):
                continue
            
            # 发送通知消息
            await bot.send_group_msg(group_id=group_id, message=message)
            success_count += 1
            logger.info(f"向群组{group_id}发送{notification_type}通知成功")
        except Exception as e:
            failed_count += 1
            logger.error(f"向群组{group_id}发送{notification_type}通知失败: {e}")
    
    logger.info(f"发送{notification_type}通知完成，成功: {success_count}，失败: {failed_count}")

async def send_notification_to_superusers(message: str):
    """向所有超级用户发送通知"""
    if not config.superusers:
        logger.warning("没有配置超级用户，无法发送通知")
        return
    
    # 获取第一个可用的机器人
    try:
        bot = get_bot().bots[list(get_bot().bots.keys())[0]]
    except IndexError:
        logger.error("没有可用的机器人")
        return
    
    success_count = 0
    failed_count = 0
    
    for user_id in config.superusers:
        try:
            await bot.send_private_msg(user_id=user_id, message=message)
            success_count += 1
            logger.info(f"向超级用户{user_id}发送通知成功")
        except Exception as e:
            failed_count += 1
            logger.error(f"向超级用户{user_id}发送通知失败: {e}")
    
    logger.info(f"向超级用户发送通知完成，成功: {success_count}，失败: {failed_count}")

# 启动监控的函数（在插件加载时调用）
async def init_monitor():
    """初始化监控模块"""
    global _is_monitoring
    
    # 默认不自动启动监控，需要管理员手动启动
    _is_monitoring = False
    
    logger.info("服务器监控模块初始化完成")

# 当模块被加载时执行初始化
import asyncio
loop = asyncio.get_event_loop()
if loop.is_running():
    loop.create_task(init_monitor())
else:
    loop.run_until_complete(init_monitor())

# 导出监控控制函数
export_start_monitoring = start_monitoring
export_stop_monitoring = stop_monitoring