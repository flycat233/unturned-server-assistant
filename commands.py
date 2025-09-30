"""
Unturned服务器助手机器人命令模块
实现所有命令的逻辑和消息处理规则
"""
from nonebot import on_command, on_message, on_notice, on_request
from nonebot.adapters import Message
from nonebot.adapters.onebot.v11 import MessageSegment, GroupMessageEvent, PrivateMessageEvent, Bot, Event
from nonebot.params import CommandArg, Arg, ArgStr, T_State
from nonebot.permission import SUPERUSER
from nonebot.typing import T_Handler
from typing import Optional, Dict, Any, List
from datetime import datetime

from core import config, is_superuser, check_server_status, logger
from database import database

# 命令前缀设置
# nonebot默认使用"/"作为命令前缀，可以在.env文件中配置

# 帮助命令
help_cmd = on_command("help", aliases={"帮助", "使用说明", "命令列表"}, priority=10, block=True)

@help_cmd.handle()
async def handle_help(bot: Bot, event: Event):
    """处理帮助命令"""
    help_text = (
        "【Unturned服务器助手机器人命令列表】\n"
        "\n"
        "🔹 基础命令\n"
        "/help 或 /帮助 - 显示本帮助信息\n"
        "/bind [SteamID] - 绑定你的QQ账号与SteamID\n"
        "/sign 或 /签到 - 每日签到获取游戏内奖励\n"
        "/me 或 /个人信息 - 查询你的游戏数据和统计信息\n"
        "/status 或 /服务器状态 - 查询Unturned服务器当前状态\n"
        "\n"
        "🔹 管理员命令（需权限）\n"
        "/broadcast [消息内容] - 向所有监控群发送公告\n"
        "/addadmin [QQ号] - 在当前群添加管理员\n"
        "/removeadmin [QQ号] - 在当前群移除管理员\n"
        "/groupconfig - 查看和修改群配置\n"
        "\n"
        "使用说明：所有命令以斜杠/开头，私聊和群聊均可使用\n"
        "注意：部分命令需要相应权限才能使用"
    )
    
    # 记录命令日志
    database.log_command(
        qq_id=str(event.user_id),
        group_id=str(event.group_id) if hasattr(event, 'group_id') else None,
        command="help",
        success=True
    )
    
    await help_cmd.finish(help_text)

# 绑定命令
bind_cmd = on_command("bind", aliases={"绑定"}, priority=10, block=True)

@bind_cmd.handle()
async def handle_bind_first_receive(bot: Bot, event: Event, args: Message = CommandArg()):
    """首次接收绑定命令"""
    # 检查是否已提供SteamID参数
    if args.extract_plain_text().strip():
        await handle_bind_receive_steam_id(bot, event, args)

@bind_cmd.got("steam_id", prompt="请输入你的SteamID（数字ID）：")
async def handle_bind_receive_steam_id(bot: Bot, event: Event, state: T_State):
    """接收并处理SteamID"""
    steam_id = str(state["steam_id"]).strip()
    
    # 简单验证SteamID格式（应该是纯数字）
    if not steam_id.isdigit():
        await bind_cmd.reject("SteamID格式不正确，请输入纯数字的SteamID：")
        return
    
    # 获取用户昵称
    user_nickname = ""
    if isinstance(event, GroupMessageEvent):
        user_info = await bot.get_group_member_info(group_id=event.group_id, user_id=event.user_id)
        user_nickname = user_info.get("nickname", "")
    elif isinstance(event, PrivateMessageEvent):
        user_info = await bot.get_stranger_info(user_id=event.user_id)
        user_nickname = user_info.get("nickname", "")
    
    # 执行绑定操作
    qq_id = str(event.user_id)
    success = database.bind_qq_steam(qq_id, steam_id, user_nickname)
    
    if success:
        # 记录命令日志
        database.log_command(
            qq_id=qq_id,
            group_id=str(event.group_id) if hasattr(event, 'group_id') else None,
            command="bind",
            parameters=steam_id,
            success=True
        )
        
        await bind_cmd.finish(f"✅ 绑定成功！\n你的QQ号 {qq_id} 已成功绑定SteamID {steam_id}")
    else:
        # 记录命令日志
        database.log_command(
            qq_id=qq_id,
            group_id=str(event.group_id) if hasattr(event, 'group_id') else None,
            command="bind",
            parameters=steam_id,
            success=False,
            error_message="数据库操作失败"
        )
        
        await bind_cmd.finish("❌ 绑定失败，请稍后重试")

