#!/usr/bin/env python3
"""
Unturned服务器助手机器人启动脚本
使用方法：python start_bot.py
"""
import os
import sys
import logging
from pathlib import Path

# 确保正确的工作目录
current_dir = Path(__file__).parent.resolve()
if not (current_dir / "__init__.py").is_file():
    print("错误：请在插件目录下运行此脚本")
    sys.exit(1)

# 添加当前目录到Python路径
sys.path.insert(0, str(current_dir))

# 首先导入统一配置模块
try:
    from settings import get_config, check_dependencies
    
    # 检查依赖
    missing_packages = check_dependencies()
    if missing_packages:
        print(f"错误：缺少必要的依赖包: {', '.join(missing_packages)}")
        print("请运行: pip install -r requirements.txt")
        sys.exit(1)
    
    # 获取配置
    config = get_config()
    logger = logging.getLogger("unturned_bot")
    logger.info(f"成功加载配置，超级用户: {config.superusers}, 类型: {type(config.superusers)}")
    
    # 创建用于NoneBot初始化的配置副本，确保不修改原始配置
    nonebot_config = config.dict().copy()
    
except Exception as e:
    print(f"加载配置失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# 启动NoneBot2
try:
    import nonebot
    from nonebot.adapters.onebot.v11 import Adapter as OneBotV11Adapter
    
    # 初始化NoneBot - 全新解决方案：不使用set类型，而是通过NoneBot的自定义配置方式
    # 移除原来的superusers配置，使用特殊方式处理
    if 'superusers' in nonebot_config:
        del nonebot_config['superusers']
    
    # 初始化NoneBot，但不包含superusers配置
    nonebot.init(config=nonebot_config)
    
    # 注册适配器
    driver = nonebot.get_driver()
    driver.register_adapter(OneBotV11Adapter)
    
    # 单独设置superusers - 通过driver设置，这样可以避免类型验证问题
    # 将superusers转换为字符串列表，这样NoneBot内部会正确处理
    driver.config.superusers = [str(user_id) for user_id in config.superusers]
    
    # 加载当前目录下的所有插件
    nonebot.load_plugins(str(current_dir))
    
    # 启动API服务（如果启用）
    try:
        if config.api_enabled:
            logger.info(f"启动API服务: {config.api_host}:{config.api_port}")
            # 在单独的线程中启动API服务
            import threading
            import uvicorn
            from api import app as api_app
            
            api_thread = threading.Thread(
                target=lambda: uvicorn.run(
                    api_app, 
                    host=config.api_host, 
                    port=config.api_port, 
                    log_level="info" if config.api_debug else "warning"
                ),
                daemon=True
            )
            api_thread.start()
        else:
            logger.info("API服务已禁用")
    except Exception as e:
        logger.error(f"启动API服务失败: {e}")
    
    # 运行NoneBot
    logger.info("Unturned服务器助手机器人启动中...")
    nonebot.run()
except KeyboardInterrupt:
    logger.info("收到中断信号，正在关闭机器人...")
except Exception as e:
    logger.error(f"机器人启动失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)