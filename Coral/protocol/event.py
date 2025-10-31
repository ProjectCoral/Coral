from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional, Union, List, Dict, Any
import time
from .message import MessageBase, MessageChain, UserInfo, GroupInfo
from .types import EventType


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

    def isprivate(self) -> bool:
        """判断是否为私聊事件"""
        return self.group is None

    def isgroup(self) -> bool:
        return self.group is not None

    def ismetentioned(self) -> bool:
        """判断是否被@"""
        return any(
            seg.type == "at" and isinstance(seg.data, dict) and seg.data["user_id"] == str(self.self_id)
            for seg in self.message.segments
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

    def isprivate(self) -> bool:
        """判断是否为私聊事件"""
        return self.group is None

    def isgroup(self) -> bool:
        return self.group is not None

    def ismetentioned(self) -> bool:
        """判断target是否为自身"""
        return self.target is not None and self.target.user_id == self.self_id

    def isoperator(self) -> bool:
        """判断operator是否为自身"""
        return self.operator is not None and self.operator.user_id == self.self_id


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

    def isprivate(self) -> bool:
        """判断是否为私聊事件"""
        return self.group is None

    def isgroup(self) -> bool:
        return self.group is not None


@dataclass
class GenericEvent(Event):
    """通用事件类型，用于旧系统兼容"""

    platform: str  # 平台名称
    name: str = ""  # 事件名称
    self_id: str = "Coral"  # 机器人自身ID
    data: Optional[dict] = None  # 事件数据