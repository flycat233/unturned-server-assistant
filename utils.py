import logging
import datetime
import requests
from settings import get_config

# 配置日志
def setup_logger():
    config = get_config()
    logger = logging.getLogger("unturned_bot")
    logger.setLevel(getattr(logging, config.LOG_LEVEL))
    
    # 清空已有的处理器
    if logger.handlers:
        logger.handlers.clear()
    
    # 创建控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setLevel(getattr(logging, config.LOG_LEVEL))
    
    # 创建文件处理器（如果启用）
    if config.LOG_TO_FILE:
        file_handler = logging.FileHandler(config.LOG_FILE, encoding="utf-8")
        file_handler.setLevel(getattr(logging, config.LOG_LEVEL))
    
    # 设置日志格式
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    console_handler.setFormatter(formatter)
    if config.LOG_TO_FILE:
        file_handler.setFormatter(formatter)
    
    # 添加处理器
    logger.addHandler(console_handler)
    if config.LOG_TO_FILE:
        logger.addHandler(file_handler)
    
    return logger

# 获取日志记录器
logger = setup_logger()

# 发送API请求
def send_api_request(url, method="GET", data=None, headers=None):
    config = get_config()
    retry_count = 0
    
    # 如果没有提供headers，使用默认headers
    if headers is None:
        headers = {}
        if config.API_KEY:
            headers["Authorization"] = f"Bearer {config.API_KEY}"
    
    while retry_count <= config.MAX_RETRY_TIMES:
        try:
            if method.upper() == "GET":
                response = requests.get(url, params=data, headers=headers, timeout=config.SERVER_TIMEOUT)
            elif method.upper() == "POST":
                response = requests.post(url, json=data, headers=headers, timeout=config.SERVER_TIMEOUT)
            elif method.upper() == "PUT":
                response = requests.put(url, json=data, headers=headers, timeout=config.SERVER_TIMEOUT)
            elif method.upper() == "DELETE":
                response = requests.delete(url, headers=headers, timeout=config.SERVER_TIMEOUT)
            else:
                logger.error(f"不支持的请求方法: {method}")
                return None
            
            response.raise_for_status()  # 抛出HTTP错误
            return response.json()
        except requests.exceptions.RequestException as e:
            retry_count += 1
            logger.error(f"API请求失败 (尝试 {retry_count}/{config.MAX_RETRY_TIMES}): {str(e)}")
            
            if retry_count <= config.MAX_RETRY_TIMES:
                logger.info(f"{config.RETRY_INTERVAL}秒后重试...")
                import time
                time.sleep(config.RETRY_INTERVAL)
            else:
                logger.error("达到最大重试次数，请求失败")
                return None

# 格式化时间
def format_time(dt):
    if isinstance(dt, datetime.datetime):
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    return str(dt)

# 检查是否为超级用户
def is_superuser(user_id):
    config = get_config()
    return str(user_id) in [str(uid) for uid in config.SUPERUSERS]

# 获取当前时间戳
def get_current_timestamp():
    return datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")

# 计算连续签到奖励
def calculate_sign_in_reward(consecutive_days):
    config = get_config()
    reward = config.SIGN_IN_REWARD_BASE
    
    # 添加连续签到额外奖励
    if consecutive_days % 30 == 0:
        reward += config.SIGN_IN_REWARD_30DAYS
    elif consecutive_days % 7 == 0:
        reward += config.SIGN_IN_REWARD_7DAYS
    
    return reward

# 发送OneBot消息
def send_onebot_message(message_type, user_id=None, group_id=None, message=None):
    config = get_config()
    url = f"{config.ONE_BOT_URL}/send_message"
    
    # 构建消息参数
    params = {
        "message_type": message_type,
        "message": message
    }
    
    if message_type == "private" and user_id:
        params["user_id"] = user_id
    elif message_type == "group" and group_id:
        params["group_id"] = group_id
    else:
        logger.error("消息类型或目标ID不正确")
        return False
    
    # 添加访问令牌（如果有）
    headers = {}
    if config.ONE_BOT_ACCESS_TOKEN:
        headers["Authorization"] = f"Bearer {config.ONE_BOT_ACCESS_TOKEN}"
    
    # 发送请求
    response = send_api_request(url, method="POST", data=params, headers=headers)
    
    if response and response.get("status") == "ok":
        logger.info(f"成功发送{message_type}消息到{user_id or group_id}")
        return True
    else:
        logger.error(f"发送消息失败: {response}")
        return False

# 记录命令日志
def log_command(user_id, group_id, command, arguments, success, result):
    from database import get_db
    from models import CommandLogs
    import datetime
    
    try:
        db = next(get_db())
        log_entry = CommandLogs(
            user_id=str(user_id),
            group_id=str(group_id) if group_id else None,
            command=command,
            arguments=arguments,
            success=success,
            result=result[:255] if result else None  # 截断过长的结果
        )
        db.add(log_entry)
        db.commit()
    except Exception as e:
        logger.error(f"记录命令日志失败: {str(e)}")
    finally:
        db.close()