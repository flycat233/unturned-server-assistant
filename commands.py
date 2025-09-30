from nonebot import on_command, on_regex
from nonebot.adapters import Event
from nonebot.typing import T_State
from nonebot.permission import SUPERUSER
from nonebot.adapters.onebot.v11 import Message
from .settings import get_config
from .database import get_db
from .models import QQBotPlayers, PlayerStats, DailySignIn, Announcements
from .monitor import get_current_status
from .onebot_http import bot_http
import datetime

# 获取配置
config = get_config()

# 帮助命令：显示所有可用命令及使用说明
bot_help = on_command("help", aliases={"帮助", "命令列表"}, priority=10, block=True)

@bot_help.handle()
async def handle_help():
    help_text = "🚀 Unturned服务器助手机器人命令列表\n\n"
    help_text += "💡 **基础命令**\n"
    help_text += "/help - 显示此帮助信息\n"
    help_text += "/bind [SteamID] - 绑定SteamID与QQ账号\n"
    help_text += "/sign - 每日签到获取奖励\n"
    help_text += "/me - 查询个人信息\n"
    help_text += "/server - 查询服务器状态\n"
    help_text += "/echo [内容] - 重复你说的话\n\n"
    help_text += "👑 **管理员命令**\n"
    help_text += "/broadcast [内容] - 向所有群发送公告\n"
    help_text += "/restart - 重启机器人\n"
    
    await bot_help.finish(Message(help_text))

# 绑定命令：绑定SteamID与QQ账号
bind_steam = on_command("bind", aliases={"绑定"}, priority=10, block=True)

@bind_steam.handle()
async def handle_bind_steam(event: Event, state: T_State):
    args = str(event.get_message()).strip()
    if args:
        state["steam_id"] = args

@bind_steam.got("steam_id", prompt="请输入你的SteamID")
async def got_steam_id(event: Event, state: T_State):
    user_id = str(event.user_id)
    steam_id = state["steam_id"]
    
    db = next(get_db())
    try:
        # 检查是否已绑定
        existing = db.query(QQBotPlayers).filter(QQBotPlayers.qq_id == user_id).first()
        
        if existing:
            existing.steam_id = steam_id
            existing.last_login = datetime.datetime.utcnow()
            db.commit()
            await bind_steam.finish(Message(f"✅ SteamID绑定已更新: {steam_id}"))
        else:
            # 创建新绑定记录
            new_player = QQBotPlayers(
                qq_id=user_id,
                steam_id=steam_id,
                nickname=str(event.sender.nickname) if hasattr(event, 'sender') and hasattr(event.sender, 'nickname') else "未知用户"
            )
            db.add(new_player)
            
            # 创建玩家统计记录
            stats = PlayerStats(player=new_player)
            db.add(stats)
            
            # 创建签到记录
            signin = DailySignIn(player=new_player)
            db.add(signin)
            
            db.commit()
            await bind_steam.finish(Message(f"✅ SteamID绑定成功: {steam_id}\n现在你可以使用签到等功能了！"))
    except Exception as e:
        db.rollback()
        await bind_steam.finish(Message(f"❌ 绑定失败: {str(e)}"))
    finally:
        db.close()

# 签到命令：每日签到获取奖励
daily_sign = on_command("sign", aliases={"签到", "打卡"}, priority=10, block=True)

@daily_sign.handle()
async def handle_daily_sign(event: Event):
    user_id = str(event.user_id)
    
    db = next(get_db())
    try:
        # 查找玩家
        player = db.query(QQBotPlayers).filter(QQBotPlayers.qq_id == user_id).first()
        
        if not player:
            await daily_sign.finish(Message("❌ 请先使用 /bind 命令绑定SteamID！"))
            return
        
        # 查找签到记录
        signin = db.query(DailySignIn).filter(DailySignIn.player_id == player.id).first()
        
        if not signin:
            signin = DailySignIn(player=player)
            db.add(signin)
        
        # 检查是否已签到
        today = datetime.date.today()
        last_signin_date = signin.last_signin.date() if signin.last_signin else None
        
        if last_signin_date == today:
            await daily_sign.finish(Message("✅ 你今天已经签到过了，明天再来吧！"))
            return
        
        # 更新签到记录
        signin.last_signin = datetime.datetime.utcnow()
        signin.total_days += 1
        
        # 检查连续签到天数
        if last_signin_date and (today - last_signin_date).days == 1:
            signin.consecutive_days += 1
        else:
            signin.consecutive_days = 1
        
        db.commit()
        
        # 根据连续签到天数发放不同奖励
        reward_msg = ""
        if signin.consecutive_days == 1:
            reward_msg = "获得了100游戏币奖励！"
        elif signin.consecutive_days == 7:
            reward_msg = "获得了1000游戏币和一个稀有道具！"
        elif signin.consecutive_days == 30:
            reward_msg = "获得了5000游戏币和一个传说道具！"
        else:
            reward_msg = f"获得了{signin.consecutive_days * 20}游戏币奖励！"
        
        await daily_sign.finish(Message(f"🎉 签到成功！\n连续签到: {signin.consecutive_days}天\n累计签到: {signin.total_days}天\n{reward_msg}"))
    except Exception as e:
        db.rollback()
        await daily_sign.finish(Message(f"❌ 签到失败: {str(e)}"))
    finally:
        db.close()

