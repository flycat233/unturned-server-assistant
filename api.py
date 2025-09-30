"""
Unturned服务器助手机器人API模块
提供FastAPI接口，支持通过HTTP请求向指定QQ群或私聊发送消息
"""
import asyncio
import uvicorn
from fastapi import FastAPI, HTTPException, Depends, Request, Response
from fastapi.security import APIKeyHeader
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
import json
import hmac
import hashlib

from nonebot import get_bot
from nonebot.adapters.onebot.v11 import MessageSegment

from core import config, logger, verify_onebot_signature, send_request
from database import database

# API密钥认证
expected_api_key = config.api_key
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

def get_api_key(api_key: str = Depends(api_key_header)):
    """验证API密钥"""
    if not expected_api_key:
        # 如果没有配置API密钥，则跳过验证
        return True
    if not api_key or api_key != expected_api_key:
        raise HTTPException(status_code=403, detail="无效的API密钥")
    return True

# FastAPI应用初始化
api_app = FastAPI(
    title="Unturned服务器助手机器人API",
    description="提供消息发送、服务器状态查询等功能的API接口",
    version="1.0.0"
)

# 数据模型定义
class SendMessageRequest(BaseModel):
    """发送消息请求模型"""
    type: str = Field(..., description="消息类型：private 或 group", regex="^(private|group)$")
    target_id: str = Field(..., description="目标ID：私聊为QQ号，群聊为群号")
    message: str = Field(..., description="消息内容")
    reply_id: Optional[str] = Field(None, description="回复的消息ID")
    auto_escape: Optional[bool] = Field(False, description="是否自动转义特殊字符")

class BroadcastMessageRequest(BaseModel):
    """广播消息请求模型"""
    message: str = Field(..., description="广播消息内容")
    include_groups: Optional[List[str]] = Field(None, description="指定要发送的群列表，为空则发送到所有配置了监控的群")

class ServerStatusRequest(BaseModel):
    """服务器状态查询请求模型"""
    ip: Optional[str] = Field(None, description="服务器IP，默认使用配置中的SERVER_IP")
    port: Optional[int] = Field(None, description="服务器端口，默认使用配置中的SERVER_PORT")

# 工具函数
async def send_onebot_message(bot_id: str, message_type: str, target_id: str, message: str, 
                              reply_id: str = None, auto_escape: bool = False) -> Dict[str, Any]:
    """发送OneBot消息"""
    try:
        bot = get_bot(bot_id)
        
        if message_type == "private":
            if reply_id:
                return await bot.call_api(
                    "send_private_msg",
                    user_id=target_id,
                    message=message,
                    reply_message_id=reply_id,
                    auto_escape=auto_escape
                )
            else:
                return await bot.call_api(
                    "send_private_msg",
                    user_id=target_id,
                    message=message,
                    auto_escape=auto_escape
                )
        elif message_type == "group":
            if reply_id:
                return await bot.call_api(
                    "send_group_msg",
                    group_id=target_id,
                    message=message,
                    reply_message_id=reply_id,
                    auto_escape=auto_escape
                )
            else:
                return await bot.call_api(
                    "send_group_msg",
                    group_id=target_id,
                    message=message,
                    auto_escape=auto_escape
                )
        else:
            raise ValueError(f"不支持的消息类型: {message_type}")
    except Exception as e:
        logger.error(f"发送消息失败: {e}")
        raise HTTPException(status_code=500, detail=f"发送消息失败: {str(e)}")

async def get_all_bots() -> List[str]:
    """获取所有可用的机器人ID"""
    bots = []
    for bot_id in get_bot().bots:
        bots.append(bot_id)
    return bots

async def get_first_bot_id() -> str:
    """获取第一个可用的机器人ID"""
    bots = await get_all_bots()
    if not bots:
        raise HTTPException(status_code=503, detail="当前没有可用的机器人")
    return bots[0]

# API端点
@api_app.get("/health", summary="健康检查", tags=["基础功能"])
async def health_check():
    """检查机器人API服务是否正常运行"""
    return {
        "status": "ok",
        "message": "Unturned服务器助手机器人API服务正常运行中",
        "timestamp": asyncio.get_event_loop().time()
    }

