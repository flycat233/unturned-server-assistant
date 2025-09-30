"""
Unturned服务器助手机器人启动通知模块
实现机器人启动时的通知功能
"""
import asyncio
from datetime import datetime
from typing import Optional

from nonebot import get_bot, on_startup
from nonebot.adapters.onebot.v11 import Bot

from core import config, logger

# 启动通知函数
@on_startup
def startup_notification():
    """机器人启动时的通知处理函数"""
    # 创建异步任务发送启动通知
    loop = asyncio.get_event_loop()
    loop.create_task(send_startup_notifications())

async def send_startup_notifications():
    """发送启动通知"""
    # 等待机器人连接稳定
    await asyncio.sleep(5)
    
    try:
        # 获取可用的机器人
        bot = get_bot().bots[list(get_bot().bots.keys())[0]] if get_bot().bots else None
        
        if not bot:
            logger.warning("没有可用的机器人，无法发送启动通知")
            return
        
        # 获取机器人信息
        bot_info = await bot.get_login_info()
        bot_name = bot_info.get("nickname", "未知机器人")
        bot_id = bot_info.get("user_id", "未知ID")
        
        # 构建启动通知消息
        startup_message = (
            f"【机器人启动通知】🎉\n" +
            f"机器人名称：{bot_name}\n" +
            f"机器人QQ：{bot_id}\n" +
            f"启动时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n" +
            f"\n" +
            f"🔧 当前配置\n" +
            f"监控服务器：{config.server_ip}:{config.server_port}\n" +
            f"监控间隔：{config.monitor_interval}秒\n" +
            f"每日签到奖励：{config.daily_sign_in_reward} 游戏币\n" +
            f"\n" +
            f"💡 使用提示\n" +
            f"1. 输入 /help 查看所有可用命令\n" +
            f"2. 输入 /monitor 启动服务器监控\n" +
            f"3. 输入 /status 查看服务器当前状态\n" +
            f"\n" +
            f"机器人已成功启动，随时为您服务！"
        )
        
        # 发送通知给所有超级用户
        success_count = 0
        failed_count = 0
        
        for user_id in config.superusers:
            try:
                await bot.send_private_msg(user_id=user_id, message=startup_message)
                success_count += 1
                logger.info(f"向超级用户{user_id}发送启动通知成功")
            except Exception as e:
                failed_count += 1
                logger.error(f"向超级用户{user_id}发送启动通知失败: {e}")
        
        logger.info(f"启动通知发送完成，成功: {success_count}，失败: {failed_count}")
        
    except Exception as e:
        logger.error(f"发送启动通知时发生错误: {e}")

async def send_shutdown_notifications():
    """发送关闭通知"""
    try:
        # 获取可用的机器人
        bot = get_bot().bots[list(get_bot().bots.keys())[0]] if get_bot().bots else None
        
        if not bot:
            logger.warning("没有可用的机器人，无法发送关闭通知")
            return
        
        # 获取机器人信息
        bot_info = await bot.get_login_info()
        bot_name = bot_info.get("nickname", "未知机器人")
        
        # 构建关闭通知消息
        shutdown_message = (
            f"【机器人关闭通知】🛑\n" +
            f"机器人名称：{bot_name}\n" +
            f"关闭时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n" +
            f"\n" +
            f"机器人即将关闭，如有需要请手动重启。"
        )
        
        # 发送通知给所有超级用户
        success_count = 0
        failed_count = 0
        
        for user_id in config.superusers:
            try:
                await bot.send_private_msg(user_id=user_id, message=shutdown_message)
                success_count += 1
                logger.info(f"向超级用户{user_id}发送关闭通知成功")
            except Exception as e:
                failed_count += 1
                logger.error(f"向超级用户{user_id}发送关闭通知失败: {e}")
        
        logger.info(f"关闭通知发送完成，成功: {success_count}，失败: {failed_count}")
        
    except Exception as e:
        logger.error(f"发送关闭通知时发生错误: {e}")

async def send_error_notification(error_message: str, error_source: str = "未知来源"):
    """发送错误通知给超级用户"""
    try:
        # 获取可用的机器人
        bot = get_bot().bots[list(get_bot().bots.keys())[0]] if get_bot().bots else None
        
        if not bot:
            logger.warning("没有可用的机器人，无法发送错误通知")
            return
        
        # 构建错误通知消息
        error_notification = (
            f"【机器人错误通知】⚠️\n" +
            f"错误来源：{error_source}\n" +
            f"发生时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n" +
            f"错误信息：{error_message}\n" +
            f"\n" +
            f"请管理员及时处理！"
        )
        
        # 发送通知给所有超级用户
        for user_id in config.superusers:
            try:
                await bot.send_private_msg(user_id=user_id, message=error_notification)
                logger.info(f"向超级用户{user_id}发送错误通知成功")
            except Exception as e:
                logger.error(f"向超级用户{user_id}发送错误通知失败: {e}")
        
    except Exception as e:
        logger.error(f"发送错误通知时发生错误: {e}")

# 导出通知函数供其他模块使用
export_send_startup_notifications = send_startup_notifications
export_send_shutdown_notifications = send_shutdown_notifications
export_send_error_notification = send_error_notification

# 注意：机器人关闭通知需要在nonebot的关闭钩子中调用
# 但nonebot目前没有直接的关闭钩子，可能需要通过其他方式实现
# 例如，可以在main函数中添加信号处理