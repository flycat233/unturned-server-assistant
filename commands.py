from nonebot import on_command
from nonebot.adapters import Event
from nonebot.typing import T_State
from nonebot.permission import SUPERUSER
from nonebot.adapters.onebot.v11 import Message
from .settings import get_config

# 获取配置
config = get_config()

# 示例命令：echo
# 重复用户发送的内容
echo = on_command("echo", priority=10, block=True)

@echo.handle()
async def handle_echo(event: Event, state: T_State):
    args = str(event.get_message()).strip()
    if args:
        state["echo_msg"] = args

@echo.got("echo_msg", prompt="请输入要重复的内容")
async def got_echo_msg(event: Event, state: T_State):
    echo_msg = state["echo_msg"]
    await echo.finish(f"你说的是：{echo_msg}")

# 示例命令：server
# 查询服务器状态
server_status = on_command("server", aliases={"服务器状态"}, priority=10, block=True)

@server_status.handle()
async def handle_server_status():
    # 这里可以添加实际获取服务器状态的逻辑
    await server_status.finish(Message("服务器当前状态：运行中\n在线人数：0/24\n当前地图：Unknown"))

# 示例命令：restart（仅超级用户可用）
# 重启机器人（仅超级用户可用）
restart_bot = on_command("restart", aliases={"重启"}, permission=SUPERUSER, priority=5, block=True)

@restart_bot.handle()
async def handle_restart_bot():
    await restart_bot.send("正在准备重启机器人...")
    # 实际重启逻辑通常需要外部脚本配合
    await restart_bot.finish("机器人重启命令已执行，请手动检查机器人状态")