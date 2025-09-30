from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from settings import get_config

# 获取配置
config = get_config()

# 创建数据库引擎
engine = create_engine(
    config.DATABASE_URL,
    pool_size=config.DB_POOL_SIZE,
    max_overflow=10,
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

# 初始化数据库（创建表和初始数据）
def init_db():
    # 导入所有模型以确保它们被注册
    from models import (
        QQBotPlayers, PlayerStats, Uconomy, ServerStatus,
        DailySignIn, GroupManagement, CommandLogs, Announcements
    )
    
    # 创建所有表
    Base.metadata.create_all(bind=engine)
    
    # 添加初始数据
    db = next(get_db())
    
    # 检查是否已有超级用户
    for superuser_id in config.SUPERUSERS:
        existing_user = db.query(QQBotPlayers).filter(
            QQBotPlayers.qq_id == superuser_id
        ).first()
        
        if not existing_user:
            # 创建超级用户记录
            superuser = QQBotPlayers(
                qq_id=superuser_id,
                steam_id=f"superuser_{superuser_id}",
                nickname="超级用户",
                points=99999
            )
            db.add(superuser)
    
    # 添加监控群配置
    for group_id in config.MONITOR_GROUPS:
        existing_group = db.query(GroupManagement).filter(
            GroupManagement.group_id == group_id
        ).first()
        
        if not existing_group:
            # 创建群配置记录
            group_config = GroupManagement(
                group_id=group_id,
                enabled=True,
                admin_only=False,
                welcome_message="欢迎加入Unturned服务器交流群！"
            )
            db.add(group_config)
    
    # 提交事务
    db.commit()
    db.close()