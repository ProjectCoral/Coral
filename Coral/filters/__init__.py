"""
过滤器系统包
提供丰富的事件过滤条件，简化插件开发
支持多种事件类型：MessageEvent, CommandEvent, NoticeEvent, GenericEvent
"""
from typing import Union, List, Callable, Any, Optional

from .base import EventFilter, MessageFilter, CompositeFilter
from .message_filters import (
    ContainsFilter,
    StartsWithFilter,
    EndsWithFilter,
    RegexFilter,
    EqualFilter,
    UserFilter,
    GroupFilter,
    PrivateFilter,
    GroupOnlyFilter,
    PermissionFilter,
    RateLimitFilter,
    MessageTypeFilter,
    AtSomeoneFilter,
    AtMeFilter,
    HasAtFilter,
    CustomFilter,
    AndFilter,
    OrFilter,
    NotFilter,
)

# ==================== 工厂函数 ====================

def contains(keywords: Union[str, List[str]], case_sensitive: bool = False) -> MessageFilter:
    """包含关键词"""
    return ContainsFilter(keywords, case_sensitive)


def starts_with(prefix: str, case_sensitive: bool = False) -> MessageFilter:
    """以指定前缀开头"""
    return StartsWithFilter(prefix, case_sensitive)


def ends_with(suffix: str, case_sensitive: bool = False) -> MessageFilter:
    """以指定后缀结尾"""
    return EndsWithFilter(suffix, case_sensitive)


def regex(pattern: str, flags: int = 0) -> MessageFilter:
    """正则表达式匹配"""
    return RegexFilter(pattern, flags)


def equal(text: str, case_sensitive: bool = False) -> MessageFilter:
    """完全相等"""
    return EqualFilter(text, case_sensitive)


def from_user(user_ids: Union[int, str, List[Union[int, str]]]) -> MessageFilter:
    """来自指定用户"""
    return UserFilter(user_ids)


def in_group(group_ids: Union[int, str, List[Union[int, str]]]) -> MessageFilter:
    """在指定群组中"""
    return GroupFilter(group_ids)


def is_private() -> MessageFilter:
    """私聊消息"""
    return PrivateFilter()


def is_group() -> MessageFilter:
    """群聊消息"""
    return GroupOnlyFilter()


def has_permission(permission: Union[str, List[str]]) -> MessageFilter:
    """具有指定权限"""
    return PermissionFilter(permission)


def rate_limit(requests: int, period: int = 60, key_func: Optional[Callable[[Any], str]] = None) -> MessageFilter:
    """速率限制"""
    return RateLimitFilter(requests, period, key_func)


def message_type(msg_type: str) -> MessageFilter:
    """指定消息类型"""
    return MessageTypeFilter(msg_type)


def custom(func: Callable[[Any], Union[bool, Any]]) -> MessageFilter:
    """自定义过滤函数"""
    return CustomFilter(func)


def and_(*filters: MessageFilter) -> MessageFilter:
    """逻辑与组合"""
    return AndFilter(*filters)


def or_(*filters: MessageFilter) -> MessageFilter:
    """逻辑或组合"""
    return OrFilter(*filters)


def not_(filter: MessageFilter) -> MessageFilter:
    """逻辑非"""
    return NotFilter(filter)


def to_someone(user_ids: Union[int, str, List[Union[int, str]]]) -> MessageFilter:
    """检查是否@了指定用户"""
    return AtSomeoneFilter(user_ids)


def to_me() -> MessageFilter:
    """检查是否@了机器人自己"""
    return AtMeFilter()


def has_at() -> MessageFilter:
    """检查是否包含任何@"""
    return HasAtFilter()


# 导出所有过滤器类
__all__ = [
    # 基类
    'EventFilter',
    'MessageFilter',
    'CompositeFilter',
    
    # 消息过滤器类
    'ContainsFilter',
    'StartsWithFilter',
    'EndsWithFilter',
    'RegexFilter',
    'EqualFilter',
    'UserFilter',
    'GroupFilter',
    'PrivateFilter',
    'GroupOnlyFilter',
    'PermissionFilter',
    'RateLimitFilter',
    'MessageTypeFilter',
    'AtSomeoneFilter',
    'AtMeFilter',
    'HasAtFilter',
    'CustomFilter',
    'AndFilter',
    'OrFilter',
    'NotFilter', 
    
    # 工厂函数
    'contains',
    'starts_with',
    'ends_with',
    'regex',
    'equal',
    'from_user',
    'in_group',
    'is_private',
    'is_group',
    'has_permission',
    'rate_limit',
    'message_type',
    'custom',
    'and_',
    'or_',
    'not_',
    'to_someone',
    'to_me',
    'has_at',
]