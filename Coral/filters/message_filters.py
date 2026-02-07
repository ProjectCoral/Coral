"""
消息事件过滤器模块
包含所有 MessageEvent 相关的过滤器和复合过滤器
"""
import time
import re
from typing import Union, List, Optional, Dict, Any, Callable, Type
from collections import defaultdict

from .base import MessageFilter, CompositeFilter, EventFilter
from ..protocol import MessageEvent, UserInfo, GroupInfo
from ..perm_system import PermSystem


class AndFilter(CompositeFilter):
    """逻辑与过滤器"""
    
    def __init__(self, *filters: EventFilter):
        super().__init__(*filters)
    
    async def check(self, event: Any) -> bool:
        for filter_obj in self.filters:
            if not await filter_obj.check_with_warning(event):
                return False
        return True


class OrFilter(CompositeFilter):
    """逻辑或过滤器"""
    
    def __init__(self, *filters: EventFilter):
        super().__init__(*filters)
    
    async def check(self, event: Any) -> bool:
        for filter_obj in self.filters:
            if await filter_obj.check_with_warning(event):
                return True
        return False


class NotFilter(EventFilter):
    """逻辑非过滤器"""
    
    def __init__(self, filter: EventFilter):
        super().__init__()
        self.filter = filter
    
    def _get_supported_event_types(self) -> List[Type]:
        """Not过滤器支持与子过滤器相同的事件类型"""
        return self.filter.supported_event_types
    
    async def check(self, event: Any) -> bool:
        return not await self.filter.check_with_warning(event)
    
    def __repr__(self) -> str:
        return f"NotFilter({repr(self.filter)})"


# ==================== 基础内容过滤器 ====================

class ContainsFilter(MessageFilter):
    """包含关键词过滤器"""
    
    def __init__(self, keywords: Union[str, List[str]], case_sensitive: bool = False):
        super().__init__()
        self.keywords = [keywords] if isinstance(keywords, str) else keywords
        self.case_sensitive = case_sensitive
    
    async def check(self, event: MessageEvent) -> bool:
        text = event.message.to_plain_text()
        if not self.case_sensitive:
            text = text.lower()
        
        for keyword in self.keywords:
            check_keyword = keyword if self.case_sensitive else keyword.lower()
            if check_keyword in text:
                return True
        return False
    
    def __repr__(self) -> str:
        return f"ContainsFilter(keywords={self.keywords}, case_sensitive={self.case_sensitive})"


class StartsWithFilter(MessageFilter):
    """以指定前缀开头过滤器"""
    
    def __init__(self, prefix: str, case_sensitive: bool = False):
        super().__init__()
        self.prefix = prefix
        self.case_sensitive = case_sensitive
    
    async def check(self, event: MessageEvent) -> bool:
        text = event.message.to_plain_text()
        if not self.case_sensitive:
            text = text.lower()
            prefix = self.prefix.lower()
        else:
            prefix = self.prefix
        
        return text.startswith(prefix)
    
    def __repr__(self) -> str:
        return f"StartsWithFilter(prefix='{self.prefix}', case_sensitive={self.case_sensitive})"


class EndsWithFilter(MessageFilter):
    """以指定后缀结尾过滤器"""
    
    def __init__(self, suffix: str, case_sensitive: bool = False):
        super().__init__()
        self.suffix = suffix
        self.case_sensitive = case_sensitive
    
    async def check(self, event: MessageEvent) -> bool:
        text = event.message.to_plain_text()
        if not self.case_sensitive:
            text = text.lower()
            suffix = self.suffix.lower()
        else:
            suffix = self.suffix
        
        return text.endswith(suffix)
    
    def __repr__(self) -> str:
        return f"EndsWithFilter(suffix='{self.suffix}', case_sensitive={self.case_sensitive})"


class RegexFilter(MessageFilter):
    """正则表达式过滤器"""
    
    def __init__(self, pattern: str, flags: int = 0):
        super().__init__()
        self.pattern = re.compile(pattern, flags)
    
    async def check(self, event: MessageEvent) -> bool:
        text = event.message.to_plain_text()
        return bool(self.pattern.search(text))
    
    def __repr__(self) -> str:
        return f"RegexFilter(pattern='{self.pattern.pattern}')"


class EqualFilter(MessageFilter):
    """完全相等过滤器"""
    
    def __init__(self, text: str, case_sensitive: bool = False):
        super().__init__()
        self.text = text
        self.case_sensitive = case_sensitive
    
    async def check(self, event: MessageEvent) -> bool:
        message_text = event.message.to_plain_text()
        if not self.case_sensitive:
            return message_text.lower() == self.text.lower()
        return message_text == self.text
    
    def __repr__(self) -> str:
        return f"EqualFilter(text='{self.text}', case_sensitive={self.case_sensitive})"


# ==================== 用户和群组过滤器 ====================

class UserFilter(MessageFilter):
    """用户ID过滤器"""
    
    def __init__(self, user_ids: Union[int, str, List[Union[int, str]]]):
        super().__init__()
        if isinstance(user_ids, (int, str)):
            self.user_ids = [str(user_ids)]
        else:
            self.user_ids = [str(uid) for uid in user_ids]
    
    async def check(self, event: MessageEvent) -> bool:
        try:
            user_id = str(event.user.user_id)
            return user_id in self.user_ids
        except (ValueError, AttributeError):
            return False
    
    def __repr__(self) -> str:
        return f"UserFilter(user_ids={self.user_ids})"


