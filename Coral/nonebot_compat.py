# nonebot_compat.py
import asyncio
import logging
from typing import Any, Callable, Dict, List, Optional, Tuple, Type, Union

from Coral.protocol import (
    MessageEvent as CoreMessageEvent, 
    NoticeEvent as CoreNoticeEvent, 
    CommandEvent as CoreCommandEvent, 
    MessageChain as CoreMessageChain, 
    MessageSegment as CoreMessageSegment,
    MessageRequest as CoreMessageRequest,
    GenericEvent,
    MessageRequest,
    MessageBase  # 新增导入
)
from Coral.event_bus import EventBus
from Coral.register import Register
from Coral.perm_system import PermSystem

logger = logging.getLogger(__name__)

class Bot:
    def __init__(self, adapter_name: str):
        self.self_id = "coral_bot"
        self.adapter = adapter_name
        self.config = {}
    
    async def send(self, event: Union[CoreMessageEvent, CoreNoticeEvent, CoreCommandEvent], message: Union[str, CoreMessageChain], **kwargs):
        if isinstance(message, str):
            message = CoreMessageChain([CoreMessageSegment.text(message)])
        
        return await EventBusManager.publish_message(
            event.platform,
            event.event_id,
            self.self_id,
            message,
            event.user,
            event.group if hasattr(event, 'group') else None
        )

class Event(MessageBase):  # 继承MessageBase
    def __init__(self, raw_event: Union[CoreMessageEvent, CoreNoticeEvent, CoreCommandEvent]):
        self.raw_event = raw_event
        self.time = raw_event.time
        self.self_id = raw_event.self_id
        self.post_type = ""
        
        if isinstance(raw_event, CoreMessageEvent):
            self.post_type = "message"
            self.message_type = "private" if raw_event.isprivate() else "group"
        elif isinstance(raw_event, CoreNoticeEvent):
            self.post_type = "notice"
        elif isinstance(raw_event, CoreCommandEvent):
            self.post_type = "command"

    def get_user_id(self) -> str:
        return self.raw_event.user.user_id if self.raw_event.user else ""
    
    def get_session_id(self) -> str:
        if hasattr(self.raw_event, 'group') and self.raw_event.group:
            return f"group_{self.raw_event.group.group_id}_{self.get_user_id()}"
        return f"private_{self.get_user_id()}"
    
    def get_message(self) -> CoreMessageChain:
        if isinstance(self.raw_event, CoreMessageEvent) and hasattr(self.raw_event, 'message'):
            return self.raw_event.message
        return CoreMessageChain()

class MessageEvent(Event, MessageBase):  # 双重继承
    def __init__(self, raw_event: CoreMessageEvent):
        super().__init__(raw_event)
        self.message = raw_event.message
        self.raw_message = raw_event.message.to_plain_text()
        self.user_id = raw_event.user.user_id
        self.group_id = raw_event.group.group_id if raw_event.group else None
        
    def is_tome(self) -> bool:
        return any(
            seg.type == "at" and isinstance(seg.data, Dict) and seg.data["user_id"] == self.self_id 
            for seg in self.message.segments
        )

class NoticeEvent(Event, MessageBase):  # 双重继承
    def __init__(self, raw_event: CoreNoticeEvent):
        super().__init__(raw_event)
        self.notice_type = raw_event.type
        self.user_id = raw_event.user.user_id if raw_event.user else None
        self.group_id = raw_event.group.group_id if raw_event.group else None

class CommandEvent(Event, MessageBase):  # 双重继承
    def __init__(self, raw_event: CoreCommandEvent):
        super().__init__(raw_event)
        self.command = raw_event.command
        self.args = raw_event.args
        self.user_id = raw_event.user.user_id
        self.group_id = raw_event.group.group_id if raw_event.group else None

