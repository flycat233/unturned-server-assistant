import datetime
import asyncio
from nonebot import get_driver, logger
from nonebot.adapters.onebot.v11 import Bot
from nonebot.adapters.onebot.v11.message import Message
from .settings import get_config
from .database import get_db, init_db
from .models import QQBotPlayers, GroupManagement

# 获取配置
config = get_config()

# 初始化数据库
init_db()

# 记录上次发送的通知时间
last_notify_time = 0

# 发送启动通知
async def send_startup_notify(bot: Bot):
    if not getattr(config, 'notify_on_startup', True):
        logger.info("启动通知已禁用")
        return
    
    try:
        # 获取当前时间
        current_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # 准备通知消息
        notification_msg = f"🚀 Unturned服务器助手机器人已启动！\n" \
                           f"版本: {getattr(config, 'VERSION', 'v0.1.0')}\n" \
                           f"启动时间: {current_time}\n" \
                           f"\n📊 系统状态:\n" \
                           f"✅ 数据库连接: 已建立\n" \
                           f"✅ API服务: {'运行中' if getattr(config, 'api_enabled', False) else '已禁用'}\n" \
                           f"✅ 服务器监控: {'运行中' if getattr(config, 'MONITOR_ENABLED', False) else '已禁用'}\n" \
                           f"\n💡 使用提示:\n" \
                           f"- 发送 /help 查看所有可用命令\n" \
                           f"- 发送 /server 查看服务器状态\n" \
                           f"- 管理员可发送 /broadcast 发送公告"
        
        # 向所有超级用户发送通知
        if hasattr(config, 'superusers') and config.superusers:
            for user_id in config.superusers:
                try:
                    await bot.send_private_msg(user_id=int(user_id), message=Message(notification_msg))
                    logger.info(f"已向超级用户 {user_id} 发送启动通知")
                except Exception as e:
                    logger.error(f"向超级用户 {user_id} 发送启动通知失败: {e}")
        else:
            logger.warning("未配置超级用户，跳过启动通知")
            
        # 发送通知到监控群
        if hasattr(config, 'MONITOR_GROUPS') and config.MONITOR_GROUPS:
            for group_id in config.MONITOR_GROUPS:
                try:
                    await bot.send_group_msg(
                        group_id=int(group_id),
                        message=Message(f"📢 机器人已启动，现在可以使用各种命令了！\n" \
                                        f"发送 /help 查看所有可用命令")
                    )
                    logger.info(f"已向监控群 {group_id} 发送启动通知")
                except Exception as e:
                    logger.error(f"向监控群 {group_id} 发送启动通知失败: {e}")
    except Exception as e:
        logger.error(f"发送启动通知失败: {e}")

# 发送关闭通知
async def send_shutdown_notify(bot: Bot):
    if not getattr(config, 'notify_on_shutdown', True):
        logger.info("关闭通知已禁用")
        return
    
    try:
        # 获取当前时间
        current_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # 准备通知消息
        shutdown_msg = f"🛑 Unturned服务器助手机器人已关闭！\n" \
                       f"版本: {getattr(config, 'VERSION', 'v0.1.0')}\n" \
                       f"关闭时间: {current_time}\n" \
                       f"下次启动时间: 待定\n" \
                       f"感谢使用！"
        
        # 向所有超级用户发送通知
        if hasattr(config, 'superusers') and config.superusers:
            for user_id in config.superusers:
                try:
                    await bot.send_private_msg(user_id=int(user_id), message=Message(shutdown_msg))
                    logger.info(f"已向超级用户 {user_id} 发送关闭通知")
                except Exception as e:
                    logger.error(f"向超级用户 {user_id} 发送关闭通知失败: {e}")
    except Exception as e:
        logger.error(f"发送关闭通知失败: {e}")

# 机器人连接成功后的启动通知
def register_notify_hooks():
    driver = get_driver()
    
    # 机器人上线时发送启动通知
    @driver.on_bot_connect
    async def handle_bot_connect(bot: Bot):
        logger.info(f"机器人 {bot.self_id} 已连接到OneBot服务")
        # 延迟发送通知，确保系统完全初始化
        await asyncio.sleep(3)
        await send_startup_notify(bot)
    
    # 驱动关闭时发送关闭通知（需要在机器人连接状态下才能发送）
    @driver.on_shutdown
    async def handle_driver_shutdown():
        logger.info("机器人即将关闭，尝试发送关闭通知")
        bots = list(get_driver().bots.values())
        if bots:
            # 选择第一个可用的机器人发送通知
            await send_shutdown_notify(bots[0])
        else:
            logger.warning("没有可用的机器人实例，无法发送关闭通知")

# 注册通知钩子
register_notify_hooks()