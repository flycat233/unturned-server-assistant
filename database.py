"""
Unturned服务器助手机器人数据库模块
包含所有数据库模型定义和表操作功能
"""
import sqlite3
from datetime import datetime
from typing import Optional, Dict, List, Any
from core import db_manager, logger, config

# 数据库模型定义与操作类
class Database:
    @staticmethod
    def init_database():
        """初始化数据库，创建所有表"""
        conn = db_manager.connect()
        cursor = conn.cursor()
        
        try:
            # 创建QQBotPlayers表：存储QQ用户与SteamID绑定信息
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS QQBotPlayers (
                    qq_id TEXT PRIMARY KEY,
                    steam_id TEXT NOT NULL UNIQUE,
                    nickname TEXT,
                    create_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_update_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # 创建PlayerStats表：存储玩家游戏统计数据
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS PlayerStats (
                    steam_id TEXT PRIMARY KEY,
                    total_play_time INTEGER DEFAULT 0,
                    kill_count INTEGER DEFAULT 0,
                    death_count INTEGER DEFAULT 0,
                    zombie_kills INTEGER DEFAULT 0,
                    headshots INTEGER DEFAULT 0,
                    play_sessions INTEGER DEFAULT 0,
                    last_online TIMESTAMP,
                    FOREIGN KEY (steam_id) REFERENCES QQBotPlayers (steam_id)
                )
            ''')
            
            # 创建Uconomy表：存储玩家游戏内经济数据
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS Uconomy (
                    steam_id TEXT PRIMARY KEY,
                    balance INTEGER DEFAULT 0,
                    last_update_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (steam_id) REFERENCES QQBotPlayers (steam_id)
                )
            ''')
            
            # 创建ServerStatus表：记录服务器状态历史
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS ServerStatus (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    online INTEGER NOT NULL,
                    players INTEGER DEFAULT 0,
                    max_players INTEGER DEFAULT 0,
                    server_name TEXT,
                    map_name TEXT,
                    version TEXT,
                    status_message TEXT
                )
            ''')
            
            # 创建DailySignIn表：存储玩家签到记录
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS DailySignIn (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    steam_id TEXT NOT NULL,
                    sign_in_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    reward INTEGER NOT NULL,
                    FOREIGN KEY (steam_id) REFERENCES QQBotPlayers (steam_id)
                )
            ''')
            
            # 创建GroupManagement表：存储群管理配置
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS GroupManagement (
                    group_id TEXT PRIMARY KEY,
                    admin_list TEXT DEFAULT '',
                    enable_monitor INTEGER DEFAULT 1,
                    notify_online INTEGER DEFAULT 1,
                    notify_offline INTEGER DEFAULT 1,
                    welcome_message TEXT DEFAULT '',
                    auto_approve INTEGER DEFAULT 0
                )
            ''')
            
            # 创建CommandLogs表：记录命令执行日志
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS CommandLogs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    qq_id TEXT NOT NULL,
                    group_id TEXT,
                    command TEXT NOT NULL,
                    parameters TEXT,
                    success INTEGER NOT NULL,
                    error_message TEXT
                )
            ''')
            
            # 创建Announcements表：存储系统公告
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS Announcements (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    content TEXT NOT NULL,
                    create_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    author TEXT NOT NULL,
                    is_active INTEGER DEFAULT 1
                )
            ''')
            
            conn.commit()
            logger.info("数据库初始化完成，所有表已创建")
        except sqlite3.Error as e:
            logger.error(f"数据库初始化失败: {e}")
            conn.rollback()
        finally:
            cursor.close()
    
    # QQBotPlayers相关操作
    @staticmethod
    def bind_qq_steam(qq_id: str, steam_id: str, nickname: str = None) -> bool:
        """绑定QQ账号与SteamID"""
        conn = db_manager.connect()
        cursor = conn.cursor()
        try:
            cursor.execute(
                "INSERT OR REPLACE INTO QQBotPlayers (qq_id, steam_id, nickname, last_update_time) VALUES (?, ?, ?, ?)",
                (qq_id, steam_id, nickname, datetime.now())
            )
            
            # 确保PlayerStats表中有对应的记录
            cursor.execute(
                "INSERT OR IGNORE INTO PlayerStats (steam_id) VALUES (?)",
                (steam_id,)
            )
            
            # 确保Uconomy表中有对应的记录
            cursor.execute(
                "INSERT OR IGNORE INTO Uconomy (steam_id) VALUES (?)",
                (steam_id,)
            )
            
            conn.commit()
            logger.info(f"QQ {qq_id} 成功绑定SteamID {steam_id}")
            return True
        except sqlite3.Error as e:
            logger.error(f"绑定QQ与SteamID失败: {e}")
            conn.rollback()
            return False
        finally:
            cursor.close()
    
    @staticmethod
    def get_steam_id_by_qq(qq_id: str) -> Optional[str]:
        """通过QQ号获取绑定的SteamID"""
        conn = db_manager.connect()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT steam_id FROM QQBotPlayers WHERE qq_id = ?", (qq_id,))
            result = cursor.fetchone()
            return result[0] if result else None
        except sqlite3.Error as e:
            logger.error(f"获取SteamID失败: {e}")
            return None
        finally:
            cursor.close()
    
    @staticmethod
    def get_qq_id_by_steam(steam_id: str) -> Optional[str]:
        """通过SteamID获取绑定的QQ号"""
        conn = db_manager.connect()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT qq_id FROM QQBotPlayers WHERE steam_id = ?", (steam_id,))
            result = cursor.fetchone()
            return result[0] if result else None
        except sqlite3.Error as e:
            logger.error(f"获取QQ号失败: {e}")
            return None
        finally:
            cursor.close()
    
    # PlayerStats相关操作
    @staticmethod
    def update_player_stats(steam_id: str, stats: Dict[str, Any]) -> bool:
        """更新玩家统计数据"""
        conn = db_manager.connect()
        cursor = conn.cursor()
        try:
            # 构建更新语句
            set_clause = ", ".join([f"{key} = ?" for key in stats.keys()])
            values = list(stats.values()) + [steam_id]
            
            cursor.execute(f"UPDATE PlayerStats SET {set_clause} WHERE steam_id = ?", values)
            conn.commit()
            return True
        except sqlite3.Error as e:
            logger.error(f"更新玩家统计数据失败: {e}")
            conn.rollback()
            return False
        finally:
            cursor.close()
    
    @staticmethod
    def get_player_stats(steam_id: str) -> Optional[Dict[str, Any]]:
        """获取玩家统计数据"""
        conn = db_manager.connect()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT * FROM PlayerStats WHERE steam_id = ?", (steam_id,))
            result = cursor.fetchone()
            if not result:
                return None
            
            columns = [desc[0] for desc in cursor.description]
            return dict(zip(columns, result))
        except sqlite3.Error as e:
            logger.error(f"获取玩家统计数据失败: {e}")
            return None
        finally:
            cursor.close()
    
    # Uconomy相关操作
    @staticmethod
    def update_balance(steam_id: str, amount: int, is_add: bool = True) -> bool:
        """更新玩家经济数据"""
        conn = db_manager.connect()
        cursor = conn.cursor()
        try:
            if is_add:
                cursor.execute(
                    "UPDATE Uconomy SET balance = balance + ?, last_update_time = ? WHERE steam_id = ?",
                    (amount, datetime.now(), steam_id)
                )
            else:
                cursor.execute(
                    "UPDATE Uconomy SET balance = balance - ?, last_update_time = ? WHERE steam_id = ?",
                    (amount, datetime.now(), steam_id)
                )
            conn.commit()
            return True
        except sqlite3.Error as e:
            logger.error(f"更新玩家经济数据失败: {e}")
            conn.rollback()
            return False
        finally:
            cursor.close()
    
    @staticmethod
    def get_balance(steam_id: str) -> int:
        """获取玩家余额"""
        conn = db_manager.connect()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT balance FROM Uconomy WHERE steam_id = ?", (steam_id,))
            result = cursor.fetchone()
            return result[0] if result else 0
        except sqlite3.Error as e:
            logger.error(f"获取玩家余额失败: {e}")
            return 0
        finally:
            cursor.close()
    
    # ServerStatus相关操作
    @staticmethod
    def record_server_status(status: Dict[str, Any]) -> bool:
        """记录服务器状态"""
        conn = db_manager.connect()
        cursor = conn.cursor()
        try:
            cursor.execute(
                '''INSERT INTO ServerStatus (online, players, max_players, server_name, map_name, version, status_message)
                   VALUES (?, ?, ?, ?, ?, ?, ?)''',
                (
                    1 if status.get('online', False) else 0,
                    status.get('players', 0),
                    status.get('max_players', 0),
                    status.get('name', ''),
                    status.get('map', ''),
                    status.get('version', ''),
                    status.get('error', '')
                )
            )
            conn.commit()
            return True
        except sqlite3.Error as e:
            logger.error(f"记录服务器状态失败: {e}")
            conn.rollback()
            return False
        finally:
            cursor.close()
    
    @staticmethod
    def get_latest_server_status() -> Optional[Dict[str, Any]]:
        """获取最新的服务器状态"""
        conn = db_manager.connect()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT * FROM ServerStatus ORDER BY timestamp DESC LIMIT 1")
            result = cursor.fetchone()
            if not result:
                return None
            
            columns = [desc[0] for desc in cursor.description]
            return dict(zip(columns, result))
        except sqlite3.Error as e:
            logger.error(f"获取服务器状态失败: {e}")
            return None
        finally:
            cursor.close()
    
    # DailySignIn相关操作
    @staticmethod
    def record_sign_in(steam_id: str, reward: int) -> bool:
        """记录玩家签到"""
        conn = db_manager.connect()
        cursor = conn.cursor()
        try:
            cursor.execute(
                "INSERT INTO DailySignIn (steam_id, reward) VALUES (?, ?)",
                (steam_id, reward)
            )
            conn.commit()
            return True
        except sqlite3.Error as e:
            logger.error(f"记录签到失败: {e}")
            conn.rollback()
            return False
        finally:
            cursor.close()
    
    @staticmethod
    def has_signed_in_today(steam_id: str) -> bool:
        """检查玩家今天是否已签到"""
        conn = db_manager.connect()
        cursor = conn.cursor()
        try:
            today = datetime.now().strftime("%Y-%m-%d")
            cursor.execute(
                "SELECT COUNT(*) FROM DailySignIn WHERE steam_id = ? AND DATE(sign_in_time) = ?",
                (steam_id, today)
            )
            result = cursor.fetchone()
            return result[0] > 0
        except sqlite3.Error as e:
            logger.error(f"检查签到状态失败: {e}")
            return False
        finally:
            cursor.close()
    
    @staticmethod
    def get_sign_in_count(steam_id: str) -> int:
        """获取玩家签到次数"""
        conn = db_manager.connect()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT COUNT(*) FROM DailySignIn WHERE steam_id = ?", (steam_id,))
            result = cursor.fetchone()
            return result[0] if result else 0
        except sqlite3.Error as e:
            logger.error(f"获取签到次数失败: {e}")
            return 0
        finally:
            cursor.close()
    
    # GroupManagement相关操作
    @staticmethod
    def get_group_config(group_id: str) -> Dict[str, Any]:
        """获取群配置"""
        conn = db_manager.connect()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT * FROM GroupManagement WHERE group_id = ?", (group_id,))
            result = cursor.fetchone()
            if not result:
                # 如果群配置不存在，返回默认配置
                default_config = {
                    "group_id": group_id,
                    "admin_list": "",
                    "enable_monitor": 1,
                    "notify_online": 1,
                    "notify_offline": 1,
                    "welcome_message": "",
                    "auto_approve": 0
                }
                # 插入默认配置
                cursor.execute(
                    '''INSERT INTO GroupManagement (group_id, admin_list, enable_monitor, notify_online, notify_offline, welcome_message, auto_approve)
                       VALUES (?, ?, ?, ?, ?, ?, ?)''',
                    tuple(default_config.values())
                )
                conn.commit()
                return default_config
            
            columns = [desc[0] for desc in cursor.description]
            return dict(zip(columns, result))
        except sqlite3.Error as e:
            logger.error(f"获取群配置失败: {e}")
            # 返回默认配置
            return {
                "group_id": group_id,
                "admin_list": "",
                "enable_monitor": 1,
                "notify_online": 1,
                "notify_offline": 1,
                "welcome_message": "",
                "auto_approve": 0
            }
        finally:
            cursor.close()
    
    @staticmethod
    def update_group_config(group_id: str, config: Dict[str, Any]) -> bool:
        """更新群配置"""
        conn = db_manager.connect()
        cursor = conn.cursor()
        try:
            # 确保群配置存在
            current_config = Database.get_group_config(group_id)
            
            # 合并配置
            current_config.update(config)
            
            cursor.execute(
                '''UPDATE GroupManagement SET admin_list = ?, enable_monitor = ?, notify_online = ?, notify_offline = ?, welcome_message = ?, auto_approve = ?
                   WHERE group_id = ?''',
                (
                    current_config["admin_list"],
                    current_config["enable_monitor"],
                    current_config["notify_online"],
                    current_config["notify_offline"],
                    current_config["welcome_message"],
                    current_config["auto_approve"],
                    group_id
                )
            )
            conn.commit()
            return True
        except sqlite3.Error as e:
            logger.error(f"更新群配置失败: {e}")
            conn.rollback()
            return False
        finally:
            cursor.close()
    
    # CommandLogs相关操作
    @staticmethod
    def log_command(qq_id: str, command: str, parameters: str = None, group_id: str = None, success: bool = True, error_message: str = None) -> bool:
        """记录命令执行日志"""
        conn = db_manager.connect()
        cursor = conn.cursor()
        try:
            cursor.execute(
                "INSERT INTO CommandLogs (qq_id, group_id, command, parameters, success, error_message) VALUES (?, ?, ?, ?, ?, ?)",
                (qq_id, group_id, command, parameters, 1 if success else 0, error_message)
            )
            conn.commit()
            return True
        except sqlite3.Error as e:
            logger.error(f"记录命令日志失败: {e}")
            conn.rollback()
            return False
        finally:
            cursor.close()
    
    # Announcements相关操作
    @staticmethod
    def add_announcement(title: str, content: str, author: str) -> bool:
        """添加公告"""
        conn = db_manager.connect()
        cursor = conn.cursor()
        try:
            cursor.execute(
                "INSERT INTO Announcements (title, content, author) VALUES (?, ?, ?)",
                (title, content, author)
            )
            conn.commit()
            return True
        except sqlite3.Error as e:
            logger.error(f"添加公告失败: {e}")
            conn.rollback()
            return False
        finally:
            cursor.close()
    
    @staticmethod
    def get_active_announcements() -> List[Dict[str, Any]]:
        """获取所有活跃的公告"""
        conn = db_manager.connect()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT * FROM Announcements WHERE is_active = 1 ORDER BY create_time DESC")
            results = cursor.fetchall()
            if not results:
                return []
            
            columns = [desc[0] for desc in cursor.description]
            return [dict(zip(columns, row)) for row in results]
        except sqlite3.Error as e:
            logger.error(f"获取公告失败: {e}")
            return []
        finally:
            cursor.close()

# 初始化数据库
database = Database()
database.init_database()