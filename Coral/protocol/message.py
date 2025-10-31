from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional, Union, List, Dict, Any


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
        return "".join(seg.data for seg in self.segments if seg.type == "text" and isinstance(seg.data, str))