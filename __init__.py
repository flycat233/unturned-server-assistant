# UnturnedServerPlugin 包初始化文件

# 版本信息
try:
    from settings import get_config
    __version__ = get_config().VERSION
except ImportError:
    __version__ = "1.0.0"

# 导出主要模块和函数
from . import core
from . import commands
from . import monitor
from . import api
from . import database
from . import models
from . import utils

# 导出常用功能
__all__ = [
    "core",
    "commands",
    "monitor",
    "api",
    "database",
    "models",
    "utils"
]
