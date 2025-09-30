#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GitHub上传前准备检查脚本
"""
import os
import re
from pathlib import Path

# 项目根目录
PROJECT_ROOT = Path(__file__).parent.resolve()

print("=== GitHub上传前准备检查 ===")

# 1. 检查.env.example文件
print("\n1. 检查.env.example文件...")
env_example_path = PROJECT_ROOT / ".env.example"
if not env_example_path.exists():
    print("❌ .env.example文件不存在！")
else:
    with open(env_example_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 检查是否包含虚拟数据
    virtual_data_checks = [
        ('SUPERUSERS=\["1000000000"\]', "超级用户配置"),
        ('SERVER_IP=127.0.0.1', "服务器IP配置"),
        ('DATABASE_URL=mysql\+pymysql:\/\/root:password@localhost:3306/unturned_bot', "数据库配置"),
        ('API_KEY=your-api-key-here', "API密钥配置"),
        ('MONITOR_GROUPS=\["123456789"\]', "监控群配置"),
    ]
    
    all_ok = True
    for pattern, desc in virtual_data_checks:
        if re.search(pattern, content):
            print(f"✅ {desc} 已替换为虚拟数据")
        else:
            print(f"❌ {desc} 可能包含真实数据")
            all_ok = False
    
    if all_ok:
        print("✅ .env.example文件检查通过")

# 2. 检查.gitignore文件
print("\n2. 检查.gitignore文件...")
gitignore_path = PROJECT_ROOT / ".gitignore"
if not gitignore_path.exists():
    print("❌ .gitignore文件不存在！")
else:
    with open(gitignore_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 必须包含的忽略规则
    required_rules = [
        ".env",                  # 环境文件
        "__pycache__/",          # Python缓存
        "*.pyc",                 # 编译后的Python文件
        "venv/", "env/",         # 虚拟环境
        "*.log",                 # 日志文件
        "*.db", "*.sqlite",      # 数据库文件
    ]
    
    all_present = True
    for rule in required_rules:
        if rule not in content:
            print(f"⚠️ 缺少必要忽略规则: {rule}")
            all_present = False
    
    if all_present:
        print("✅ .gitignore文件检查通过")

# 3. 检查COMMANDS.md文件
print("\n3. 检查COMMANDS.md文件...")
commands_path = PROJECT_ROOT / "COMMANDS.md"
if not commands_path.exists():
    print("❌ COMMANDS.md文件不存在！")
else:
    # 检查是否包含我们新增的命令
    new_commands = [
        'bind_server', 'unbind_server', 'list_servers', 
        'players', 'admin', 'ping', 'help', 
        'signin', 'rank', 'api_status', 
        'set_permission', 'get_permission'
    ]
    
    with open(commands_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    all_present = True
    for cmd in new_commands:
        if cmd not in content:
            print(f"⚠️ 缺少命令文档: {cmd}")
            all_present = False
    
    if all_present:
        print("✅ COMMANDS.md文件已包含所有命令文档")

print("\n=== 检查完成 ===")
print("\n如果所有检查都通过，您可以执行以下命令上传代码到GitHub：")
print("  git add .")
print("  git commit -m \"准备上传GitHub，替换隐私数据\"\n")
print("  git push origin main")