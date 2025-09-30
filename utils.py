"""
Unturned服务器助手机器人工具模块
提供通用的工具函数和辅助功能
"""
import re
import time
import random
import string
import hashlib
import json
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List, Union

from core import logger

# 文本处理工具
def extract_steam_id(text: str) -> Optional[str]:
    """从文本中提取SteamID（数字ID）"""
    # 匹配纯数字SteamID
    match = re.search(r'\b\d{17}\b', text)
    if match:
        return match.group(0)
    
    # 匹配SteamID格式（如STEAM_0:0:12345678）
    match = re.search(r'STEAM_\d:\d:\d+', text)
    if match:
        # 转换为数字ID（这里简化处理，实际应该进行正确的转换）
        steam_id_text = match.group(0)
        parts = steam_id_text.split(':')
        if len(parts) >= 3:
            try:
                # 简单的转换算法，仅供参考
                account_id = int(parts[2])
                universe = int(parts[1])
                steam_id64 = 76561197960265728 + universe + account_id * 2
                return str(steam_id64)
            except ValueError:
                pass
    
    # 匹配Steam个人资料URL
    match = re.search(r'steamcommunity\.com/(profiles|id)/([\w-]+)', text)
    if match:
        # 这里应该调用Steam API来获取对应的数字ID
        # 但为了简化，我们只返回提取的部分
        return match.group(2)
    
    return None

def format_time(seconds: int) -> str:
    """将秒数格式化为易读的时间字符串"""
    if seconds < 0:
        return "0秒"
    
    days, remainder = divmod(seconds, 86400)
    hours, remainder = divmod(remainder, 3600)
    minutes, seconds = divmod(remainder, 60)
    
    parts = []
    if days > 0:
        parts.append(f"{days}天")
    if hours > 0:
        parts.append(f"{hours}小时")
    if minutes > 0:
        parts.append(f"{minutes}分钟")
    if seconds > 0 or not parts:
        parts.append(f"{seconds}秒")
    
    return "".join(parts)

def format_number(num: int) -> str:
    """格式化数字，添加千位分隔符"""
    return "{:,}".format(num)

def generate_random_string(length: int = 8, use_digits: bool = True, use_uppercase: bool = True, use_lowercase: bool = True) -> str:
    """生成随机字符串"""
    chars = ""
    if use_lowercase:
        chars += string.ascii_lowercase
    if use_uppercase:
        chars += string.ascii_uppercase
    if use_digits:
        chars += string.digits
    
    if not chars:
        raise ValueError("至少需要选择一种字符类型")
    
    return ''.join(random.choice(chars) for _ in range(length))

def md5_hash(text: str) -> str:
    """计算文本的MD5哈希值"""
    return hashlib.md5(text.encode()).hexdigest()

def sha1_hash(text: str) -> str:
    """计算文本的SHA1哈希值"""
    return hashlib.sha1(text.encode()).hexdigest()

# 日期时间工具
def get_current_timestamp() -> int:
    """获取当前时间戳（秒）"""
    return int(time.time())

def get_current_datetime() -> str:
    """获取当前日期时间字符串"""
    return datetime.now().strftime('%Y-%m-%d %H:%M:%S')

def get_date_string(date: Optional[datetime] = None) -> str:
    """获取日期字符串（YYYY-MM-DD）"""
    if date is None:
        date = datetime.now()
    return date.strftime('%Y-%m-%d')

def get_time_string(date: Optional[datetime] = None) -> str:
    """获取时间字符串（HH:MM:SS）"""
    if date is None:
        date = datetime.now()
    return date.strftime('%H:%M:%S')