class GroupFilter(MessageFilter):
    """群组ID过滤器"""
    
    def __init__(self, group_ids: Union[int, str, List[Union[int, str]]]):
        super().__init__()
        if isinstance(group_ids, (int, str)):
            self.group_ids = [str(group_ids)]
        else:
            self.group_ids = [str(gid) for gid in group_ids]
    
    async def check(self, event: MessageEvent) -> bool:
        if not event.group:
            return False
        try:
            group_id = str(event.group.group_id)
            return group_id in self.group_ids
        except (ValueError, AttributeError):
            return False
    
    def __repr__(self) -> str:
        return f"GroupFilter(group_ids={self.group_ids})"


class PrivateFilter(MessageFilter):
    """私聊消息过滤器"""
    
    def __init__(self):
        super().__init__()
    
    async def check(self, event: MessageEvent) -> bool:
        return event.group is None
    
    def __repr__(self) -> str:
        return "PrivateFilter()"


class GroupOnlyFilter(MessageFilter):
    """群聊消息过滤器"""
    
    def __init__(self):
        super().__init__()
    
    async def check(self, event: MessageEvent) -> bool:
        return event.group is not None
    
    def __repr__(self) -> str:
        return "GroupOnlyFilter()"


# ==================== 权限过滤器 ====================

class PermissionFilter(MessageFilter):
    """权限检查过滤器"""
    
    def __init__(self, permission: Union[str, List[str]], perm_system: Optional[PermSystem] = None):
        super().__init__()
        self.permission = permission
        self.perm_system = perm_system
    
    async def check(self, event: MessageEvent) -> bool:
        if not self.perm_system:
            # 尝试从全局导入
            from .. import perm_system as global_perm_system
            self.perm_system = global_perm_system
        
        if not self.perm_system:
            return True  # 如果没有权限系统，默认通过
        
        group_id = event.group.group_id if event.group else -1
        return self.perm_system.check_perm(
            self.permission,
            event.user.user_id,
            group_id
        )
    
    def __repr__(self) -> str:
        return f"PermissionFilter(permission={self.permission})"


# ==================== 速率限制过滤器 ====================

class RateLimitFilter(MessageFilter):
    """速率限制过滤器"""
    
    def __init__(self, requests: int, period: int = 60, key_func: Optional[Callable[[MessageEvent], str]] = None):
        """
        Args:
            requests: 允许的请求次数
            period: 时间周期（秒）
            key_func: 生成限制键的函数，默认为按用户ID限制
        """
        super().__init__()
        self.requests = requests
        self.period = period
        self.key_func = key_func or (lambda event: str(event.user.user_id))
        self.requests_log: Dict[str, List[float]] = defaultdict(list)
    
    async def check(self, event: MessageEvent) -> bool:
        key = self.key_func(event)
        now = time.time()
        
        # 清理过期记录
        self.requests_log[key] = [
            t for t in self.requests_log[key]
            if now - t < self.period
        ]
        
        if len(self.requests_log[key]) >= self.requests:
            return False
        
        self.requests_log[key].append(now)
        return True
    
    def __repr__(self) -> str:
        return f"RateLimitFilter(requests={self.requests}, period={self.period})"


# ==================== 消息类型过滤器 ====================

class MessageTypeFilter(MessageFilter):
    """消息类型过滤器"""
    
    def __init__(self, message_type: str):
        super().__init__()
        self.message_type = message_type
    
    async def check(self, event: MessageEvent) -> bool:
        # 检查消息链中是否包含指定类型的消息段
        for segment in event.message.segments:
            if segment.type == self.message_type:
                return True
        return False
    
    def __repr__(self) -> str:
        return f"MessageTypeFilter(message_type='{self.message_type}')"


# ==================== AT类型过滤器 ====================

class AtSomeoneFilter(MessageFilter):
    """检查是否@了指定用户"""
    
    def __init__(self, user_ids: Union[int, str, List[Union[int, str]]]):
        super().__init__()
        if isinstance(user_ids, (int, str)):
            self.user_ids = [str(user_ids)]
        else:
            self.user_ids = [str(uid) for uid in user_ids]
    
    async def check(self, event: MessageEvent) -> bool:
        for segment in event.message.segments:
            if segment.type == "at" and isinstance(segment.data, dict):
                user_id = segment.data.get("user_id")
                if user_id and user_id in self.user_ids:
                    return True
        return False
    
    def __repr__(self) -> str:
        return f"AtSomeoneFilter(user_ids={self.user_ids})"


class AtMeFilter(MessageFilter):
    """检查是否@了机器人自己"""
    
    async def check(self, event: MessageEvent) -> bool:
        return event.to_me()
    
    def __repr__(self) -> str:
        return "AtMeFilter()"


class HasAtFilter(MessageFilter):
    """检查是否包含任何@"""
    
    async def check(self, event: MessageEvent) -> bool:
        return any(seg.type == "at" for seg in event.message.segments)
    
    def __repr__(self) -> str:
        return "HasAtFilter()"


# ==================== 自定义函数过滤器 ====================

class CustomFilter(MessageFilter):
    """自定义函数过滤器"""
    
    def __init__(self, func: Callable[[MessageEvent], Union[bool, Any]]):
        super().__init__()
        self.func = func
    
    async def check(self, event: MessageEvent) -> bool:
        result = self.func(event)
        if isinstance(result, bool):
            return result
        return bool(result)
    
    def __repr__(self) -> str:
        return f"CustomFilter(func={self.func.__name__})"