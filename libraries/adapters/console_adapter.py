# [file name]: adapters/console_adapter.py
import time
import logging
from typing import Any, Dict
from core.adapter import BaseAdapter
from core.driver import BaseDriver
from core.protocol import MessageEvent, CommandEvent, MessageChain, MessageSegment, UserInfo, MessageRequest, ActionRequest, GenericEvent

logger = logging.getLogger(__name__)

PROTOCOL = "console"

class ConsoleAdapter(BaseAdapter):
    """控制台适配器 - 处理控制台消息转换"""
    
    def __init__(self, config: Dict[str, Any] = {}):
        super().__init__(config)
    
    async def handle_incoming(self, raw_data: Dict[str, Any]):
        """处理控制台输入"""
        text = raw_data.get("text", "").strip()
        if not text:
            return
        
        logger.debug(f"Received message: {text}")
        
        # 转换为命令事件
        command, *args = text.split(" ", 1)
        # args = args[0] if args else ""
        args = args[0].split() if args else [] # 将参数转换为列表
        
        event = CommandEvent(
            event_id=f"console-{time.time()}",
            platform="console",
            self_id="Console",
            command=command,
            raw_message=MessageChain([MessageSegment.text(text)]),
            user=UserInfo(
                platform="system",
                user_id="Console"
            ),
            args=args if args else []
        )
        
        await self.publish_event(event)
    
    def convert_to_protocol(self, event: Any):
        """控制台事件转换 (不需要转换)"""
        return event
    
    async def handle_outgoing_message(self, message: MessageRequest):
        """处理消息回复到控制台"""
        # 将消息内容输出到控制台
        plain_text = message.message.to_plain_text()
        await self.send_to_driver({
            "type": "message",
            "message": plain_text
        })
    
    async def handle_outgoing_action(self, action: ActionRequest):
        """处理主动动作 (控制台暂不需要)"""
        logger.warning(f"Unsupported action for console: {action.type}")