from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional, Union, List, Dict, Any, TYPE_CHECKING
import time
from .message import MessageBase, MessageChain, UserInfo, GroupInfo, MessageSegment
from .types import EventType

if TYPE_CHECKING:
    from .response import MessageRequest


@dataclass
class Event:
    """所有事件的基类"""

    platform: str
    self_id: str


@dataclass
class MessageEvent(Event, MessageBase):
    """消息事件 - 用户发送的消息"""

    platform: str  # 平台名称
    self_id: str  # 机器人自身ID
    event_id: str  # 事件唯一ID
    message: MessageChain = field(default_factory=MessageChain)  # 消息内容
    user: UserInfo = field(default_factory=lambda: UserInfo("", ""))  # 发送者信息
    time: float = field(default_factory=time.time)  # 时间戳
    group: Optional[GroupInfo] = None  # 群组信息（私聊时为None）
    raw: Optional[dict] = None  # 原始平台消息数据

    def is_private(self) -> bool:
        """判断是否为私聊事件"""
        return self.group is None

    def is_group(self) -> bool:
        return self.group is not None

    def to_me(self) -> bool:
        """判断是否被@"""
        return any(
            seg.type == "at" and isinstance(seg.data, dict) and seg.data["user_id"] == str(self.self_id)
            for seg in self.message.segments
        )

    def reply(
        self,
        message: Union[str, MessageChain],
        at_sender: bool = False,
        recall_duration: Optional[int] = None
    ) -> "MessageRequest":
        """便捷回复方法
        
        Args:
            message: 回复消息内容，可以是字符串或MessageChain
            at_sender: 是否@发送者
            recall_duration: 自动撤回时间（秒）
        
        Returns:
            MessageRequest: 构建好的消息请求
        """
        if isinstance(message, str):
            message = MessageChain([MessageSegment.text(message)])
        
        # 延迟导入以避免循环导入
        from .response import MessageRequest
        
        return MessageRequest(
            platform=self.platform,
            event_id=self.event_id,
            self_id=self.self_id,
            message=message,
            user=self.user,
            group=self.group,
            at_sender=at_sender,
            recall_duration=recall_duration
        )


@dataclass
class NoticeEvent(Event, MessageBase):
    """通知事件 - 系统通知事件"""

    platform: str   # 平台名称
    self_id: str  # 机器人自身ID
    event_id: str   # 事件唯一ID
    type: EventType  # 通知类型
    time: float = field(default_factory=time.time)  # 时间戳
    user: Optional[UserInfo] = None  # 相关用户信息
    group: Optional[GroupInfo] = None  # 相关群组信息
    operator: Optional[UserInfo] = None  # 操作者信息
    target: Optional[UserInfo] = None  # 目标用户信息
    comment: Optional[str] = None  # 附加说明
    raw: Optional[dict] = None  # 原始平台通知数据

    def is_private(self) -> bool:
        """判断是否为私聊事件"""
        return self.group is None

    def is_group(self) -> bool:
        return self.group is not None

    def to_me(self) -> bool:
        """判断target是否为自身"""
        return self.target is not None and self.target.user_id == self.self_id

    def is_operator(self) -> bool:
        """判断operator是否为自身"""
        return self.operator is not None and self.operator.user_id == self.self_id

    def reply(
        self,
        message: Union[str, MessageChain],
        at_sender: bool = False,
        recall_duration: Optional[int] = None
    ) -> "MessageRequest":
        """便捷回复方法
        
        Args:
            message: 回复消息内容，可以是字符串或MessageChain
            at_sender: 是否@发送者
            recall_duration: 自动撤回时间（秒）
        
        Returns:
            MessageRequest: 构建好的消息请求
        """
        if isinstance(message, str):
            message = MessageChain([MessageSegment.text(message)])
        
        # 延迟导入以避免循环导入
        from .response import MessageRequest
        
        # 对于NoticeEvent，user可能为None，需要处理
        reply_user = self.user
        if reply_user is None and self.target is not None:
            # 如果没有user但有target，使用target作为接收者
            reply_user = self.target
        
        return MessageRequest(
            platform=self.platform,
            event_id=self.event_id,
            self_id=self.self_id,
            message=message,
            user=reply_user,
            group=self.group,
            at_sender=at_sender,
            recall_duration=recall_duration
        )


@dataclass
class CommandEvent(Event, MessageBase):
    """命令事件 - 用户执行的命令"""

    platform: str  # 平台名称
    self_id: str  # 机器人自身ID
    event_id: str  # 事件唯一ID
    command: str  # 命令名称
    raw_message: MessageChain = field(default_factory=MessageChain)  # 原始消息内容
    user: UserInfo = field(default_factory=lambda: UserInfo("", ""))  # 发送者信息
    time: float = field(default_factory=time.time)  # 时间戳
    group: Optional[GroupInfo] = None  # 群组信息
    args: List[str] = field(default_factory=list)  # 命令参数

    def is_private(self) -> bool:
        """判断是否为私聊事件"""
        return self.group is None

    def is_group(self) -> bool:
        return self.group is not None

    def reply(
        self,
        message: Union[str, MessageChain],
        at_sender: bool = False,
        recall_duration: Optional[int] = None
    ) -> "MessageRequest":
        """便捷回复方法
        
        Args:
            message: 回复消息内容，可以是字符串或MessageChain
            at_sender: 是否@发送者
            recall_duration: 自动撤回时间（秒）
        
        Returns:
            MessageRequest: 构建好的消息请求
        """
        if isinstance(message, str):
            message = MessageChain([MessageSegment.text(message)])
        
        # 延迟导入以避免循环导入
        from .response import MessageRequest
        
        return MessageRequest(
            platform=self.platform,
            event_id=self.event_id,
            self_id=self.self_id,
            message=message,
            user=self.user,
            group=self.group,
            at_sender=at_sender,
            recall_duration=recall_duration
        )


@dataclass
class GenericEvent(Event):
    """通用事件类型，用于旧系统兼容"""

    platform: str  # 平台名称
    name: str = ""  # 事件名称
    self_id: str = "Coral"  # 机器人自身ID
    data: Optional[dict] = None  # 事件数据