def parse_datetime(datetime_str: str, formats: Optional[List[str]] = None) -> Optional[datetime]:
    """解析日期时间字符串"""
    if formats is None:
        formats = [
            '%Y-%m-%d %H:%M:%S',
            '%Y-%m-%d %H:%M',
            '%Y-%m-%d',
            '%Y/%m/%d %H:%M:%S',
            '%Y/%m/%d %H:%M',
            '%Y/%m/%d',
            '%d-%m-%Y %H:%M:%S',
            '%d-%m-%Y %H:%M',
            '%d-%m-%Y'
        ]
    
    for fmt in formats:
        try:
            return datetime.strptime(datetime_str, fmt)
        except ValueError:
            continue
    
    logger.warning(f"无法解析日期时间字符串: {datetime_str}")
    return None

def is_today(datetime_obj: datetime) -> bool:
    """检查给定的日期时间是否是今天"""
    return datetime_obj.date() == datetime.now().date()

def days_between(date1: datetime, date2: datetime) -> int:
    """计算两个日期之间的天数差"""
    return abs((date2.date() - date1.date()).days)

# 数据处理工具
def safe_json_loads(json_str: str) -> Optional[Dict[str, Any]]:
    """安全地解析JSON字符串"""
    try:
        return json.loads(json_str)
    except (json.JSONDecodeError, TypeError) as e:
        logger.error(f"解析JSON失败: {e}")
        return None

def safe_int(value: Any, default: int = 0) -> int:
    """安全地转换为整数"""
    try:
        return int(value)
    except (ValueError, TypeError):
        return default

def safe_float(value: Any, default: float = 0.0) -> float:
    """安全地转换为浮点数"""
    try:
        return float(value)
    except (ValueError, TypeError):
        return default

def safe_str(value: Any, default: str = "") -> str:
    """安全地转换为字符串"""
    try:
        if value is None:
            return default
        return str(value)
    except Exception:
        return default

def is_valid_qq(qq_id: str) -> bool:
    """验证QQ号是否有效"""
    # QQ号通常是5-13位数字
    return qq_id.isdigit() and 5 <= len(qq_id) <= 13

def is_valid_steam_id(steam_id: str) -> bool:
    """验证SteamID是否有效"""
    # SteamID64通常是17位数字
    return steam_id.isdigit() and len(steam_id) == 17

# 列表和字典处理工具
def get_dict_value(d: Dict[str, Any], keys: Union[str, List[str]], default: Any = None) -> Any:
    """从嵌套字典中获取值"""
    if isinstance(keys, str):
        keys = keys.split('.')
    
    current = d
    for key in keys:
        if not isinstance(current, dict) or key not in current:
            return default
        current = current[key]
    
    return current

def merge_dicts(dict1: Dict[str, Any], dict2: Dict[str, Any]) -> Dict[str, Any]:
    """合并两个字典，深拷贝"""
    result = dict1.copy()
    for key, value in dict2.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = merge_dicts(result[key], value)
        else:
            result[key] = value
    return result

def chunk_list(lst: List[Any], chunk_size: int) -> List[List[Any]]:
    """将列表分割成多个指定大小的子列表"""
    if chunk_size <= 0:
        raise ValueError("chunk_size必须大于0")
    
    return [lst[i:i+chunk_size] for i in range(0, len(lst), chunk_size)]

def flatten_list(nested_list: List[Any]) -> List[Any]:
    """扁平化嵌套列表"""
    result = []
    for item in nested_list:
        if isinstance(item, list):
            result.extend(flatten_list(item))
        else:
            result.append(item)
    return result

# 格式化工具
def format_message(template: str, **kwargs) -> str:
    """格式化消息模板"""
    try:
        return template.format(**kwargs)
    except KeyError as e:
        logger.error(f"消息格式化失败，缺少参数: {e}")
        return template

def format_percentage(numerator: int, denominator: int) -> str:
    """计算并格式化百分比"""
    if denominator == 0:
        return "0%"
    
    percentage = (numerator / denominator) * 100
    return f"{percentage:.1f}%"

def truncate_text(text: str, max_length: int, suffix: str = "...") -> str:
    """截断文本到指定长度"""
    if len(text) <= max_length:
        return text
    
    return text[:max_length - len(suffix)] + suffix

# 数字相关工具
def clamp(value: float, min_value: float, max_value: float) -> float:
    """将值限制在指定范围内"""
    return max(min_value, min(value, max_value))

