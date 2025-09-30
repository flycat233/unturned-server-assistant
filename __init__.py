"""
Unturned服务器助手机器人插件
提供API消息发送、服务器监控、玩家管理、权限管理和实用命令系统
"""

import os
import sys
import nonebot
from nonebot.adapters.onebot.v11 import Adapter as OneBotV11Adapter
from pathlib import Path

# 确保当前目录在Python路径中
current_dir = Path(__file__).parent.resolve()
sys.path.append(str(current_dir))

# 初始化NoneBot
nonebot.init()

# 注册OneBot V11适配器
driver = nonebot.get_driver()
driver.register_adapter(OneBotV11Adapter)

# 加载当前目录下的所有插件（跨平台兼容的方式）
nonebot.load_plugins(str(current_dir))

if __name__ == "__main__":
    nonebot.run()