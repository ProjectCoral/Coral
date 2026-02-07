from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional, Union, Dict, Any
from .message import MessageBase, MessageChain, MessageSegment, UserInfo, GroupInfo
from .response import BotResponse, MessageRequest, ActionRequest
from .event import Event
from .types import ActionType


class MessageSender:
    """消息发送器，支持链式调用"""
    
    def __init__(self, bot: "Bot", user: Optional[UserInfo] = None, group: Optional[GroupInfo] = None):
        self.bot = bot
        self.user = user
        self.group = group
        self.at_sender = False
        self.recall_duration: Optional[int] = None
    
    def to_user(self, user_id: str, platform: Optional[str] = None) -> "MessageSender":
        """发送给指定用户"""
        platform = platform or self.bot.platform
        self.user = UserInfo(platform=platform, user_id=user_id)
        self.group = None
        return self
    
    def to_group(self, group_id: str, platform: Optional[str] = None) -> "MessageSender":
        """发送到指定群组"""
        platform = platform or self.bot.platform
        self.group = GroupInfo(platform=platform, group_id=group_id)
        self.user = None
        return self
    
    def at_sender(self, at_sender: bool = True) -> "MessageSender":
        """是否@发送者"""
        self.at_sender = at_sender
        return self
    
    def recall_after(self, seconds: int) -> "MessageSender":
        """设置自动撤回时间"""
        self.recall_duration = seconds
        return self
    
    async def send(self, message: Union[str, MessageChain]) -> Optional[BotResponse]:
        """发送消息"""
        if isinstance(message, str):
            message = MessageChain([MessageSegment.text(message)])
        
        msg_request = MessageRequest(
            platform=self.bot.platform,
            event_id="",  # 新消息没有关联事件
            self_id=self.bot.self_id,
            message=message,
            user=self.user,
            group=self.group,
            at_sender=self.at_sender,
            recall_duration=self.recall_duration
        )
        
        if self.bot.adapter:
            return await self.bot.adapter.handle_outgoing_message(msg_request)
        return None


@dataclass
class Bot:
    """机器人对象，代表一个平台连接"""
    
    platform: str  # 平台名称
    self_id: str   # 机器人ID
    adapter: Any = None  # 关联的适配器
    config: Dict[str, Any] = field(default_factory=dict)  # 机器人配置
    
    def to_user(self, user_id: str, platform: Optional[str] = None) -> MessageSender:
        """发送给指定用户（链式调用起点）"""
        return MessageSender(self).to_user(user_id, platform)
    
    def to_group(self, group_id: str, platform: Optional[str] = None) -> MessageSender:
        """发送到指定群组（链式调用起点）"""
        return MessageSender(self).to_group(group_id, platform)
    
    async def send_message(
        self, 
        message: Union[str, MessageChain], 
        user: Optional[UserInfo] = None,
        group: Optional[GroupInfo] = None,
        at_sender: bool = False
    ) -> Optional[BotResponse]:
        """发送消息（传统方式）"""
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