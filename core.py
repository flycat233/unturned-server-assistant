import nonebot
from nonebot.adapters.onebot.v11 import Adapter as OneBotV11Adapter
from .settings import get_config

# 获取配置
config = get_config()

# 初始化NoneBot
nonebot.init(config=config)

# 注册适配器
driver = nonebot.get_driver()
driver.register_adapter(OneBotV11Adapter)

# 加载插件
nonebot.load_plugins("f:\\UnturnedServer\\NoneBot2Plugin")

# 导出NoneBot实例供外部使用
bot = nonebot.get_bot
driver_instance = driver

# 启动前的准备工作
def on_startup():
    # 可以在这里添加启动前的初始化代码
    pass

# 关闭前的清理工作
def on_shutdown():
    # 可以在这里添加关闭前的清理代码
    pass

# 注册启动和关闭事件
@driver.on_startup
def startup():
    on_startup()

@driver.on_shutdown
def shutdown():
    on_shutdown()