class Message:
    def __init__(self, message: Union[str, CoreMessageChain, List[CoreMessageSegment]]):
        if isinstance(message, str):
            self.chain = CoreMessageChain([CoreMessageSegment.text(message)])
        elif isinstance(message, CoreMessageChain):
            self.chain = message
        elif isinstance(message, list):
            # 处理原始消息段转换
            self.chain = CoreMessageChain(segments=[
                seg if isinstance(seg, CoreMessageSegment) else CoreMessageSegment(**seg)
                for seg in message
            ])
        else:
            raise TypeError(f"Unsupported message type: {type(message)}")
    
    def __str__(self) -> str:
        return self.chain.to_plain_text()
    
    def __add__(self, other):
        if isinstance(other, Message):
            return Message(self.chain.segments + other.chain.segments)
        if isinstance(other, str):
            return Message(self.chain.segments + [CoreMessageSegment.text(other)])
        return NotImplemented
    
    def extract_plain_text(self) -> str:
        return self.chain.to_plain_text()

class MessageSegment:
    @staticmethod
    def text(text: str) -> CoreMessageSegment:
        return CoreMessageSegment.text(text)
    
    @staticmethod
    def image(file: str) -> CoreMessageSegment:
        return CoreMessageSegment.image(file)
    
    @staticmethod
    def at(user_id: str) -> CoreMessageSegment:
        return CoreMessageSegment.at(user_id)
    
    @staticmethod
    def face(id: str) -> CoreMessageSegment:
        return CoreMessageSegment.face(id)

class Matcher:
    handlers = []
    
    def __init__(self, type: str, handlers: List[Callable], priority: int = 5):
        self.type = type
        self.handlers = handlers
        self.priority = priority
    
    async def run(self, bot: Bot, event: Event):
        for handler in self.handlers:
            try:
                await handler(bot, event)
            except Exception as e:
                logger.error(f"Error in matcher handler: {e}")

class EventBusManager:
    event_bus: EventBus
    register: Register
    perm_system: PermSystem
    matchers: Dict[Type, List[Matcher]] = {}
    
    @classmethod
    def initialize(cls, event_bus: EventBus, register: Register, perm_system: PermSystem):
        cls.event_bus = event_bus
        cls.register = register
        cls.perm_system = perm_system
        
        event_bus.subscribe(CoreMessageEvent, cls.handle_message_event)
        event_bus.subscribe(CoreNoticeEvent, cls.handle_notice_event)
        event_bus.subscribe(CoreCommandEvent, cls.handle_command_event)
    
    @classmethod
    def register_matcher(cls, event_type: Type, matcher: Matcher):
        if event_type not in cls.matchers:
            cls.matchers[event_type] = []
        cls.matchers[event_type].append(matcher)
        cls.matchers[event_type].sort(key=lambda m: m.priority, reverse=True)
    
    @classmethod
    async def handle_message_event(cls, event: CoreMessageEvent):
        if not cls.event_bus or not cls.matchers:
            return
        
        bot = Bot(event.platform)
        nb_event = MessageEvent(event)
        
        for matcher in cls.matchers.get(MessageEvent, []):
            if matcher.type == "message":
                await matcher.run(bot, nb_event)
    
    @classmethod
    async def handle_notice_event(cls, event: CoreNoticeEvent):
        if not cls.event_bus or not cls.matchers:
            return
        
        bot = Bot(event.platform)
        nb_event = NoticeEvent(event)
        
        for matcher in cls.matchers.get(NoticeEvent, []):
            if matcher.type == "notice":
                await matcher.run(bot, nb_event)
    
    @classmethod
    async def handle_command_event(cls, event: CoreCommandEvent):
        if not cls.event_bus or not cls.matchers:
            return
        
        bot = Bot(event.platform)
        nb_event = CommandEvent(event)
        
        for matcher in cls.matchers.get(CommandEvent, []):
            if matcher.type == "command":
                await matcher.run(bot, nb_event)
    
    @classmethod
    async def publish_message(
        cls, 
        platform: str,
        event_id: str,
        self_id: str,
        message: CoreMessageChain,
        user: Any,
        group: Optional[Any] = None
    ):
        if not cls.event_bus:
            return
        
        msg_request = CoreMessageRequest(
            platform=platform,
            event_id=event_id,
            self_id=self_id,
            message=message,
            user=user,
            group=group
        )
        await cls.event_bus.publish(msg_request)

