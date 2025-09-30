from nonebot import on_command
from nonebot.adapters.onebot.v11 import Message, GroupMessageEvent, PrivateMessageEvent
from nonebot.params import CommandArg
from nonebot.permission import SUPERUSER
from nonebot.rule import to_me
from settings import get_config
from utils import logger, calculate_sign_in_reward, format_time
from database import get_db
from models import QQBotPlayers, PlayerStats, DailySignIn, GroupManagement
from core import process_command
import datetime
import re

# 获取配置
config = get_config()

# 定义命令
def register_commands():
    # 帮助命令
    if config.ENABLE_HELP_COMMAND:
        help_cmd = on_command("help", aliases={"帮助", "h"}, priority=5, block=True)
        
        @help_cmd.handle()
        async def handle_help(event, bot):
            async def help_handler(event, bot):
                # 构建帮助信息
                help_text = [
                    "📋 Unturned服务器助手命令列表：",
                    "",
                    "🎮 基础命令：",
                    f"{'✅' if config.ENABLE_BIND_COMMAND else '❌'} /bind <SteamID> - 绑定QQ与Steam账号",
                    f"{'✅' if config.ENABLE_SIGN_COMMAND else '❌'} /sign - 每日签到领取积分",
                    f"{'✅' if config.ENABLE_ME_COMMAND else '❌'} /me - 查看个人信息",
                    f"{'✅' if config.ENABLE_SERVER_COMMAND else '❌'} /server - 查看服务器状态",
                    "",
                    "🔧 管理员命令：",
                    f"{'✅' if config.ENABLE_BROADCAST_COMMAND else '❌'} /broadcast <消息> - 广播消息到所有监控群",
                    "",
                    f"版本: {config.VERSION}"
                ]
                
                await bot.send(event, "\n".join(help_text))
                return "显示帮助信息成功"
            
            await process_command(event, bot, "help", help_handler)
    
    # 绑定命令
    if config.ENABLE_BIND_COMMAND:
        bind_cmd = on_command("bind", priority=5, block=True)
        
        @bind_cmd.handle()
        async def handle_bind(event, bot, args: Message = CommandArg()):
            async def bind_handler(event, bot):
                # 获取参数
                steam_id = args.extract_plain_text().strip()
                
                if not steam_id:
                    await bot.send(event, "❌ 请输入SteamID，格式：/bind <SteamID>")
                    return "绑定失败：未提供SteamID"
                
                # 简单验证SteamID格式
                if not re.match(r'^\d{17}$', steam_id):
                    await bot.send(event, "❌ SteamID格式不正确，请输入17位数字的SteamID")
                    return "绑定失败：SteamID格式不正确"
                
                user_id = event.user_id
                
                # 检查数据库
                db = next(get_db())
                try:
                    # 检查是否已绑定
                    existing_user = db.query(QQBotPlayers).filter(
                        QQBotPlayers.qq_id == str(user_id)
                    ).first()
                    
                    if existing_user:
                        # 更新绑定
                        existing_user.steam_id = steam_id
                        existing_user.last_login = datetime.datetime.utcnow()
                        db.commit()
                        await bot.send(event, f"✅ 账号绑定已更新！\nQQ: {user_id}\nSteamID: {steam_id}")
                        return f"更新绑定成功：QQ={user_id}, SteamID={steam_id}"
                    else:
                        # 创建新绑定
                        new_player = QQBotPlayers(
                            qq_id=str(user_id),
                            steam_id=steam_id,
                            nickname=f"玩家{user_id[:4]}"
                        )
                        db.add(new_player)
                        db.flush()  # 获取新创建的ID
                        
                        # 创建相关记录
                        player_stats = PlayerStats(player_id=new_player.id)
                        daily_signin = DailySignIn(player_id=new_player.id)
                        db.add_all([player_stats, daily_signin])
                        db.commit()
                        
                        await bot.send(event, f"✅ 账号绑定成功！\nQQ: {user_id}\nSteamID: {steam_id}")
                        return f"绑定成功：QQ={user_id}, SteamID={steam_id}"
                except Exception as e:
                    db.rollback()
                    raise e
                finally:
                    db.close()
            
            await process_command(event, bot, "bind", bind_handler)
    
    # 签到命令
    if config.ENABLE_SIGN_COMMAND:
        sign_cmd = on_command("sign", aliases={"签到"}, priority=5, block=True)
        
        @sign_cmd.handle()
        async def handle_sign(event, bot):
            async def sign_handler(event, bot):
                user_id = event.user_id
                
                # 检查数据库
                db = next(get_db())
                try:
                    # 查询用户
                    player = db.query(QQBotPlayers).filter(
                        QQBotPlayers.qq_id == str(user_id)
                    ).first()
                    
                    if not player:
                        await bot.send(event, "❌ 您还未绑定账号，请先使用 /bind 命令绑定")
                        return "签到失败：用户未绑定"
                    
                    # 查询签到记录
                    signin_record = db.query(DailySignIn).filter(
                        DailySignIn.player_id == player.id
                    ).first()
                    
                    if not signin_record:
                        signin_record = DailySignIn(player_id=player.id)
                        db.add(signin_record)
                    
                    # 检查是否今天已签到
                    today = datetime.date.today()
                    if signin_record.last_signin and \
                       signin_record.last_signin.date() == today:
                        await bot.send(event, "❌ 您今天已经签到过了，明天再来吧~")
                        return "签到失败：今日已签到"
                    
                    # 更新签到记录
                    yesterday = today - datetime.timedelta(days=1)
                    if signin_record.last_signin and \
                       signin_record.last_signin.date() == yesterday:
                        # 连续签到
                        signin_record.consecutive_days += 1
                    else:
                        # 重置连续签到天数
                        signin_record.consecutive_days = 1
                    
                    # 更新签到时间和总天数
                    signin_record.last_signin = datetime.datetime.utcnow()
                    signin_record.total_days += 1
                    
                    # 计算奖励
                    reward = calculate_sign_in_reward(signin_record.consecutive_days)
                    player.points += reward
                    
                    # 更新最后签到日期
                    player.last_checkin_date = today.strftime("%Y-%m-%d")
                    
                    db.commit()
                    
                    # 发送签到成功消息
                    message = [
                        f"✅ {player.nickname} 签到成功！",
                        f"今日获得: {reward} 积分",
                        f"当前积分: {player.points}",
                        f"连续签到: {signin_record.consecutive_days} 天",
                        f"累计签到: {signin_record.total_days} 天"
                    ]
                    
                    # 如果是连续7天或30天，添加额外提示
                    if signin_record.consecutive_days % 30 == 0:
                        message.append("🎉 恭喜达成连续签到30天成就！获得额外奖励！")
                    elif signin_record.consecutive_days % 7 == 0:
                        message.append("🎉 恭喜达成连续签到7天成就！获得额外奖励！")
                    
                    await bot.send(event, "\n".join(message))
                    return f"签到成功：获得{reward}积分，连续{signin_record.consecutive_days}天"
                except Exception as e:
                    db.rollback()
                    raise e
                finally:
                    db.close()
            
            await process_command(event, bot, "sign", sign_handler)
    
    # 个人信息命令
    if config.ENABLE_ME_COMMAND:
        me_cmd = on_command("me", aliases={"我的信息"}, priority=5, block=True)
        
        @me_cmd.handle()
        async def handle_me(event, bot):
            async def me_handler(event, bot):
                user_id = event.user_id
                
                # 检查数据库
                db = next(get_db())
                try:
                    # 查询用户
                    player = db.query(QQBotPlayers).filter(
                        QQBotPlayers.qq_id == str(user_id)
                    ).first()
                    
                    if not player:
                        await bot.send(event, "❌ 您还未绑定账号，请先使用 /bind 命令绑定")
                        return "查看信息失败：用户未绑定"
                    
                    # 查询相关记录
                    player_stats = db.query(PlayerStats).filter(
                        PlayerStats.player_id == player.id
                    ).first()
                    
                    signin_record = db.query(DailySignIn).filter(
                        DailySignIn.player_id == player.id
                    ).first()
                    
                    # 构建个人信息
                    info = [
                        f"👤 {player.nickname} 的个人信息",
                        f"QQ: {player.qq_id}",
                        f"SteamID: {player.steam_id}",
                        f"积分: {player.points}",
                        f"绑定时间: {format_time(player.bind_time)}",
                        f"最近登录: {format_time(player.last_login)}"
                    ]
                    
                    # 添加统计信息
                    if player_stats:
                        info.extend([
                            "",
                            "🎮 游戏统计：",
                            f"游戏时长: {player_stats.play_time:.2f} 小时",
                            f"击杀玩家: {player_stats.kills} 人",
                            f"死亡次数: {player_stats.deaths} 次",
                            f"击杀僵尸: {player_stats.zombies_killed} 只"
                        ])
                    
                    # 添加签到信息
                    if signin_record:
                        info.extend([
                            "",
                            "📅 签到信息：",
                            f"连续签到: {signin_record.consecutive_days} 天",
                            f"累计签到: {signin_record.total_days} 天",
                            f"最后签到: {format_time(signin_record.last_signin) if signin_record.last_signin else '从未签到'}"
                        ])
                    
                    await bot.send(event, "\n".join(info))
                    return "查看个人信息成功"
                except Exception as e:
                    db.rollback()
                    raise e
                finally:
                    db.close()
            
            await process_command(event, bot, "me", me_handler)
    
    # 服务器状态命令
    if config.ENABLE_SERVER_COMMAND:
        server_cmd = on_command("server", aliases={"服务器状态"}, priority=5, block=True)
        
        @server_cmd.handle()
        async def handle_server(event, bot):
            async def server_handler(event, bot):
                from monitor import get_server_status
                
                status = get_server_status()
                
                if status["is_online"]:
                    # 在线状态
                    message = [
                        "🟢 服务器状态：在线",
                        f"服务器地址: {config.SERVER_IP}:{config.SERVER_PORT}",
                        f"当前玩家: {status['players']}/{status['max_players']}",
                        f"当前地图: {status['map']}"
                    ]
                    
                    if status['players_list']:
                        message.append(f"在线玩家: {', '.join(status['players_list'])}")
                else:
                    # 离线状态
                    message = [
                        "🔴 服务器状态：离线",
                        f"服务器地址: {config.SERVER_IP}:{config.SERVER_PORT}",
                        "服务器当前不可用，请稍后再试"
                    ]
                
                await bot.send(event, "\n".join(message))
                return f"查询服务器状态：{'在线' if status['is_online'] else '离线'}"
            
            await process_command(event, bot, "server", server_handler)
    
    # 广播命令（管理员）
    if config.ENABLE_BROADCAST_COMMAND:
        broadcast_cmd = on_command("broadcast", aliases={"广播"}, priority=5, block=True, permission=SUPERUSER)
        
        @broadcast_cmd.handle()
        async def handle_broadcast(event, bot, args: Message = CommandArg()):
            async def broadcast_handler(event, bot):
                # 获取广播内容
                content = args.extract_plain_text().strip()
                
                if not content:
                    await bot.send(event, "❌ 请输入广播内容，格式：/broadcast <消息>")
                    return "广播失败：未提供内容"
                
                # 发送广播到所有监控群
                success_count = 0
                fail_count = 0
                
                from utils import send_onebot_message
                
                for group_id in config.MONITOR_GROUPS:
                    # 构建广播消息
                    broadcast_msg = f"📢 系统广播\n{content}\n\n-- 管理员 {event.user_id} 发送"
                    
                    # 发送消息
                    if await bot.send_group_msg(group_id=int(group_id), message=broadcast_msg):
                        success_count += 1
                    else:
                        fail_count += 1
                
                # 反馈结果
                result_msg = f"✅ 广播完成\n成功: {success_count} 个群\n失败: {fail_count} 个群"
                await bot.send(event, result_msg)
                return result_msg
            
            await process_command(event, bot, "broadcast", broadcast_handler, is_admin_only=True)

# 注册所有命令
register_commands()