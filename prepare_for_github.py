#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GitHub上传准备脚本

此脚本用于在上传代码到GitHub之前，自动替换配置文件中的隐私数据为虚拟数据。
执行此脚本后，所有敏感信息将被替换为安全的示例数据。

使用方法：
python prepare_for_github.py
"""
import os
import json
import shutil
from pathlib import Path
from typing import Dict, List, Any

# 项目根目录
PROJECT_ROOT = Path(__file__).parent.resolve()

# 需要处理的配置文件
CONFIG_FILES = [
    PROJECT_ROOT / ".env.example",  # 示例配置文件，确保不包含真实数据
    PROJECT_ROOT / "settings.py",    # 设置文件，检查默认值
]

# 隐私数据替换规则
# 键为配置项名称，值为替换后的虚拟数据
PRIVACY_REPLACEMENTS = {
    # 超级用户配置
    "SUPERUSERS": '["1000000000"]',
    'superusers': '["1000000000"]',
    "SUPERUSERS=[\"1049217020\"]": "SUPERUSERS=[\"1000000000\"]",
    # 服务器配置
    "SERVER_IP": "127.0.0.1",
    "server_ip": "127.0.0.1",
    # 数据库配置
    "DATABASE_URL": "mysql+pymysql://root:password@localhost:3306/unturned_bot",
    "database_url": "mysql+pymysql://root:password@localhost:3306/unturned_bot",
}

# 需要确保安全的文件内容检查正则表达式
SAFETY_CHECKS = [
    # 检查是否包含真实的QQ号
    (r'SUPERUSERS=\["[0-9]{10}\"\]', r'SUPERUSERS=\["1000000000"\]'),
    # 检查是否包含非本地IP地址
    (r'SERVER_IP=([0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3})', r'SERVER_IP=127.0.0.1'),
    # 检查是否包含真实的数据库连接信息
    (r'DATABASE_URL=mysql\+pymysql:\/\/[^:@]+:[^@]+@[^:]+:\d+\/[^\\s]+', 
     r'DATABASE_URL=mysql+pymysql://root:password@localhost:3306/unturned_bot'),
]

def process_file(file_path: Path) -> bool:
    """处理单个配置文件，替换隐私数据"""
    if not file_path.exists():
        print(f"文件不存在: {file_path}")
        return False

    try:
        # 读取文件内容
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # 创建备份文件
        backup_path = file_path.with_suffix(f"{file_path.suffix}.backup")
        with open(backup_path, 'w', encoding='utf-8') as f:
            f.write(content)

        # 替换隐私数据
        modified = False
        for old_value, new_value in PRIVACY_REPLACEMENTS.items():
            if old_value in content:
                content = content.replace(old_value, new_value)
                modified = True

        # 执行安全检查并替换
        import re
        for pattern, replacement in SAFETY_CHECKS:
            if re.search(pattern, content):
                content = re.sub(pattern, replacement, content)
                modified = True

        # 写回文件
        if modified:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"已更新文件: {file_path}")
        else:
            print(f"文件无需更新: {file_path}")
            # 删除不必要的备份
            if backup_path.exists():
                os.remove(backup_path)

        return True
    except Exception as e:
        print(f"处理文件失败 {file_path}: {e}")
        # 如果出现错误，恢复备份
        if backup_path.exists():
            shutil.copy2(backup_path, file_path)
            os.remove(backup_path)
        return False

def check_gitignore() -> bool:
    """检查.gitignore文件是否正确配置"""
    gitignore_path = PROJECT_ROOT / ".gitignore"
    if not gitignore_path.exists():
        print("警告: .gitignore文件不存在！")
        return False

    with open(gitignore_path, 'r', encoding='utf-8') as f:
        content = f.read()

    required_rules = [
        ".env",          # 忽略实际配置文件
        "*.log",         # 忽略日志文件
        "__pycache__",   # 忽略编译缓存
        "*.pyc",         # 忽略编译后的Python文件
        "venv/",         # 忽略虚拟环境
        "*.sqlite",      # 忽略SQLite数据库文件
        "*.db",          # 忽略数据库文件
    ]

    missing_rules = []
    for rule in required_rules:
        if rule not in content:
            missing_rules.append(rule)

    if missing_rules:
        print(f"警告: .gitignore文件缺少以下必要规则:")
        for rule in missing_rules:
            print(f"  - {rule}")
        return False
    else:
        print(".gitignore文件配置正确")
        return True

def generate_command_documentation() -> bool:
    """生成插件指令文档"""
    try:
        # 直接定义指令信息（基于已知的commands.py内容）
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
                f.write("\n")
        
        print(f"已成功生成指令文档: {doc_path}")
        return True
    except Exception as e:
        print(f"生成指令文档失败: {str(e)}")
        return False

def main() -> None:
    """主函数"""
    print("=== GitHub上传准备脚本 ===")
    print(f"正在处理项目: {PROJECT_ROOT}")
    
    # 处理所有配置文件
    all_success = True
    for file_path in CONFIG_FILES:
        success = process_file(file_path)
        all_success = all_success and success
    
    # 检查.gitignore文件
    gitignore_ok = check_gitignore()
    all_success = all_success and gitignore_ok
    
    # 生成指令文档
    doc_success = generate_command_documentation()
    all_success = all_success and doc_success
    
    # 生成总结
    print("\n=== 总结 ===")
    if all_success:
        print("✅ 所有操作已成功完成！")
        print("\n接下来您可以执行以下命令上传代码到GitHub：")
        print("  git add .")
        print("  git commit -m \"准备上传GitHub，替换隐私数据\"")
        print("  git push origin main")
    else:
        print("⚠️ 部分操作执行失败，请查看上面的详细信息。")