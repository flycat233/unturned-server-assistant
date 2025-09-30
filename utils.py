import os
import sys
import time
import logging
from typing import Any, Dict, List, Optional, Union

# 设置日志配置
def setup_logger(name: str, log_file: Optional[str] = None, level: int = logging.INFO) -> logging.Logger:
    """
    设置一个自定义的日志记录器
    
    参数:
        name: 日志记录器名称
        log_file: 日志文件路径，如果为None则只输出到控制台
        level: 日志级别
    
    返回:
        配置好的日志记录器
    """
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.propagate = False  # 防止日志重复输出
    
    # 清除已有的处理器
    if logger.handlers:
        logger.handlers.clear()
    
    # 添加控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # 添加文件处理器（如果指定了日志文件）
    if log_file:
        # 确保日志目录存在
        log_dir = os.path.dirname(log_file)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir)
        
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger

# 检查是否是超级用户
def is_superuser(user_id: Union[str, int]) -> bool:
    """
    检查给定的用户ID是否是超级用户
    
    参数:
        user_id: 用户ID（字符串或整数）
    
    返回:
        是否是超级用户
    """
    from .settings import get_config
    config = get_config()
    return str(user_id) in config.superusers

# 格式化时间
def format_time(timestamp: float = None, format_str: str = "%Y-%m-%d %H:%M:%S") -> str:
    """
    将时间戳格式化为字符串
    
    参数:
        timestamp: 时间戳，如果为None则使用当前时间
        format_str: 时间格式字符串
    
    返回:
        格式化后的时间字符串
    """
    if timestamp is None:
        timestamp = time.time()
    return time.strftime(format_str, time.localtime(timestamp))

# 安全地转换为整数
def safe_int(value: Any, default: int = 0) -> int:
    """
    安全地将值转换为整数
    
    参数:
        value: 要转换的值
        default: 转换失败时的默认值
    
    返回:
        转换后的整数或默认值
    """
    try:
        return int(value)
    except (ValueError, TypeError):
        return default

# 安全地转换为字符串
def safe_str(value: Any, default: str = "") -> str:
    """
    安全地将值转换为字符串
    
    参数:
        value: 要转换的值
        default: 转换失败时的默认值
    
    返回:
        转换后的字符串或默认值
    """
    try:
        return str(value)
    except (ValueError, TypeError):
        return default

# 检查文件是否存在
def file_exists(file_path: str) -> bool:
    """
    检查文件是否存在
    
    参数:
        file_path: 文件路径
    
    返回:
        文件是否存在
    """
    return os.path.isfile(file_path)

# 确保目录存在
def ensure_dir(dir_path: str) -> bool:
    """
    确保目录存在，如果不存在则创建
    
    参数:
        dir_path: 目录路径
    
    返回:
        是否成功创建或目录已存在
    """
    try:
        if not os.path.exists(dir_path):
            os.makedirs(dir_path, exist_ok=True)
        return True
    except Exception:
        return False

# 从文件读取文本
def read_file(file_path: str, encoding: str = 'utf-8') -> Optional[str]:
    """
    从文件中读取文本
    
    参数:
        file_path: 文件路径
        encoding: 文件编码
    
    返回:
        文件内容，如果文件不存在或读取失败则返回None
    """
    if not file_exists(file_path):
        return None
    
    try:
        with open(file_path, 'r', encoding=encoding) as f:
            return f.read()
    except Exception:
        return None

# 写入文本到文件
def write_file(file_path: str, content: str, encoding: str = 'utf-8') -> bool:
    """
    将文本写入文件
    
    参数:
        file_path: 文件路径
        content: 要写入的内容
        encoding: 文件编码
    
    返回:
        是否写入成功
    """
    try:
        # 确保目录存在
        dir_path = os.path.dirname(file_path)
        if dir_path and not os.path.exists(dir_path):
            os.makedirs(dir_path, exist_ok=True)
        
        with open(file_path, 'w', encoding=encoding) as f:
            f.write(content)
        return True
    except Exception:
        return False

# 获取当前工作目录
def get_working_dir() -> str:
    """
    获取当前工作目录
    
    返回:
        当前工作目录的绝对路径
    """
    return os.path.dirname(os.path.abspath(sys.argv[0])) if sys.argv else os.getcwd()