from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from .settings import get_config

# 获取配置
config = get_config()

# 创建数据库引擎
engine = create_engine(
    config.database_url, 
    connect_args={"check_same_thread": False} if config.database_url.startswith("sqlite") else {}
)

# 创建会话本地类
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 创建基础模型类
Base = declarative_base()

# 获取数据库会话
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# 初始化数据库
def init_db():
    # 创建所有表
    Base.metadata.create_all(bind=engine)

# 示例模型定义
# class ServerStatus(Base):
#     __tablename__ = "server_status"
#     id = Column(Integer, primary_key=True, index=True)
#     server_name = Column(String, index=True)
#     status = Column(Boolean)
#     players = Column(Integer)
#     last_update = Column(DateTime, default=datetime.utcnow)