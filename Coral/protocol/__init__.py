from .message import MessageBase, UserInfo, GroupInfo, MessageSegment, MessageChain
from .event import Event, MessageEvent, NoticeEvent, CommandEvent, GenericEvent
from .response import BotResponse, MessageRequest, ActionRequest
from .bot import Bot
from .types import EventType, ActionType

__all__ = [
    "MessageBase",
    "UserInfo", 
    "GroupInfo",
    "MessageSegment",
    "MessageChain",
    "Event",
    "MessageEvent",
    "NoticeEvent",
    "CommandEvent",
    "GenericEvent",
    "BotResponse",
    "MessageRequest",
    "ActionRequest",
    "Bot",
    "EventType",
    "ActionType",
    "PROTOCOL_VERSION"
]

PROTOCOL_VERSION = "1.1.0"  # 协议版本