def random_int(min_value: int, max_value: int) -> int:
    """生成指定范围内的随机整数"""
    return random.randint(min_value, max_value)

def random_float(min_value: float, max_value: float) -> float:
    """生成指定范围内的随机浮点数"""
    return random.uniform(min_value, max_value)

def calculate_average(numbers: List[float]) -> float:
    """计算平均值"""
    if not numbers:
        return 0.0
    
    return sum(numbers) / len(numbers)

def calculate_median(numbers: List[float]) -> float:
    """计算中位数"""
    if not numbers:
        return 0.0
    
    sorted_numbers = sorted(numbers)
    n = len(sorted_numbers)
    
    if n % 2 == 0:
        return (sorted_numbers[n//2 - 1] + sorted_numbers[n//2]) / 2
    else:
        return sorted_numbers[n//2]

# 网络相关工具
def is_valid_ip(ip: str) -> bool:
    """验证IP地址是否有效"""
    # 简单的IPv4验证
    pattern = r'^((25[0-5]|2[0-4]\d|[01]?\d\d?)\.){3}(25[0-5]|2[0-4]\d|[01]?\d\d?)$'
    return bool(re.match(pattern, ip))

def is_valid_port(port: int) -> bool:
    """验证端口号是否有效"""
    return isinstance(port, int) and 1 <= port <= 65535

def parse_server_address(address: str) -> Optional[Dict[str, Any]]:
    """解析服务器地址（IP:端口）"""
    # 尝试匹配IP:端口格式
    match = re.search(r'^([\d.]+):(\d+)$', address)
    if match:
        ip = match.group(1)
        port = int(match.group(2))
        
        if is_valid_ip(ip) and is_valid_port(port):
            return {"ip": ip, "port": port}
    
    # 尝试匹配域名:端口格式
    match = re.search(r'^([a-zA-Z0-9.-]+):(\d+)$', address)
    if match:
        domain = match.group(1)
        port = int(match.group(2))
        
        if is_valid_port(port):
            return {"domain": domain, "port": port}
    
    logger.warning(f"无效的服务器地址格式: {address}")
    return None

# 缓存工具
class SimpleCache:
    """简单的内存缓存实现"""
    def __init__(self):
        self._cache = {}
    
    def set(self, key: str, value: Any, ttl: int = 3600) -> None:
        """设置缓存项"""
        expiry = time.time() + ttl
        self._cache[key] = (value, expiry)
    
    def get(self, key: str) -> Optional[Any]:
        """获取缓存项"""
        if key not in self._cache:
            return None
        
        value, expiry = self._cache[key]
        
        # 检查是否过期
        if time.time() > expiry:
            self.delete(key)
            return None
        
        return value
    
    def delete(self, key: str) -> None:
        """删除缓存项"""
        if key in self._cache:
            del self._cache[key]
    
    def clear(self) -> None:
        """清空缓存"""
        self._cache.clear()
    
    def keys(self) -> List[str]:
        """获取所有缓存键"""
        # 先清理过期项
        self._cleanup()
        return list(self._cache.keys())
    
    def _cleanup(self) -> None:
        """清理过期的缓存项"""
        current_time = time.time()
        expired_keys = [k for k, (_, expiry) in self._cache.items() if current_time > expiry]
        
        for key in expired_keys:
            self.delete(key)

# 创建全局缓存实例
global_cache = SimpleCache()

# 导出常用工具函数
export_extract_steam_id = extract_steam_id
export_format_time = format_time
export_format_number = format_number
export_generate_random_string = generate_random_string
export_parse_datetime = parse_datetime
export_is_today = is_today
export_safe_json_loads = safe_json_loads
export_safe_int = safe_int
export_get_dict_value = get_dict_value
export_merge_dicts = merge_dicts
export_chunk_list = chunk_list
export_format_message = format_message
export_clamp = clamp
export_random_int = random_int
export_global_cache = global_cache