import aiohttp
import json
import logging
from typing import Dict, Any, Optional
from .settings import get_config

logger = logging.getLogger("unturned_bot")
config = get_config()

class OneBotHTTP:
    def __init__(self):
        self.api_url = f"http://{config.onebot_host}:{config.onebot_port}/"
        self.access_token = config.onebot_access_token
        self.headers = {
            "Content-Type": "application/json"
        }
        if self.access_token:
            self.headers["Authorization"] = f"Bearer {self.access_token}"
        
    async def _request(self, action: str, params: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        try:
            url = f"{self.api_url}{action}"
            async with aiohttp.ClientSession(headers=self.headers) as session:
                async with session.post(url, json=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data.get("status") == "ok":
                            return data.get("data")
                        else:
                            logger.error(f"OneBot API error: {data}")
                    else:
                        logger.error(f"OneBot API request failed: HTTP {response.status}")
        except Exception as e:
            logger.error(f"OneBot API request exception: {e}")
        return None
    
    # 发送私聊消息
    async def send_private_msg(self, user_id: int, message: str) -> Optional[Dict[str, Any]]:
        params = {
            "user_id": user_id,
            "message": message
        }
        return await self._request("send_private_msg", params)
    
    # 发送群消息
    async def send_group_msg(self, group_id: int, message: str) -> Optional[Dict[str, Any]]:
        params = {
            "group_id": group_id,
            "message": message
        }
        return await self._request("send_group_msg", params)
    
    # 发送广播消息到所有启用的群
    async def broadcast(self, message: str) -> Dict[str, Any]:
        from .database import get_db
        from .models import GroupManagement
        
        results = {
            "success": [],
            "failed": []
        }
        
        db = next(get_db())
        try:
            groups = db.query(GroupManagement).filter(GroupManagement.enabled == True).all()
            
            for group in groups:
                result = await self.send_group_msg(int(group.group_id), message)
                if result:
                    results["success"].append(group.group_id)
                else:
                    results["failed"].append(group.group_id)
        finally:
            db.close()
            
        return results

# 全局实例
bot_http = OneBotHTTP()