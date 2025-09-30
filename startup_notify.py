import datetime
from nonebot import get_driver, logger
from nonebot.adapters.onebot.v11 import Bot
from nonebot.adapters.onebot.v11.message import Message
from .settings import get_config

# 获取配置
config = get_config()

# 记录上次发送的通知时间
last_notify_time = 0

# 发送启动通知
async def send_startup_notify(bot: Bot):
    if not config.notify_on_startup:
        logger.info("启动通知已禁用")
        return
    
    try:
        current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        message = f"🚀 Unturned服务器助手机器人已启动\n" \
                  f"启动时间: {current_time}\n" \
                  f"版本: v0.1.0\n" \
                  f"API服务: {'✅ 已启用' if config.api_enabled else '❌ 已禁用'}\n"
        
        # 向所有超级用户发送通知
        for user_id in config.superusers:
            try:
                await bot.send_private_msg(user_id=int(user_id), message=Message(message))
                logger.info(f"已向超级用户 {user_id} 发送启动通知")
            except Exception as e:
                logger.error(f"向超级用户 {user_id} 发送启动通知失败: {e}")
    except Exception as e:
        logger.error(f"发送启动通知失败: {e}")

# 发送关闭通知
async def send_shutdown_notify(bot: Bot):
    if not config.notify_on_shutdown:
        logger.info("关闭通知已禁用")
        return
    
    try:
        current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        message = f"🛑 Unturned服务器助手机器人即将关闭\n" \
                  f"关闭时间: {current_time}\n" \
                  f"感谢使用!"
        
        # 向所有超级用户发送通知
        for user_id in config.superusers:
            try:
                await bot.send_private_msg(user_id=int(user_id), message=Message(message))
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
        logger.info("机器人已连接到OneBot服务，准备发送启动通知")
        # 延迟发送通知，确保机器人完全就绪
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