def on_message(priority: int = 5) -> Callable:
    def decorator(func: Callable) -> Callable:
        matcher = Matcher("message", [func], priority)
        EventBusManager.register_matcher(MessageEvent, matcher)
        return func
    return decorator

def on_notice(priority: int = 5) -> Callable:
    def decorator(func: Callable) -> Callable:
        matcher = Matcher("notice", [func], priority)
        EventBusManager.register_matcher(NoticeEvent, matcher)
        return func
    return decorator

def on_command(
    cmd: Union[str, Tuple[str, ...]], 
    aliases: Optional[set] = None, 
    priority: int = 5
) -> Callable:
    if not isinstance(cmd, tuple):
        cmd = (cmd,)
    
    aliases = aliases or set()
    all_cmds = set(cmd) | aliases
    
    def decorator(func: Callable) -> Callable:
        async def command_handler(bot: Bot, event: MessageEvent):
            msg_text = event.message.to_plain_text().strip()
            for c in all_cmds:
                if msg_text.startswith(c):
                    # 创建正确的CommandEvent
                    event.raw_event = CoreCommandEvent(
                        event_id=event.raw_event.event_id,
                        platform=event.raw_event.platform,
                        self_id=event.raw_event.self_id,
                        command=c,
                        raw_message=event.raw_event.message,
                        user=event.raw_event.user,
                        group=event.raw_event.group,
                        args=msg_text[len(c):].strip().split()
                    )
                    await func(bot, event)
                    return
        
        matcher = Matcher("command", [command_handler], priority)
        EventBusManager.register_matcher(MessageEvent, matcher)
        return func
    return decorator

def on_startup(func: Callable) -> Callable:
    async def startup_handler():
        await func()
    
    EventBusManager.event_bus.subscribe(
        GenericEvent, 
        lambda e: startup_handler() if e.name == "coral_initialized" else None,
        priority=10
    )
    return func

def on_shutdown(func: Callable) -> Callable:
    async def shutdown_handler():
        await func()
    
    EventBusManager.event_bus.subscribe(
        GenericEvent, 
        lambda e: shutdown_handler() if e.name == "coral_shutdown" else None,
        priority=10
    )
    return func

def get_driver() -> Any:
    class Driver:
        @property
        def config(self):
            return {}
    
    return Driver()

def permission_control(perm: Union[str, List[str]]) -> Callable:
    def decorator(func: Callable) -> Callable:
        async def wrapper(bot: Bot, event: Event):
            user_id = event.get_user_id()
            group_id = getattr(event, 'group_id', None) or -1
            
            # 检查权限系统是否存在
            if EventBusManager.perm_system and EventBusManager.perm_system.check_perm(
                perm, user_id, group_id
            ):
                return await func(bot, event)
            else:
                logger.warning(f"User {user_id} lacks permission: {perm}")
                if isinstance(event, MessageEvent):
                    await bot.send(event.raw_event, "权限不足")  # 传递kwargs
        
        return wrapper
    return decorator

def rule_checker(func: Callable) -> Callable:
    def decorator(handler: Callable) -> Callable:
        async def wrapper(bot: Bot, event: Event):
            if await func(bot, event):
                return await handler(bot, event)
        return wrapper
    return decorator

def to_me() -> Callable:
    @rule_checker
    async def checker(bot: Bot, event: MessageEvent):
        return event.is_tome()
    return checker

def MessageTemplate(template: str) -> Message:
    return Message(template)

def init_nonebot_compat(event_bus: EventBus, register: Register, perm_system: PermSystem):
    EventBusManager.initialize(event_bus, register, perm_system)
    logger.info("NoneBot2 compatibility layer initialized")