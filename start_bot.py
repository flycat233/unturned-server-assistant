import nonebot
from nonebot.adapters.onebot.v11 import Adapter as OneBotAdapter
from settings import get_config
from utils import logger

# 获取配置
config = get_config()

# 初始化NoneBot
nonebot.init(
    debug=config.DEBUG,
    superusers=set(config.SUPERUSERS),
    nickname=config.NICKNAME,
    command_start=config.COMMAND_START,
    command_sep=config.COMMAND_SEP
)

# 加载OneBot适配器
driver = nonebot.get_driver()
driver.register_adapter(OneBotAdapter)

# 从api模块注册事件
from api import register_api_events
register_api_events(driver)

# 加载插件
nonebot.load_builtin_plugins("echo")  # 加载内置回显插件用于测试

# 加载自定义模块
import core  # 核心功能
import commands  # 命令处理
import monitor  # 服务器监控

# 启动机器人
if __name__ == "__main__":
    try:
        logger.info(f"准备启动 Unturned服务器助手 v{config.VERSION}")
        logger.info(f"Debug模式: {'开启' if config.DEBUG else '关闭'}")
        logger.info(f"超级用户: {config.SUPERUSERS}")
        logger.info(f"命令前缀: {config.COMMAND_START}")
        
        # 启动NoneBot
        nonebot.run()
    except KeyboardInterrupt:
        logger.info("收到终止信号，正在关闭机器人...")
    except Exception as e:
        logger.error(f"机器人启动失败: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        logger.info("Unturned服务器助手已完全关闭")