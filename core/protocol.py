from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional, Union, List, Dict, Any
import time

PROTOCOL_VERSION = "1.0.1"  # 协议版本


@dataclass
class MessageBase:
    """消息基类，提供通用转换方法"""

    @classmethod
    def from_dict(cls, data: dict) -> MessageBase:
        """从字典创建消息对象"""
        return cls(**data)

    def to_dict(self) -> dict:
        """将消息对象转换为字典"""
        return self.__dict__


class Event:
    """所有事件的基类"""

    platform: str
    self_id: str
    time: float = field(default_factory=time.time)


@dataclass
class UserInfo(MessageBase):
    """用户信息"""

    platform: str  # 平台名称 (如: qq, wechat, discord)
    user_id: str  # 用户ID
    nickname: Optional[str] = None  # 用户昵称
    cardname: Optional[str] = None  # 用户群名片
    avatar: Optional[str] = None  # 头像URL
    roles: List[str] = field(default_factory=list)  # 用户角色/权限


@dataclass
class GroupInfo(MessageBase):
    """群组信息"""

    platform: str  # 平台名称
    group_id: str  # 群组ID
    name: Optional[str] = None  # 群名称
    owner_id: Optional[str] = None  # 群主ID
    member_count: Optional[int] = None  # 成员数量


@dataclass
class MessageSegment(MessageBase):
    """消息段 - 支持富文本内容"""

    type: str  # 消息段类型 (text, image, at, emoji, etc.)
    data: Union[str, Dict[str, Any]]  # 消息内容或附加数据

    @staticmethod
    def text(content: str) -> MessageSegment:
        """创建文本消息段"""
        return MessageSegment(type="text", data=content)

    @staticmethod
    def image(
        url: str, width: Optional[int] = None, height: Optional[int] = None
    ) -> MessageSegment:
        """创建图片消息段"""
        return MessageSegment(
            type="image", data={"url": url, "width": width, "height": height}
        )

    @staticmethod
    def at(user_id: str) -> MessageSegment:
        """创建@用户消息段"""
        return MessageSegment(type="at", data={"user_id": user_id})

    @staticmethod
    def face(id: str) -> MessageSegment:
        """创建表情消息段"""
        return MessageSegment(type="face", data={"id": id})


@dataclass
class MessageChain(MessageBase):
    """消息链 - 包含多个消息段"""

    segments: List[MessageSegment] = field(default_factory=list)

    def append(self, segment: MessageSegment) -> None:
        """添加消息段"""
        self.segments.append(segment)

    def extend(self, segments: List[MessageSegment]) -> None:
        """扩展消息段列表"""
        self.segments.extend(segments)

    def to_plain_text(self) -> str:
        """转换为纯文本（忽略非文本消息段）"""
        return "".join(seg.data for seg in self.segments if seg.type == "text")


@dataclass
class MessageEvent(Event, MessageBase):
    """消息事件 - 用户发送的消息"""

    event_id: str  # 事件唯一ID
    platform: str  # 平台名称
    self_id: str  # 机器人自身ID
    message: MessageChain  # 消息内容
    user: UserInfo  # 发送者信息
    group: Optional[GroupInfo] = None  # 群组信息（私聊时为None）
    raw: Optional[dict] = None  # 原始平台消息数据
    time: float = field(default_factory=time.time)  # 时间戳

    def isprivate(self) -> bool:
        """判断是否为私聊事件"""
        return self.group is None

    def isgroup(self) -> bool:
        return self.group is not None

    def ismetentioned(self) -> bool:
        """判断是否被@"""
        return any(
            seg.type == "at" and seg.data["user_id"] == str(self.self_id)
            for seg in self.message.segments
        )


@dataclass
class NoticeEvent(Event, MessageBase):
    """通知事件 - 系统通知"""

    event_id: str  # 事件唯一ID
    platform: str  # 平台名称
    type: str  # 通知类型 (group_increase, group_decrease, friend_add, etc.)
    self_id: str  # 机器人自身ID
    user: Optional[UserInfo] = None  # 相关用户信息
    group: Optional[GroupInfo] = None  # 相关群组信息
    operator: Optional[UserInfo] = None  # 操作者信息
    target: Optional[UserInfo] = None  # 目标用户信息
    comment: Optional[str] = None  # 附加说明
    raw: Optional[dict] = None  # 原始平台通知数据
    time: float = field(default_factory=time.time)  # 时间戳

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

    event_id: str  # 事件唯一ID
    platform: str  # 平台名称
    self_id: str  # 机器人自身ID
    command: str  # 命令名称
    raw_message: MessageChain  # 原始消息内容
    user: UserInfo  # 发送者信息
    group: Optional[GroupInfo] = None  # 群组信息
    args: List[str] = field(default_factory=list)  # 命令参数
    time: float = field(default_factory=time.time)  # 时间戳

    def isprivate(self) -> bool:
        """判断是否为私聊事件"""
        return self.group is None

    def isgroup(self) -> bool:
        return self.group is not None


@dataclass
class BotResponse(MessageBase):
    """机器人响应"""

    success: bool  # 是否成功
    message: Optional[str] = None  # 响应消息
    data: Optional[dict] = None  # 响应数据
    event_id: Optional[str] = None  # 关联的事件ID


@dataclass
class MessageRequest(MessageBase):
    """回复消息结构"""

    platform: str  # 平台名称
    event_id: str  # 回复的事件ID
    self_id: str  # 机器人自身ID
    message: MessageChain  # 回复内容
    user: Optional[UserInfo] = None  # 接收者信息
    group: Optional[GroupInfo] = None  # 群组信息
    at_sender: bool = False  # 是否@发送者
    recall_duration: Optional[int] = None  # 自动撤回时间（秒）


@dataclass
class ActionRequest(MessageBase):
    """主动动作请求"""

    platform: str  # 平台名称
    self_id: str  # 机器人自身ID
    type: str  # 动作类型 (send_message, delete_message, kick_member, etc.)
    target: Union[UserInfo, GroupInfo]  # 目标对象
    data: dict  # 动作数据
    group: Optional[GroupInfo] = None  # 群组信息
    delay: Optional[float] = None  # 延迟执行时间（秒）


@dataclass
class GenericEvent(Event):
    """通用事件类型，用于旧系统兼容"""

    platform: str  # 平台名称
    name: str  # 事件名称
    data: Optional[dict] = None  # 事件数据
