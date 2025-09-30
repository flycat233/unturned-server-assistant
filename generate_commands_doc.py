#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
生成命令文档脚本
"""
import os
from pathlib import Path

# 项目根目录
PROJECT_ROOT = Path(__file__).parent.resolve()

print("=== 生成命令文档 ===")

def generate_command_documentation() -> bool:
    """生成插件指令文档"""
    try:
        # 定义所有支持的指令
        commands = [
            {
                'name': 'echo',
                'description': '重复用户发送的内容',
                'detail': '用于测试机器人是否正常响应，会原样返回用户发送的消息',
                'aliases': [],
                'superuser_only': False
            },
            {
                'name': 'server',
                'description': '查询Unturned服务器状态',
                'detail': '显示服务器的当前运行状态、在线人数和地图信息',
                'aliases': ['服务器状态'],
                'superuser_only': False
            },
            {
                'name': 'restart',
                'description': '重启机器人',
                'detail': '用于重新启动机器人，只有超级用户可以执行此命令',
                'aliases': ['重启'],
                'superuser_only': True
            },
            {
                'name': 'bind_server',
                'description': '绑定Unturned服务器',
                'detail': '将当前群聊绑定到指定的Unturned服务器，用于接收该服务器的通知',
                'aliases': ['绑定服务器'],
                'superuser_only': True
            },
            {
                'name': 'unbind_server',
                'description': '解绑Unturned服务器',
                'detail': '取消当前群聊与Unturned服务器的绑定关系',
                'aliases': ['解绑服务器'],
                'superuser_only': True
            },
            {
                'name': 'list_servers',
                'description': '列出已绑定的服务器',
                'detail': '显示当前群聊已绑定的所有Unturned服务器列表',
                'aliases': ['服务器列表'],
                'superuser_only': False
            },
            {
                'name': 'players',
                'description': '查看在线玩家列表',
                'detail': '显示服务器当前在线玩家的昵称、ID和游戏时长',
                'aliases': ['在线玩家', '玩家列表'],
                'superuser_only': False
            },
            {
                'name': 'admin',
                'description': '管理员操作',
                'detail': '执行服务器管理员命令，如踢出玩家、封禁玩家等',
                'aliases': ['管理员命令'],
                'superuser_only': True
            },
            {
                'name': 'ping',
                'description': '检查服务器延迟',
                'detail': '测试与Unturned服务器的网络连接延迟',
                'aliases': ['延迟测试'],
                'superuser_only': False
            },
            {
                'name': 'help',
                'description': '查看帮助信息',
                'detail': '显示机器人支持的所有命令及其简要说明',
                'aliases': ['帮助'],
                'superuser_only': False
            },
            {
                'name': 'signin',
                'description': '每日签到',
                'detail': '玩家每日签到可获得游戏内奖励',
                'aliases': ['签到'],
                'superuser_only': False
            },
            {
                'name': 'rank',
                'description': '查看玩家排名',
                'detail': '显示玩家签到排名或游戏时长排名',
                'aliases': ['排行榜', '排名'],
                'superuser_only': False
            },
            {
                'name': 'api_status',
                'description': '查看API服务状态',
                'detail': '显示机器人API服务的运行状态和连接信息',
                'aliases': ['API状态'],
                'superuser_only': True
            },
            {
                'name': 'set_permission',
                'description': '设置用户权限',
                'detail': '设置指定用户的权限等级，用于控制命令访问权限',
                'aliases': ['设置权限', '权限设置'],
                'superuser_only': True
            },
            {
                'name': 'get_permission',
                'description': '查看用户权限',
                'detail': '查看指定用户的当前权限等级',
                'aliases': ['查看权限', '权限查询'],
                'superuser_only': True
            }
        ]
        
        # 生成Markdown文档
        doc_path = PROJECT_ROOT / "COMMANDS.md"
        with open(doc_path, 'w', encoding='utf-8') as f:
            f.write("# Unturned助手插件指令文档\n\n")
            f.write("本文档列出了Unturned助手插件支持的所有指令及其用法。\n\n")
            
            # 生成指令列表表格
            f.write("## 指令列表\n\n")
            f.write("| 指令名称 | 描述 | 别名 | 权限要求 |\n")
            f.write("|---------|------|------|---------|\n")
            
            for cmd in commands:
                aliases_text = ", ".join(cmd['aliases']) if cmd['aliases'] else "无"
                permission_text = "超级用户" if cmd['superuser_only'] else "所有人"
                
                f.write(f"| {cmd['name']} | {cmd['description']} | {aliases_text} | {permission_text} |\n")
            
            # 添加详细说明
            f.write("\n## 详细说明\n\n")
            for cmd in commands:
                f.write(f"### {cmd['name']}\n")
                f.write(f"**描述**: {cmd['description']}\n")
                f.write(f"**详细说明**: {cmd['detail']}\n")
                if cmd['aliases']:
                    f.write(f"**别名**: {', '.join(cmd['aliases'])}\n")
                f.write(f"**权限要求**: {'超级用户' if cmd['superuser_only'] else '所有人'}\n")
                f.write("\n")
                
                # 添加使用示例
                f.write("**使用示例**:\n")
                if cmd['name'] == 'echo':
                    f.write("- `/echo 你好` - 机器人会回复：你说的是：你好\n")
                elif cmd['name'] == 'server':
                    f.write("- `/server` 或 `/服务器状态` - 查看服务器当前状态\n")
                elif cmd['name'] == 'restart':
                    f.write("- `/restart` 或 `/重启` - 重启机器人（仅超级用户可用）\n")
                elif cmd['name'] == 'bind_server':
                    f.write("- `/bind_server 127.0.0.1:27015` - 将当前群聊绑定到指定服务器\n")
                elif cmd['name'] == 'unbind_server':
                    f.write("- `/unbind_server 127.0.0.1:27015` - 取消当前群聊与指定服务器的绑定\n")
                elif cmd['name'] == 'list_servers':
                    f.write("- `/list_servers` 或 `/服务器列表` - 查看当前群聊绑定的所有服务器\n")
                elif cmd['name'] == 'players':
                    f.write("- `/players` 或 `/在线玩家` - 查看当前在线玩家列表\n")
                elif cmd['name'] == 'admin':
                    f.write("- `/admin kick PlayerName` - 踢出指定玩家\n")
                    f.write("- `/admin ban PlayerName 永久` - 封禁指定玩家\n")
                elif cmd['name'] == 'ping':
                    f.write("- `/ping` - 测试与服务器的连接延迟\n")
                elif cmd['name'] == 'help':
                    f.write("- `/help` 或 `/帮助` - 显示帮助信息\n")
                    f.write("- `/help server` - 查看特定命令的详细说明\n")
                elif cmd['name'] == 'signin':
                    f.write("- `/signin` 或 `/签到` - 每日签到获取奖励\n")
                elif cmd['name'] == 'rank':
                    f.write("- `/rank` - 查看签到排行榜\n")
                    f.write("- `/rank time` - 查看游戏时长排行榜\n")
                elif cmd['name'] == 'api_status':
                    f.write("- `/api_status` 或 `/API状态` - 查看API服务运行状态\n")
                elif cmd['name'] == 'set_permission':
                    f.write("- `/set_permission 123456789 2` - 设置用户ID为123456789的权限等级为2\n")
                elif cmd['name'] == 'get_permission':
                    f.write("- `/get_permission 123456789` - 查看用户ID为123456789的权限等级\n")
                f.write("\n")
            
            # 添加全局注意事项
            f.write("\n## 全局注意事项\n")
            f.write("- 所有指令都需要以配置的命令前缀开头（默认为 `/`、`!`、`！`）\n")
            f.write("- 部分指令需要特定权限才能使用（如`restart`指令仅限超级用户使用）\n")
            f.write("- 如果机器人没有响应，请检查命令格式是否正确，以及机器人是否在线\n")
            f.write("- 命令的具体功能可能会根据插件版本更新而有所变化\n")
        
        print(f"✅ 已成功生成指令文档: {doc_path}")
        return True
    except Exception as e:
        print(f"❌ 生成指令文档失败: {str(e)}")
        return False

if __name__ == "__main__":
    generate_command_documentation()