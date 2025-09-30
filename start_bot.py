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

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("unturned_bot.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("unturned_bot")

# 加载环境变量
try:
    from dotenv import load_dotenv
    dotenv_path = current_dir / ".env"
    load_dotenv(dotenv_path=dotenv_path)
    logger.info(f"成功加载.env文件: {dotenv_path}")
except ImportError:
    logger.warning("未找到python-dotenv模块，跳过.env文件加载")
except Exception as e:
    logger.error(f"加载.env文件失败: {e}")

# 检查依赖
required_packages = ["nonebot2", "nonebot-adapter-onebot", "sqlalchemy", "fastapi", "uvicorn"]
missing_packages = []
for package in required_packages:
    try:
        __import__(package)
    except ImportError:
        missing_packages.append(package)

if missing_packages:
    logger.error(f"缺少必要的依赖包: {', '.join(missing_packages)}")
    logger.error("请运行: pip install -r requirements.txt")
    sys.exit(1)

# 启动NoneBot2
try:
    import nonebot
    from nonebot.adapters.onebot.v11 import Adapter as OneBotV11Adapter
    
    # 初始化NoneBot
    nonebot.init()
    
    # 注册适配器
    driver = nonebot.get_driver()
    driver.register_adapter(OneBotV11Adapter)
    
    # 加载当前目录下的所有插件
    nonebot.load_plugins(str(current_dir))
    
    # 启动API服务
    try:
        import uvicorn
        from api import app as api_app
        from config import config
        
        if config.API_ENABLED:
            logger.info(f"启动API服务: {config.API_HOST}:{config.API_PORT}")
            # 在单独的线程中启动API服务
            import threading
            api_thread = threading.Thread(
                target=lambda: uvicorn.run(
                    api_app, 
                    host=config.API_HOST, 
                    port=config.API_PORT, 
                    log_level="info" if config.API_DEBUG else "warning"
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