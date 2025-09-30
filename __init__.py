"""
UnturnedServer 插件包
"""
from nonebot import get_driver
from nonebot.adapters.onebot.v11 import Adapter as OneBotV11Adapter

# 注册OneBot V11适配器
driver = get_driver()
driver.register_adapter(OneBotV11Adapter)

# 加载当前目录下的所有插件
from nonebot import load_plugins
load_plugins(__file__.rsplit('\\', 1)[0])

__version__ = "0.1.0"
__all__ = ["__version__"]