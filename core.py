from nonebot import get_driver, on_command, on_message, on_notice
from nonebot.adapters.onebot.v11 import Message, GroupMessageEvent, PrivateMessageEvent, Bot
from nonebot.params import CommandArg
from nonebot.permission import SUPERUSER
from settings import get_config
from utils import logger, is_superuser, send_onebot_message, log_command

# 获取配置
config = get_config()

# 机器人驱动
_driver = get_driver()

# 核心状态管理
class BotCore:
    _instance = None
    _initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(BotCore, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not self._initialized:
            self.is_running = False
            self.start_time = None
            self.connected_bots = {}
            self._initialized = True
    
    def start(self):
        self.is_running = True
        self.start_time = get_config().get_current_timestamp()
        logger.info("机器人核心服务已启动")
    
    def stop(self):
        self.is_running = False
        logger.info("机器人核心服务已停止")
    
    def register_bot(self, bot: Bot):
        self.connected_bots[bot.self_id] = bot
        logger.info(f"机器人 {bot.self_id} 已注册")
    
    def unregister_bot(self, bot: Bot):
        if bot.self_id in self.connected_bots:
            del self.connected_bots[bot.self_id]
            logger.info(f"机器人 {bot.self_id} 已注销")

# 创建全局核心实例
bot_core = BotCore()

# 注册机器人连接事件
@_driver.on_bot_connect
async def handle_bot_connect(bot: Bot):
    bot_core.register_bot(bot)
    
    # 发送启动通知（如果启用）
    if config.NOTIFY_ON_STARTUP:
        for group_id in config.MONITOR_GROUPS:
            await send_onebot_message(
                "group",
                group_id=group_id,
                message=f"✅ Unturned服务器助手已启动！\n当前版本: {config.VERSION}\n服务器监控: {'已启用' if config.MONITOR_ENABLED else '已禁用'}"
            )

# 注册机器人断开连接事件
@_driver.on_bot_disconnect
async def handle_bot_disconnect(bot: Bot):
    bot_core.unregister_bot(bot)
    
    # 发送关闭通知（如果启用）
    if config.NOTIFY_ON_SHUTDOWN:
        # 注意：此处可能无法发送消息，因为机器人已断开连接
        logger.info("准备发送机器人断开连接通知")

# 注册生命周期事件
@_driver.on_startup
async def on_startup():
    bot_core.start()
    logger.info(f"Unturned服务器助手 v{config.VERSION} 启动成功！")
    
    # 初始化数据库
    try:
        from database import init_db
        init_db()
        logger.info("数据库初始化成功")
    except Exception as e:
        logger.error(f"数据库初始化失败: {str(e)}")

@_driver.on_shutdown
async def on_shutdown():
    bot_core.stop()
    logger.info("Unturned服务器助手已关闭")

# 通用命令处理器
async def process_command(event, bot, command_name, handler_func, is_admin_only=False):
    """处理命令并记录日志"""
    user_id = event.user_id
    group_id = getattr(event, "group_id", None)
    
    # 检查是否为管理员命令
    if is_admin_only and not await SUPERUSER(bot, event):
        await bot.send(event, "❌ 权限不足，只有超级用户可以使用此命令")
        log_command(user_id, group_id, command_name, "", False, "权限不足")
        return
    
    try:
        # 调用命令处理函数
        result = await handler_func(event, bot)
        log_command(user_id, group_id, command_name, "", True, str(result))
        return result
    except Exception as e:
        error_msg = f"命令执行出错: {str(e)}"
        logger.error(error_msg)
        await bot.send(event, f"❌ {error_msg}")
        log_command(user_id, group_id, command_name, "", False, error_msg)
        return None

# 获取机器人状态
def get_bot_status():
    status = {
        "version": config.VERSION,
        "is_running": bot_core.is_running,
        "start_time": bot_core.start_time,
        "connected_bots_count": len(bot_core.connected_bots),
        "connected_bots": list(bot_core.connected_bots.keys()),
        "monitor_enabled": config.MONITOR_ENABLED,
        "api_enabled": config.API_ENABLED
    }
    return status

# 导入settings.py中的get_current_timestamp函数
def get_current_timestamp():
    from utils import get_current_timestamp as util_get_timestamp
    return util_get_timestamp()