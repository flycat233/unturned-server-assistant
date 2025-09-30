from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
import datetime
from database import Base

# QQ用户与SteamID绑定信息
class QQBotPlayers(Base):
    __tablename__ = "qq_bot_players"
    
    id = Column(Integer, primary_key=True, index=True)
    qq_id = Column(String(20), unique=True, index=True)
    steam_id = Column(String(50), unique=True, index=True)
    nickname = Column(String(100))
    points = Column(Integer, default=0)
    bind_time = Column(DateTime, default=datetime.datetime.utcnow)
    last_login = Column(DateTime, default=datetime.datetime.utcnow)
    last_checkin_date = Column(String(50))
    created_at = Column(String(50), default=lambda: datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S'))
    
    # 关系定义
    player_stats = relationship("PlayerStats", back_populates="player", uselist=False)
    daily_signin = relationship("DailySignIn", back_populates="player", uselist=False)

# 玩家游戏统计数据
class PlayerStats(Base):
    __tablename__ = "player_stats"
    
    id = Column(Integer, primary_key=True, index=True)
    player_id = Column(Integer, ForeignKey("qq_bot_players.id"))
    play_time = Column(Float, default=0)  # 游戏时长（小时）
    kills = Column(Integer, default=0)
    deaths = Column(Integer, default=0)
    zombies_killed = Column(Integer, default=0)
    last_update = Column(DateTime, default=datetime.datetime.utcnow)
    
    # 关系定义
    player = relationship("QQBotPlayers", back_populates="player_stats")

# 玩家游戏内经济数据
class Uconomy(Base):
    __tablename__ = "uconomy"
    
    id = Column(Integer, primary_key=True, index=True)
    steam_id = Column(String(50), unique=True, index=True)
    balance = Column(Float, default=0)
    last_update = Column(DateTime, default=datetime.datetime.utcnow)

# 服务器状态历史
class ServerStatus(Base):
    __tablename__ = "server_status"
    
    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    is_online = Column(Boolean, default=False)
    players = Column(Integer, default=0)
    max_players = Column(Integer, default=0)
    map = Column(String(100))
    message = Column(String(255))

# 玩家签到记录
class DailySignIn(Base):
    __tablename__ = "daily_signin"
    
    id = Column(Integer, primary_key=True, index=True)
    player_id = Column(Integer, ForeignKey("qq_bot_players.id"))
    last_signin = Column(DateTime)
    consecutive_days = Column(Integer, default=0)
    total_days = Column(Integer, default=0)
    
    # 关系定义
    player = relationship("QQBotPlayers", back_populates="daily_signin")

# 群管理配置
class GroupManagement(Base):
    __tablename__ = "group_management"
    
    id = Column(Integer, primary_key=True, index=True)
    group_id = Column(String(20), unique=True, index=True)
    enabled = Column(Boolean, default=True)
    admin_only = Column(Boolean, default=False)
    welcome_message = Column(String(255))
    last_update = Column(DateTime, default=datetime.datetime.utcnow)

# 命令执行日志
class CommandLogs(Base):
    __tablename__ = "command_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    user_id = Column(String(20))
    group_id = Column(String(20), nullable=True)
    command = Column(String(100))
    arguments = Column(String(255), nullable=True)
    success = Column(Boolean, default=True)
    result = Column(String(255), nullable=True)

# 系统公告
class Announcements(Base):
    __tablename__ = "announcements"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(100))
    content = Column(String(500))
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    created_by = Column(String(20))
    is_active = Column(Boolean, default=True)