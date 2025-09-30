from sqlalchemy import create_engine, Column, Integer, String, DateTime, Boolean, ForeignKey, Text, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship, backref
from .settings import get_config
import datetime
import logging

# 获取配置
config = get_config()

# 创建数据库引擎
engine = create_engine(
    config.database_url, 
    pool_pre_ping=True
)

# 创建会话工厂
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 创建基础模型类
Base = declarative_base()

# 数据库连接依赖
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# 初始化数据库
def init_db():
    try:
        # 导入所有模型以确保它们被Base识别
        from .models import (
            QQBotPlayers, PlayerStats, Uconomy, 
            ServerStatus, DailySignIn, GroupManagement, 
            CommandLogs, Announcements
        )
        
        # 创建所有表
        Base.metadata.create_all(bind=engine)
        
        logging.info("数据库初始化成功，所有表已创建")
        
        # 添加初始数据
        add_initial_data()
    except Exception as e:
        logging.error(f"数据库初始化失败: {str(e)}")
        raise

# 添加初始数据
def add_initial_data():
    db = next(get_db())
    try:
        # 检查是否已有超级用户
        from .models import QQBotPlayers
        if db.query(QQBotPlayers).count() == 0:
            # 如果有超级用户ID配置，添加超级用户
            if config.SUPERUSERS and len(config.SUPERUSERS) > 0:
                for superuser_id in config.SUPERUSERS:
                    superuser = QQBotPlayers(
                        qq_id=superuser_id,
                        nickname="超级管理员",
                        is_superuser=True
                    )
                    db.add(superuser)
                db.commit()
                logging.info(f"已添加超级用户: {', '.join(config.SUPERUSERS)}")
        
        # 检查是否已有群管理配置
        from .models import GroupManagement
        if db.query(GroupManagement).count() == 0:
            # 如果有监控群配置，添加群管理配置
            if hasattr(config, 'MONITOR_GROUPS') and config.MONITOR_GROUPS:
                for group_id in config.MONITOR_GROUPS:
                    group_config = GroupManagement(
                        group_id=group_id,
                        enable_monitor=True,
                        enable_commands=True
                    )
                    db.add(group_config)
                db.commit()
                logging.info(f"已添加监控群配置: {', '.join(map(str, config.MONITOR_GROUPS))}")
    except Exception as e:
        db.rollback()
        logging.error(f"添加初始数据失败: {str(e)}")
    finally:
        db.close()

# 数据库工具函数
def get_player_by_qq(qq_id):
    """根据QQ号获取玩家信息"""
    db = next(get_db())
    try:
        from .models import QQBotPlayers
        return db.query(QQBotPlayers).filter(QQBotPlayers.qq_id == qq_id).first()
    finally:
        db.close()

def log_command(user_id, command, args, success=True, error_msg=None):
    """记录命令执行日志"""
    db = next(get_db())
    try:
        from .models import CommandLogs
        log = CommandLogs(
            user_id=user_id,
            command=command,
            arguments=args,
            success=success,
            error_message=error_msg,
            timestamp=datetime.datetime.utcnow()
        )
        db.add(log)
        db.commit()
    except Exception as e:
        db.rollback()
        logging.error(f"记录命令日志失败: {str(e)}")
    finally:
        db.close()

def save_server_status(is_online, players=0, max_players=24, map_name="Unknown", ip="", port=27015):
    """保存服务器状态到数据库"""
    db = next(get_db())
    try:
        from .models import ServerStatus
        status = ServerStatus(
            is_online=is_online,
            players=players,
            max_players=max_players,
            map_name=map_name,
            server_ip=ip,
            server_port=port
        )
        db.add(status)
        db.commit()
        return status
    except Exception as e:
        db.rollback()
        logging.error(f"保存服务器状态失败: {str(e)}")
    finally:
        db.close()

def get_latest_server_status():
    """获取最新的服务器状态"""
    db = next(get_db())
    try:
        from .models import ServerStatus
        return db.query(ServerStatus).order_by(ServerStatus.timestamp.desc()).first()
    finally:
        db.close()