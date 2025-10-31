from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional, Union, Dict, Any
import time
from .message import MessageBase, MessageChain, MessageSegment, UserInfo, GroupInfo
from .response import BotResponse, MessageRequest, ActionRequest
from .event import Event
from .types import ActionType


@dataclass
class Bot:
    """机器人对象，代表一个平台连接"""
    
    platform: str  # 平台名称
    self_id: str   # 机器人ID
    adapter: Any = None  # 关联的适配器
    config: Dict[str, Any] = field(default_factory=dict)  # 机器人配置
    
    async def send_message(
        self, 
        message: Union[str, MessageChain], 
        user: Optional[UserInfo] = None,
        group: Optional[GroupInfo] = None,
        at_sender: bool = False
    ) -> Optional[BotResponse]:
        """发送消息"""
        if isinstance(message, str):
            message = MessageChain([MessageSegment.text(message)])
        
        msg_request = MessageRequest(
            platform=self.platform,
            event_id="",  # 新消息没有关联事件
            self_id=self.self_id,
            message=message,
            user=user,
            group=group,
            at_sender=at_sender
        )
        
        if self.adapter:
            return await self.adapter.handle_outgoing_message(msg_request)
        return None
    
    async def send_action(self, action_type: ActionType, target: Union[UserInfo, GroupInfo], **kwargs) -> Optional[BotResponse]:
        """发送动作请求"""
        action_request = ActionRequest(
            platform=self.platform,
            self_id=self.self_id,
            type=action_type,
            target=target,
            data=kwargs
        )
        
        if self.adapter:
            return await self.adapter.handle_outgoing_action(action_request)
        return None