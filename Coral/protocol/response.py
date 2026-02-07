from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional, Union
import time
from .message import MessageBase, MessageChain, UserInfo, GroupInfo, MessageSegment
from .event import Event
from .types import ActionType


@dataclass
class BotResponse(Event, MessageBase):
    """机器人响应"""

    success: bool = True  # 是否成功
    message: Optional[str] = None  # 响应消息
    data: Optional[dict] = None  # 响应数据
    event_id: Optional[str] = None  # 关联的事件ID
    platform: str = ""
    self_id: str = ""
    time: float = field(default_factory=time.time)


@dataclass
class MessageRequest(Event, MessageBase):
    """回复消息结构"""

    platform: str  # 平台名称
    event_id: str  # 回复的事件ID
    self_id: str  # 机器人自身ID
    message: MessageChain  # 回复内容
    time: float = field(default_factory=time.time)
    user: Optional[UserInfo] = None  # 接收者信息
    group: Optional[GroupInfo] = None  # 群组信息
    at_sender: bool = False  # 是否@发送者
    recall_duration: Optional[int] = None  # 自动撤回时间（秒）

    @classmethod
    def builder(cls, event: Optional[Event] = None) -> "MessageRequestBuilder":
        """创建构建器"""
        return MessageRequestBuilder(event)


class MessageRequestBuilder:
    """MessageRequest构建器，支持链式调用"""
    
    def __init__(self, event: Optional[Event] = None):
        self.platform = ""
        self.event_id = ""
        self.self_id = ""
        self.message = MessageChain()
        self.user: Optional[UserInfo] = None
        self.group: Optional[GroupInfo] = None
        self.at_sender = False
        self.recall_duration: Optional[int] = None
        
        if event:
            self.platform = event.platform
            self.self_id = event.self_id
            if hasattr(event, 'event_id'):
                self.event_id = event.event_id
            if hasattr(event, 'user'):
                self.user = event.user
            if hasattr(event, 'group'):
                self.group = event.group
    
    def set_platform(self, platform: str) -> "MessageRequestBuilder":
        """设置平台"""
        self.platform = platform
        return self
    
    def set_event_id(self, event_id: str) -> "MessageRequestBuilder":
        """设置事件ID"""
        self.event_id = event_id
        return self
    
    def set_self_id(self, self_id: str) -> "MessageRequestBuilder":
        """设置机器人ID"""
        self.self_id = self_id
        return self
    
    def text(self, text: str) -> "MessageRequestBuilder":
        """添加文本消息"""
        self.message.append(MessageSegment.text(text))
        return self
    
    def image(self, url: str, width: Optional[int] = None, height: Optional[int] = None) -> "MessageRequestBuilder":
        """添加图片消息"""
        self.message.append(MessageSegment.image(url, width, height))
        return self
    
    def at(self, user_id: str) -> "MessageRequestBuilder":
        """添加@消息"""
        self.message.append(MessageSegment.at(user_id))
        return self
    
    def face(self, face_id: str) -> "MessageRequestBuilder":
        """添加表情消息"""
        self.message.append(MessageSegment.face(face_id))
        return self
    
    def message_chain(self, message: MessageChain) -> "MessageRequestBuilder":
        """设置消息链"""
        self.message = message
        return self
    
    def set_user(self, user: UserInfo) -> "MessageRequestBuilder":
        """设置接收用户"""
        self.user = user
        return self
    
    def set_group(self, group: GroupInfo) -> "MessageRequestBuilder":
        """设置接收群组"""
        self.group = group
        return self
    
    def set_at_sender(self, at_sender: bool = True) -> "MessageRequestBuilder":
        """设置是否@发送者"""
        self.at_sender = at_sender
        return self
    
    def recall_after(self, seconds: int) -> "MessageRequestBuilder":
        """设置自动撤回时间"""
        self.recall_duration = seconds
        return self
    
    def build(self) -> MessageRequest:
        """构建MessageRequest对象"""
        return MessageRequest(
            platform=self.platform,
            event_id=self.event_id,
            self_id=self.self_id,
            message=self.message,
            user=self.user,
            group=self.group,
            at_sender=self.at_sender,
            recall_duration=self.recall_duration
        )


@dataclass
class ActionRequest(Event, MessageBase):
    """主动动作请求"""

    platform: str  # 平台名称
    self_id: str  # 机器人自身ID
    type: ActionType  # 动作类型
    target: Union[UserInfo, GroupInfo]  # 目标对象
    data: dict  # 动作数据
    time: float = field(default_factory=time.time)
    group: Optional[GroupInfo] = None  # 群组信息
    delay: Optional[float] = None  # 延迟执行时间（秒）