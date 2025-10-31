from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional, Union, Dict, Any
import time
from .message import MessageBase, MessageChain, UserInfo, GroupInfo
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