@api_app.get("/info", summary="机器人信息", tags=["基础功能"])
async def bot_info(api_key: bool = Depends(get_api_key)):
    """获取机器人的基本信息"""
    bots = await get_all_bots()
    return {
        "status": "ok",
        "bots": bots,
        "server_ip": config.server_ip,
        "server_port": config.server_port,
        "monitor_interval": config.monitor_interval,
        "superusers": config.superusers
    }

@api_app.post("/send_message", summary="发送消息", tags=["消息功能"])
async def send_message(request: SendMessageRequest, api_key: bool = Depends(get_api_key)):
    """向指定QQ群或私聊发送消息"""
    bot_id = await get_first_bot_id()
    result = await send_onebot_message(
        bot_id=bot_id,
        message_type=request.type,
        target_id=request.target_id,
        message=request.message,
        reply_id=request.reply_id,
        auto_escape=request.auto_escape
    )
    
    logger.info(f"通过API发送{request.type}消息到{request.target_id}成功")
    return {
        "status": "ok",
        "result": result,
        "message_id": result.get("message_id")
    }

@api_app.post("/broadcast", summary="广播消息", tags=["消息功能"])
async def broadcast_message(request: BroadcastMessageRequest, api_key: bool = Depends(get_api_key)):
    """向多个群组广播消息"""
    if request.include_groups:
        # 发送到指定的群组
        groups = request.include_groups
    else:
        # 获取所有启用了监控的群组（这里简化处理，实际应该从数据库查询）
        groups = []
        # TODO: 从GroupManagement表中获取启用了监控的群组
    
    results = {}
    failed_groups = []
    
    bot_id = await get_first_bot_id()
    for group_id in groups:
        try:
            result = await send_onebot_message(
                bot_id=bot_id,
                message_type="group",
                target_id=group_id,
                message=request.message
            )
            results[group_id] = result
        except Exception as e:
            logger.error(f"向群组{group_id}广播消息失败: {e}")
            failed_groups.append({
                "group_id": group_id,
                "error": str(e)
            })
    
    logger.info(f"广播消息完成，成功: {len(results)}, 失败: {len(failed_groups)}")
    return {
        "status": "ok",
        "total_groups": len(groups),
        "success_count": len(results),
        "failed_count": len(failed_groups),
        "failed_groups": failed_groups
    }

@api_app.get("/server_status", summary="服务器状态查询", tags=["服务器功能"])
async def get_server_status(ip: Optional[str] = None, port: Optional[int] = None, api_key: bool = Depends(get_api_key)):
    """获取Unturned服务器的当前状态"""
    from core import check_server_status
    
    server_ip = ip or config.server_ip
    server_port = port or config.server_port
    
    # 检查服务器状态
    status = await check_server_status(server_ip, server_port)
    
    # 记录服务器状态到数据库
    database.record_server_status(status)
    
    logger.info(f"查询服务器{server_ip}:{server_port}状态完成")
    return {
        "status": "ok",
        "server_info": {
            "ip": server_ip,
            "port": server_port
        },
        "server_status": status,
        "timestamp": asyncio.get_event_loop().time()
    }

@api_app.get("/player_info", summary="玩家信息查询", tags=["玩家功能"])
async def get_player_info(qq_id: Optional[str] = None, steam_id: Optional[str] = None, api_key: bool = Depends(get_api_key)):
    """查询玩家的信息"""
    if not qq_id and not steam_id:
        raise HTTPException(status_code=400, detail="必须提供qq_id或steam_id")
    
    # 根据QQ号获取SteamID
    if qq_id:
        steam_id = database.get_steam_id_by_qq(qq_id)
        if not steam_id:
            raise HTTPException(status_code=404, detail=f"QQ号{qq_id}未绑定SteamID")
    
    # 获取玩家信息
    player_stats = database.get_player_stats(steam_id)
    balance = database.get_balance(steam_id)
    sign_in_count = database.get_sign_in_count(steam_id)
    
    if not player_stats:
        raise HTTPException(status_code=404, detail=f"未找到SteamID为{steam_id}的玩家信息")
    
    # 获取绑定的QQ号（如果有的话）
    if not qq_id:
        qq_id = database.get_qq_id_by_steam(steam_id)
    
    logger.info(f"查询玩家信息完成: steam_id={steam_id}")
    return {
        "status": "ok",
        "player_info": {
            "qq_id": qq_id,
            "steam_id": steam_id,
            "stats": player_stats,
            "balance": balance,
            "sign_in_count": sign_in_count
        }
    }