# 签到命令
sign_cmd = on_command("sign", aliases={"签到"}, priority=10, block=True)

@sign_cmd.handle()
async def handle_sign(bot: Bot, event: Event):
    """处理签到命令"""
    qq_id = str(event.user_id)
    
    # 获取绑定的SteamID
    steam_id = database.get_steam_id_by_qq(qq_id)
    if not steam_id:
        # 记录命令日志
        database.log_command(
            qq_id=qq_id,
            group_id=str(event.group_id) if hasattr(event, 'group_id') else None,
            command="sign",
            success=False,
            error_message="未绑定SteamID"
        )
        
        await sign_cmd.finish("❌ 签到失败！\n你还没有绑定SteamID，请先使用 /bind 命令绑定")
        return
    
    # 检查今天是否已签到
    if database.has_signed_in_today(steam_id):
        # 记录命令日志
        database.log_command(
            qq_id=qq_id,
            group_id=str(event.group_id) if hasattr(event, 'group_id') else None,
            command="sign",
            success=False,
            error_message="今日已签到"
        )
        
        # 获取下次签到时间（明天0点）
        now = datetime.now()
        tomorrow = (now.replace(hour=0, minute=0, second=0, microsecond=0) + 
                   datetime.timedelta(days=1))
        hours, remainder = divmod((tomorrow - now).seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        
        await sign_cmd.finish(
            f"❌ 签到失败！\n你今天已经签到过了，距离下次签到还有 {hours} 小时 {minutes} 分钟"
        )
        return
    
    # 执行签到操作
    reward = config.daily_sign_in_reward
    sign_success = database.record_sign_in(steam_id, reward)
    balance_success = database.update_balance(steam_id, reward, is_add=True)
    
    if sign_success and balance_success:
        # 获取签到次数
        sign_count = database.get_sign_in_count(steam_id)
        # 获取当前余额
        balance = database.get_balance(steam_id)
        
        # 记录命令日志
        database.log_command(
            qq_id=qq_id,
            group_id=str(event.group_id) if hasattr(event, 'group_id') else None,
            command="sign",
            success=True,
            parameters=f"reward={reward}"
        )
        
        await sign_cmd.finish(
            f"✅ 签到成功！\n" +
            f"获得奖励：{reward} 游戏币\n" +
            f"当前余额：{balance} 游戏币\n" +
            f"累计签到：{sign_count} 天\n" +
            f"继续保持，明日还有更多奖励等着你～"
        )
    else:
        # 记录命令日志
        database.log_command(
            qq_id=qq_id,
            group_id=str(event.group_id) if hasattr(event, 'group_id') else None,
            command="sign",
            success=False,
            error_message="签到操作失败"
        )
        
        await sign_cmd.finish("❌ 签到失败，请稍后重试")

# 个人信息命令
me_cmd = on_command("me", aliases={"个人信息", "我的信息"}, priority=10, block=True)

@me_cmd.handle()
async def handle_me(bot: Bot, event: Event):
    """处理个人信息命令"""
    qq_id = str(event.user_id)
    
    # 获取绑定的SteamID
    steam_id = database.get_steam_id_by_qq(qq_id)
    if not steam_id:
        # 记录命令日志
        database.log_command(
            qq_id=qq_id,
            group_id=str(event.group_id) if hasattr(event, 'group_id') else None,
            command="me",
            success=False,
            error_message="未绑定SteamID"
        )
        
        await me_cmd.finish("❌ 查询失败！\n你还没有绑定SteamID，请先使用 /bind 命令绑定")
        return
    
    # 获取玩家统计数据
    player_stats = database.get_player_stats(steam_id)
    if not player_stats:
        # 记录命令日志
        database.log_command(
            qq_id=qq_id,
            group_id=str(event.group_id) if hasattr(event, 'group_id') else None,
            command="me",
            success=False,
            error_message="未找到玩家数据"
        )
        
        await me_cmd.finish("❌ 查询失败！\n未找到你的游戏数据")
        return
    
    # 获取经济数据
    balance = database.get_balance(steam_id)
    # 获取签到次数
    sign_count = database.get_sign_in_count(steam_id)
    
    # 格式化个人信息
    info_text = (
        f"【个人信息】\n" +
        f"QQ号：{qq_id}\n" +
        f"SteamID：{steam_id}\n" +
        f"\n" +
        f"【游戏数据】\n" +
        f"总游戏时长：{player_stats.get('total_play_time', 0)} 分钟\n" +
        f"击杀数：{player_stats.get('kill_count', 0)}\n" +
        f"死亡数：{player_stats.get('death_count', 0)}\n" +
        f"僵尸击杀：{player_stats.get('zombie_kills', 0)}\n" +
        f"爆头数：{player_stats.get('headshots', 0)}\n" +
        f"游戏场次：{player_stats.get('play_sessions', 0)}\n" +
        f"\n" +
        f"【经济数据】\n" +
        f"当前余额：{balance} 游戏币\n" +
        f"累计签到：{sign_count} 天\n"
    )
    
    # 记录命令日志
    database.log_command(
        qq_id=qq_id,
        group_id=str(event.group_id) if hasattr(event, 'group_id') else None,
        command="me",
        success=True
    )
    
    await me_cmd.finish(info_text)

# 服务器状态命令
status_cmd = on_command("status", aliases={"服务器状态", "服务器信息"}, priority=10, block=True)

@status_cmd.handle()
async def handle_status(bot: Bot, event: Event):
    """处理服务器状态命令"""
    # 获取服务器状态
    status = await check_server_status(config.server_ip, config.server_port)
    
    # 记录服务器状态到数据库
    database.record_server_status(status)
    
    # 格式化服务器状态信息
    if status.get("online", False):
        status_text = (
            f"【服务器状态】✅ 在线\n" +
            f"服务器名称：{status.get('name', 'Unturned服务器')}\n" +
            f"IP地址：{config.server_ip}:{config.server_port}\n" +
            f"当前地图：{status.get('map', '未知')}\n" +
            f"版本：{status.get('version', '未知')}\n" +
            f"\n" +
            f"【玩家信息】\n" +
            f"当前在线：{status.get('players', 0)}/{status.get('max_players', 0)} 人\n" +
            f"\n" +
            f"🎮 服务器正常运行中，欢迎加入游戏！"
        )
    else:
        status_text = (
            f"【服务器状态】❌ 离线\n" +
            f"服务器名称：{config.server_ip}:{config.server_port}\n" +
            f"错误信息：{status.get('error', '未知错误')}\n" +
            f"\n" +
            f"⚠️ 服务器当前不可用，请稍后再试或联系管理员"
        )
    
    # 记录命令日志
    database.log_command(
        qq_id=str(event.user_id),
        group_id=str(event.group_id) if hasattr(event, 'group_id') else None,
        command="status",
        success=True
    )
    
    await status_cmd.finish(status_text)

# 广播命令（管理员专用）
broadcast_cmd = on_command("broadcast", aliases={"广播", "公告"}, priority=10, block=True, permission=SUPERUSER)

@broadcast_cmd.handle()
async def handle_broadcast_first_receive(bot: Bot, event: Event, args: Message = CommandArg()):
    """首次接收广播命令"""
    # 检查是否已提供广播内容
    if args.extract_plain_text().strip():
        await handle_broadcast_receive_content(bot, event, args)

@broadcast_cmd.got("content", prompt="请输入要广播的公告内容：")
async def handle_broadcast_receive_content(bot: Bot, event: Event, state: T_State):
    """接收并处理广播内容"""
    content = str(state["content"]).strip()
    if not content:
        await broadcast_cmd.reject("广播内容不能为空，请重新输入：")
        return
    
    # 添加广播标记
    broadcast_message = f"【系统公告】\n{content}\n—— 管理员广播"
    
    # 获取所有启用了监控的群组（这里简化处理）
    # TODO: 从数据库中获取所有启用了监控的群组
    groups = []  # 实际应该从GroupManagement表中获取
    
    # 如果是在群聊中发起的广播，至少包含当前群
    if isinstance(event, GroupMessageEvent):
        groups.append(str(event.group_id))
    
    # 如果没有可广播的群组
    if not groups:
        # 记录命令日志
        database.log_command(
            qq_id=str(event.user_id),
            group_id=str(event.group_id) if hasattr(event, 'group_id') else None,
            command="broadcast",
            parameters=content,
            success=False,
            error_message="没有可广播的群组"
        )
        
        await broadcast_cmd.finish("❌ 广播失败！\n当前没有可广播的群组")
        return
    
    # 发送广播消息
    success_count = 0
    failed_count = 0
    failed_groups = []
    
    for group_id in groups:
        try:
            await bot.send_group_msg(group_id=group_id, message=broadcast_message)
            success_count += 1
        except Exception as e:
            logger.error(f"向群组{group_id}发送广播失败: {e}")
            failed_count += 1
            failed_groups.append(group_id)
    
    # 添加公告到数据库
    database.add_announcement(
        title="系统广播",
        content=content,
        author=str(event.user_id)
    )
    
    # 记录命令日志
    database.log_command(
        qq_id=str(event.user_id),
        group_id=str(event.group_id) if hasattr(event, 'group_id') else None,
        command="broadcast",
        parameters=content,
        success=True
    )
    
    # 返回广播结果
    result_text = (
        f"✅ 广播发送完成！\n" +
        f"成功发送：{success_count} 个群组\n" +
        f"发送失败：{failed_count} 个群组\n"
    )
    
    if failed_groups:
        result_text += f"失败的群组：{', '.join(failed_groups)}\n"
    
    await broadcast_cmd.finish(result_text)

# 群管理命令：添加管理员
add_admin_cmd = on_command("addadmin", aliases={"添加管理员"}, priority=10, block=True)

@add_admin_cmd.handle()
async def handle_add_admin(bot: Bot, event: Event, args: Message = CommandArg()):
    """处理添加管理员命令"""
    # 检查是否为群聊环境
    if not isinstance(event, GroupMessageEvent):
        await add_admin_cmd.finish("❌ 只能在群聊中使用此命令")
        return
    
    # 检查用户权限（必须是超级用户或群主/群管理员）
    qq_id = str(event.user_id)
    group_id = str(event.group_id)
    
    if not is_superuser(qq_id):
        # 检查是否为群主或群管理员
        member_info = await bot.get_group_member_info(group_id=group_id, user_id=event.user_id)
        if member_info.get("role", "") not in ["owner", "admin"]:
            await add_admin_cmd.finish("❌ 你没有权限执行此命令")
            return
    
    # 获取要添加的管理员QQ号
    admin_qq = args.extract_plain_text().strip()
    if not admin_qq or not admin_qq.isdigit():
        await add_admin_cmd.finish("❌ 请输入正确的QQ号，格式：/addadmin [QQ号]")
        return
    
    # 获取当前群配置
    group_config = database.get_group_config(group_id)
    admin_list = group_config.get("admin_list", "").split(",") if group_config.get("admin_list") else []
    
    # 检查是否已存在
    if admin_qq in admin_list:
        await add_admin_cmd.finish(f"❌ QQ号 {admin_qq} 已经是本群管理员")
        return
    
    # 添加到管理员列表
    admin_list.append(admin_qq)
    new_admin_list = ",".join(admin_list)
    
    # 更新群配置
    success = database.update_group_config(group_id, {"admin_list": new_admin_list})
    
    if success:
        # 记录命令日志
        database.log_command(
            qq_id=qq_id,
            group_id=group_id,
            command="addadmin",
            parameters=admin_qq,
            success=True
        )
        
        await add_admin_cmd.finish(f"✅ 成功添加QQ号 {admin_qq} 为本群管理员")
    else:
        # 记录命令日志
        database.log_command(
            qq_id=qq_id,
            group_id=group_id,
            command="addadmin",
            parameters=admin_qq,
            success=False,
            error_message="数据库操作失败"
        )
        
        await add_admin_cmd.finish("❌ 添加管理员失败，请稍后重试")

# 群管理命令：移除管理员
remove_admin_cmd = on_command("removeadmin", aliases={"移除管理员"}, priority=10, block=True)

@remove_admin_cmd.handle()
async def handle_remove_admin(bot: Bot, event: Event, args: Message = CommandArg()):
    """处理移除管理员命令"""
    # 检查是否为群聊环境
    if not isinstance(event, GroupMessageEvent):
        await remove_admin_cmd.finish("❌ 只能在群聊中使用此命令")
        return
    
    # 检查用户权限（必须是超级用户或群主/群管理员）
    qq_id = str(event.user_id)
    group_id = str(event.group_id)
    
    if not is_superuser(qq_id):
        # 检查是否为群主或群管理员
        member_info = await bot.get_group_member_info(group_id=group_id, user_id=event.user_id)
        if member_info.get("role", "") not in ["owner", "admin"]:
            await remove_admin_cmd.finish("❌ 你没有权限执行此命令")
            return
    
    # 获取要移除的管理员QQ号
    admin_qq = args.extract_plain_text().strip()
    if not admin_qq or not admin_qq.isdigit():
        await remove_admin_cmd.finish("❌ 请输入正确的QQ号，格式：/removeadmin [QQ号]")
        return
    
    # 获取当前群配置
    group_config = database.get_group_config(group_id)
    admin_list = group_config.get("admin_list", "").split(",") if group_config.get("admin_list") else []
    
    # 检查是否存在
    if admin_qq not in admin_list:
        await remove_admin_cmd.finish(f"❌ QQ号 {admin_qq} 不是本群管理员")
        return
    
    # 从管理员列表移除
    admin_list.remove(admin_qq)
    new_admin_list = ",".join(admin_list)
    
    # 更新群配置
    success = database.update_group_config(group_id, {"admin_list": new_admin_list})
    
    if success:
        # 记录命令日志
        database.log_command(
            qq_id=qq_id,
            group_id=group_id,
            command="removeadmin",
            parameters=admin_qq,
            success=True
        )
        
        await remove_admin_cmd.finish(f"✅ 成功移除QQ号 {admin_qq} 的本群管理员权限")
    else:
        # 记录命令日志
        database.log_command(
            qq_id=qq_id,
            group_id=group_id,
            command="removeadmin",
            parameters=admin_qq,
            success=False,
            error_message="数据库操作失败"
        )
        
        await remove_admin_cmd.finish("❌ 移除管理员失败，请稍后重试")

# 群配置命令
group_config_cmd = on_command("groupconfig", aliases={"群配置", "群设置"}, priority=10, block=True)

def is_group_admin(bot: Bot, event: GroupMessageEvent) -> bool:
    """检查用户是否为群管理员"""
    # 超级用户始终有管理权限
    if is_superuser(str(event.user_id)):
        return True
    
    # 获取群配置
    group_config = database.get_group_config(str(event.group_id))
    admin_list = group_config.get("admin_list", "").split(",") if group_config.get("admin_list") else []
    
    # 检查是否在管理员列表中
    if str(event.user_id) in admin_list:
        return True
    
    # 检查是否为群主或群管理员
    # 注意：这里需要异步调用，但作为辅助函数，实际应在处理函数中实现
    return False

@group_config_cmd.handle()
async def handle_group_config(bot: Bot, event: Event):
    """处理群配置命令"""
    # 检查是否为群聊环境
    if not isinstance(event, GroupMessageEvent):
        await group_config_cmd.finish("❌ 只能在群聊中使用此命令")
        return
    
    # 检查用户权限
    qq_id = str(event.user_id)
    group_id = str(event.group_id)
    
    # 检查是否为超级用户
    if not is_superuser(qq_id):
        # 检查是否为群管理员（从数据库配置）
        group_config = database.get_group_config(group_id)
        admin_list = group_config.get("admin_list", "").split(",") if group_config.get("admin_list") else []
        
        if str(event.user_id) not in admin_list:
            # 检查是否为群主或群管理员（从QQ群权限）
            member_info = await bot.get_group_member_info(group_id=group_id, user_id=event.user_id)
            if member_info.get("role", "") not in ["owner", "admin"]:
                await group_config_cmd.finish("❌ 你没有权限执行此命令")
                return
    
    # 获取群配置
    config = database.get_group_config(group_id)
    
    # 格式化群配置信息
    config_text = (
        f"【群配置信息】\n" +
        f"群号：{group_id}\n" +
        f"\n" +
        f"🔧 功能开关\n" +
        f"服务器监控：{'✅ 开启' if config.get('enable_monitor', 1) else '❌ 关闭'}\n" +
        f"上线通知：{'✅ 开启' if config.get('notify_online', 1) else '❌ 关闭'}\n" +
        f"下线通知：{'✅ 开启' if config.get('notify_offline', 1) else '❌ 关闭'}\n" +
        f"自动批准入群：{'✅ 开启' if config.get('auto_approve', 0) else '❌ 关闭'}\n" +
        f"\n" +
        f"💬 欢迎消息\n" +
        f"{config.get('welcome_message', '未设置')}\n" +
        f"\n" +
        f"👥 群内管理员\n" +
        f"{config.get('admin_list', '无')}\n" +
        f"\n" +
        f"使用说明：\n" +
        f"1. 使用 /addadmin [QQ号] 添加群内管理员\n" +
        f"2. 使用 /removeadmin [QQ号] 移除群内管理员\n" +
        f"3. 高级配置请联系超级管理员"
    )
    
    # 记录命令日志
    database.log_command(
        qq_id=qq_id,
        group_id=group_id,
        command="groupconfig",
        success=True
    )
    
    await group_config_cmd.finish(config_text)

# 注册所有命令到nonebot
# 注意：nonebot会自动注册使用on_command等装饰器的命令

# 其他消息处理函数（可以根据需要添加）
# message_handler = on_message(priority=5, block=False)
# 
# @message_handler.handle()
# async def handle_message(event: Event):
#     """处理所有消息"""
#     # 这里可以添加消息处理逻辑
#     pass

# 通知事件处理函数
# notice_handler = on_notice(priority=5, block=False)
# 
# @notice_handler.handle()
# async def handle_notice(event: Event):
#     """处理通知事件"""
#     # 这里可以添加通知事件处理逻辑
#     pass

# 请求事件处理函数
# request_handler = on_request(priority=5, block=False)
# 
# @request_handler.handle()
# async def handle_request(event: Event):
#     """处理请求事件"""
#     # 这里可以添加请求事件处理逻辑
#     pass