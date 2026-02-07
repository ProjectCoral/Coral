from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional, Union, List, Dict, Any
from enum import Enum


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


class ShareType(Enum):
    """分享类型枚举"""
    WEBSITE = "website"
    MUSIC = "music"
    VIDEO = "video"
    LOCATION = "location"


@dataclass
class Share(MessageBase):
    """分享数据类
    
    根据type字段的不同，其他字段的含义也不同：
    - website: name, url
    - music: name, platform, id
    - video: name, url
    - location: lon, lat, alt
    """
    type: str  # 分享类型
    name: Optional[str] = None  # 名称（website/music/video使用）
    url: Optional[str] = None   # 链接（website/video使用）
    platform: Optional[str] = None  # 平台（music使用）
    id: Optional[str] = None    # ID（music使用）
    lon: Optional[float] = None  # 经度（location使用）
    lat: Optional[float] = None  # 纬度（location使用）
    alt: Optional[float] = None  # 海拔（location使用，可选）


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

    @staticmethod
    def video(url: str) -> MessageSegment:
        """创建视频消息段"""
        return MessageSegment(type="video", data={"url": url})

    @staticmethod
    def audio(url: str, record: bool = False) -> MessageSegment:
        """创建音频消息段
        
        Args:
            url: 音频URL
            record: 是否为录音（用于onebot适配器适配）
        """
        return MessageSegment(type="audio", data={"url": url, "record": record})

    @staticmethod
    def share(share_obj: Union[Share, Dict[str, Any]]) -> MessageSegment:
        """创建分享消息段
        
        Args:
            share_obj: Share对象或字典
        """
        if isinstance(share_obj, dict):
            share_data = Share(**share_obj)
        else:
            share_data = share_obj
        
        return MessageSegment(type="share", data=share_data.to_dict())

    @staticmethod
    def share_website(name: str, url: str) -> MessageSegment:
        """创建网站分享消息段"""
        return MessageSegment.share(Share(
            type=ShareType.WEBSITE.value,
            name=name,
            url=url
        ))

    @staticmethod
    def share_music(name: str, platform: str, id: str) -> MessageSegment:
        """创建音乐分享消息段
        
        Args:
            name: 音乐名称
            platform: 平台 (qq, 163, xm)
            id: 音乐ID
        """
        return MessageSegment.share(Share(
            type=ShareType.MUSIC.value,
            name=name,
            platform=platform,
            id=id
        ))

    @staticmethod
    def share_video(name: str, url: str) -> MessageSegment:
        """创建视频分享消息段"""
        return MessageSegment.share(Share(
            type=ShareType.VIDEO.value,
            name=name,
            url=url
        ))

    @staticmethod
    def share_location(lon: float, lat: float, alt: Optional[float] = None) -> MessageSegment:
        """创建位置分享消息段"""
        return MessageSegment.share(Share(
            type=ShareType.LOCATION.value,
            lon=lon,
            lat=lat,
            alt=alt
        ))


@dataclass
class MessageChain(MessageBase):
    """消息链 - 包含多个消息段"""

    segments: List[MessageSegment] = field(default_factory=list)

    @classmethod
    def text(cls, content: str) -> "MessageChain":
        """创建文本消息链"""
        return cls([MessageSegment.text(content)])

    @classmethod
    def image(cls, url: str, width: Optional[int] = None, height: Optional[int] = None) -> "MessageChain":
        """创建图片消息链"""
        return cls([MessageSegment.image(url, width, height)])

    @classmethod
    def at(cls, user_id: str) -> "MessageChain":
        """创建@用户消息链"""
        return cls([MessageSegment.at(user_id)])

    @classmethod
    def face(cls, face_id: str) -> "MessageChain":
        """创建表情消息链"""
        return cls([MessageSegment.face(face_id)])

    def append(self, segment: MessageSegment) -> None:
        """添加消息段"""
        self.segments.append(segment)

    def extend(self, segments: List[MessageSegment]) -> None:
        """扩展消息段列表"""
        self.segments.extend(segments)

    def add_text(self, content: str) -> "MessageChain":
        """添加文本消息段（链式调用）"""
        self.segments.append(MessageSegment.text(content))
        return self

    def add_image(self, url: str, width: Optional[int] = None, height: Optional[int] = None) -> "MessageChain":
        """添加图片消息段（链式调用）"""
        self.segments.append(MessageSegment.image(url, width, height))
        return self

    def add_at(self, user_id: str) -> "MessageChain":
        """添加@用户消息段（链式调用）"""
        self.segments.append(MessageSegment.at(user_id))
        return self

    def add_face(self, face_id: str) -> "MessageChain":
        """添加表情消息段（链式调用）"""
        self.segments.append(MessageSegment.face(face_id))
        return self

    def add_video(self, url: str) -> "MessageChain":
        """添加视频消息段（链式调用）"""
        self.segments.append(MessageSegment.video(url))
        return self

    def add_audio(self, url: str, record: bool = False) -> "MessageChain":
        """添加音频消息段（链式调用）"""
        self.segments.append(MessageSegment.audio(url, record))
        return self

    def add_share(self, share_obj: Union[Share, Dict[str, Any]]) -> "MessageChain":
        """添加分享消息段（链式调用）"""
        self.segments.append(MessageSegment.share(share_obj))
        return self

    def add_share_website(self, name: str, url: str) -> "MessageChain":
        """添加网站分享消息段（链式调用）"""
        self.segments.append(MessageSegment.share_website(name, url))
        return self

    def add_share_music(self, name: str, platform: str, id: str) -> "MessageChain":
        """添加音乐分享消息段（链式调用）"""
        self.segments.append(MessageSegment.share_music(name, platform, id))
        return self

    def add_share_video(self, name: str, url: str) -> "MessageChain":
        """添加视频分享消息段（链式调用）"""
        self.segments.append(MessageSegment.share_video(name, url))
        return self

    def add_share_location(self, lon: float, lat: float, alt: Optional[float] = None) -> "MessageChain":
        """添加位置分享消息段（链式调用）"""
        self.segments.append(MessageSegment.share_location(lon, lat, alt))
        return self

    @classmethod
    def video(cls, url: str) -> "MessageChain":
        """创建视频消息链"""
        return cls([MessageSegment.video(url)])

    @classmethod
    def audio(cls, url: str, record: bool = False) -> "MessageChain":
        """创建音频消息链"""
        return cls([MessageSegment.audio(url, record)])

    @classmethod
    def share(cls, share_obj: Union[Share, Dict[str, Any]]) -> "MessageChain":
        """创建分享消息链"""
        return cls([MessageSegment.share(share_obj)])

    @classmethod
    def share_website(cls, name: str, url: str) -> "MessageChain":
        """创建网站分享消息链"""
        return cls([MessageSegment.share_website(name, url)])

    @classmethod
    def share_music(cls, name: str, platform: str, id: str) -> "MessageChain":
        """创建音乐分享消息链"""
        return cls([MessageSegment.share_music(name, platform, id)])

    @classmethod
    def share_video(cls, name: str, url: str) -> "MessageChain":
        """创建视频分享消息链"""
        return cls([MessageSegment.share_video(name, url)])

    @classmethod
    def share_location(cls, lon: float, lat: float, alt: Optional[float] = None) -> "MessageChain":
        """创建位置分享消息链"""
        return cls([MessageSegment.share_location(lon, lat, alt)])

    def to_plain_text(self) -> str:
        """转换为纯文本（忽略非文本消息段和头尾空格）"""
        return "".join(seg.data for seg in self.segments if seg.type == "text" and isinstance(seg.data, str)).strip()