# OneBot事件接收处理（用于游戏插件的通信）
@api_app.post("/onebot_event", summary="OneBot事件接收", tags=["游戏插件集成"])
async def receive_onebot_event(request: Request):
    """接收来自OneBot的事件上报
    参考文档: https://283375.github.io/onebot_v11_vitepress/communication/http-post.html
    """
    try:
        # 获取请求头中的签名
        signature = request.headers.get("X-Signature", "")
        
        # 获取请求体数据
        data = await request.body()
        
        # 验证签名
        if not verify_onebot_signature(data, signature):
            logger.warning("接收到无效签名的OneBot事件")
            return Response(status_code=403)
        
        # 解析JSON数据
        event_data = json.loads(data)
        
        # 处理事件数据
        post_type = event_data.get("post_type", "")
        
        if post_type == "message":
            # 处理消息事件
            message_type = event_data.get("message_type", "")
            user_id = event_data.get("user_id", "")
            group_id = event_data.get("group_id", "")
            message = event_data.get("message", "")
            
            logger.info(f"接收到消息事件: type={message_type}, user_id={user_id}, group_id={group_id}, message={message}")
            
            # TODO: 在这里实现游戏插件需要的消息处理逻辑
            # 例如，将消息转发到游戏内聊天
            
        elif post_type == "notice":
            # 处理通知事件
            notice_type = event_data.get("notice_type", "")
            
            logger.info(f"接收到通知事件: type={notice_type}")
            
        elif post_type == "request":
            # 处理请求事件
            request_type = event_data.get("request_type", "")
            
            logger.info(f"接收到请求事件: type={request_type}")
            
        else:
            logger.info(f"接收到未知类型的事件: {post_type}")
        
        # 返回204状态码表示成功接收但不需要快速操作
        return Response(status_code=204)
        
    except json.JSONDecodeError:
        logger.error("接收到无效的JSON数据")
        return Response(status_code=400)
    except Exception as e:
        logger.error(f"处理OneBot事件失败: {e}")
        return Response(status_code=500)

# API服务器启动函数
async def start_api_server():
    """启动API服务器"""
    try:
        # 使用uvicorn运行FastAPI应用
        config = uvicorn.Config(
            api_app,
            host="0.0.0.0",
            port=8080,
            log_level="info"
        )
        server = uvicorn.Server(config)
        
        logger.info("Unturned服务器助手机器人API服务启动成功，监听端口: 8080")
        await server.serve()
    except Exception as e:
        logger.error(f"API服务器启动失败: {e}")

# 创建后台任务启动API服务器
def create_api_server_task():
    """创建API服务器后台任务"""
    loop = asyncio.get_event_loop()
    if loop.is_running():
        loop.create_task(start_api_server())
    else:
        loop.run_until_complete(start_api_server())

# 导出API应用和启动函数供其他模块使用
export_api_app = api_app
export_start_api_server = start_api_server

def start_api():
    """启动API服务的简化函数"""
    import threading
    
    # 在单独的线程中启动API服务器，避免阻塞主事件循环
    api_thread = threading.Thread(target=create_api_server_task, daemon=True)
    api_thread.start()
    
    logger.info("API服务已在后台线程中启动")

# 模块加载时自动启动API服务
# 注意：在实际使用时，可能需要根据nonebot的启动流程调整启动时机
# start_api()  # 暂时注释，避免在导入模块时自动启动