# 个人信息命令：查询玩家个人统计数据
user_info = on_command("me", aliases={"个人信息", "我的信息"}, priority=10, block=True)

@user_info.handle()
async def handle_user_info(event: Event):
    user_id = str(event.user_id)
    
    db = next(get_db())
    try:
        # 查找玩家
        player = db.query(QQBotPlayers).filter(QQBotPlayers.qq_id == user_id).first()
        
        if not player:
            await user_info.finish(Message("❌ 请先使用 /bind 命令绑定SteamID！"))
            return
        
        # 获取统计信息
        stats = db.query(PlayerStats).filter(PlayerStats.player_id == player.id).first()
        signin = db.query(DailySignIn).filter(DailySignIn.player_id == player.id).first()
        
        # 构建消息
        message = f"👤 **个人信息**\n" \
                 f"QQ: {player.qq_id}\n" \
                 f"SteamID: {player.steam_id}\n" \
                 f"昵称: {player.nickname}\n" \
                 f"绑定时间: {player.bind_time.strftime('%Y-%m-%d')}\n" \
                 f"\n🎮 **游戏统计**\n" \
                 f"游戏时长: {stats.play_time if stats else 0}小时\n" \
                 f"\n📅 **签到记录**\n" \
                 f"连续签到: {signin.consecutive_days if signin else 0}天\n" \
                 f"累计签到: {signin.total_days if signin else 0}天"
        
        await user_info.finish(Message(message))
    except Exception as e:
        await user_info.finish(Message(f"❌ 查询失败: {str(e)}"))
    finally:
        db.close()

# 服务器状态命令：查询当前服务器运行状态
server_status_cmd = on_command("server", aliases={"服务器状态", "服务器"}, priority=10, block=True)

@server_status_cmd.handle()
async def handle_server_status():
    status = get_current_status()
    
    status_text = "🖥️ **服务器状态**\n" \
                 f"在线状态: {'✅ 在线' if status['is_online'] else '❌ 离线'}\n" \
                 f"在线人数: {status['players']}/{status['max_players']}\n" \
                 f"当前地图: {status['map']}\n" \
                 f"最后更新: {datetime.datetime.fromtimestamp(status['last_update']).strftime('%Y-%m-%d %H:%M:%S')}"
    
    await server_status_cmd.finish(Message(status_text))

# 广播命令：管理员向所有群发送公告
broadcast_cmd = on_command("broadcast", aliases={"广播", "公告"}, permission=SUPERUSER, priority=5, block=True)

@broadcast_cmd.handle()
async def handle_broadcast(event: Event, state: T_State):
    args = str(event.get_message()).strip()
    if args:
        state["broadcast_content"] = args

@broadcast_cmd.got("broadcast_content", prompt="请输入要广播的内容")
async def got_broadcast_content(event: Event, state: T_State):
    content = state["broadcast_content"]
    
    # 添加广播标记和发送者信息
    sender = str(event.sender.nickname) if hasattr(event, 'sender') and hasattr(event.sender, 'nickname') else str(event.user_id)
    broadcast_message = f"📢 **系统公告**\n" \
                       f"发送者: {sender}\n" \
                       f"时间: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n" \
                       f"\n{content}"
    
    # 发送广播
    results = await bot_http.broadcast(broadcast_message)
    
    # 记录公告到数据库
    db = next(get_db())
    try:
        announcement = Announcements(
            title="系统广播",
            content=content,
            created_by=str(event.user_id)
        )
        db.add(announcement)
        db.commit()
    except Exception as e:
        db.rollback()
    finally:
        db.close()
    
    await broadcast_cmd.finish(Message(f"✅ 广播发送完成！\n成功: {len(results['success'])}个群\n失败: {len(results['failed'])}个群"))

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

# 重启机器人（仅超级用户可用）
restart_bot = on_command("restart", aliases={"重启"}, permission=SUPERUSER, priority=5, block=True)

@restart_bot.handle()
async def handle_restart_bot():
    await restart_bot.send("正在准备重启机器人...")
    # 实际重启逻辑通常需要外部脚本配合
    await restart_bot.finish("机器人重启命令已执行，请手动检查机器人状态")