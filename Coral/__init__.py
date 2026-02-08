"""
Coral Core对外接口模块
将核心功能的对外接口集中在此模块中，方便外部调用
"""
from typing import Any, List, Union, Optional
from .protocol import *
from .filters import *
from .core import (
    config,
    event_bus,
    register,
    perm_system,
    plugin_manager,
    driver_manager,
    adapter_manager,
    CORAL_VERSION,
)

__all__ = [
    "config",
    "event_bus",
    "register",
    "perm_system",
    "plugin_manager",
    "driver_manager",
    "adapter_manager",
    "CORAL_VERSION",
    # 外部接口
    "on_message",
    "on_notice",
    "on_event",
    "on_command",
    "on_function",
    "on_load",
    "on_unload",
    "get_bot",
    "get_bots_by_platform",
    # 过滤条件工厂函数
    "contains",
    "starts_with",
    "ends_with",
    "regex",
    "equal",
    "from_user",
    "in_group",
    "is_private",
    "is_group",
    "has_permission",
    "rate_limit",
    "message_type",
    "custom",
    "and_",
    "or_",
    "not_",
    # 新增的AT相关过滤器
    "to_someone",
    "to_me",
    "has_at",
]



def on_message(
    name: str | None = None, 
    priority: int = 5,
    filters: Optional[Union[EventFilter, List[EventFilter]]] = None
):
    """
    消息事件处理器注册装饰器（支持过滤条件）
    
    Args:
        name: 处理器名称，如果为None则使用函数名
        priority: 优先级，数字越小优先级越高（默认为5）
        filters: 过滤条件，可以是单个EventFilter或列表
        
    Returns:
        装饰器函数
    """

    def decorator(func):
        nonlocal name
        if name is None:
            name = func.__name__
        
        async def wrapper(event: MessageEvent):
            # 应用过滤条件
            if filters:
                if isinstance(filters, EventFilter):
                    if not await filters.check_with_warning(event):
                        return None
                else:
                    for filter in filters:
                        if not await filter.check_with_warning(event):
                            return None
            return await func(event)
        
        event_bus.subscribe(MessageEvent, wrapper, priority)
        return func

    return decorator


def on_notice(
    name: str | None = None, 
    priority: int = 5,
    filters: Optional[Union[EventFilter, List[EventFilter]]] = None
):
    """
    通知事件处理器注册装饰器（支持过滤条件）
    
    Args:
        name: 处理器名称，如果为None则使用函数名
        priority: 优先级，数字越小优先级越高（默认为5）
        filters: 过滤条件，可以是单个EventFilter或列表
        
    Returns:
        装饰器函数
    """

    def decorator(func):
        nonlocal name
        if name is None:
            name = func.__name__
        
        async def wrapper(event: NoticeEvent):
            # 应用过滤条件
            if filters:
                if isinstance(filters, EventFilter):
                    if not await filters.check_with_warning(event):
                        return None
                else:
                    for filter in filters:
                        if not await filter.check_with_warning(event):
                            return None
            return await func(event)
        
        event_bus.subscribe(NoticeEvent, wrapper, priority)
        return func

    return decorator


def on_event(
    name: str | None = None, 
    event_type: Any = MessageEvent, 
    priority: int = 5,
    filters: Optional[Union[EventFilter, List[EventFilter]]] = None
):
    """事件处理器注册（支持过滤条件）"""

    def decorator(func):
        nonlocal name
        if name is None:
            name = func.__name__
        
        async def wrapper(event):
            # 应用过滤条件
            if filters:
                if isinstance(filters, EventFilter):
                    if not await filters.check_with_warning(event):
                        return None
                else:
                    for filter in filters:
                        if not await filter.check_with_warning(event):
                            return None
            return await func(event)
        
        event_bus.subscribe(event_type, wrapper, priority)
        return func

    return decorator


def on_command(
    name: str, 
    description: str, 
    permission: Union[str, List[str], None] = None,
    filters: Optional[Union[EventFilter, List[EventFilter]]] = None
):
    """命令处理器注册（支持过滤条件）"""

    def decorator(func):
        # 创建包装函数
        async def wrapper(event: CommandEvent):
            # 应用过滤条件
            if filters:
                if isinstance(filters, EventFilter):
                    if not await filters.check_with_warning(event):
                        return None
                else:
                    for filter in filters:
                        if not await filter.check_with_warning(event):
                            return None
            return await func(event)
        
        # 注册命令（权限检查已经在register.register_command中处理）
        register.register_command(name, description, wrapper, permission)

        return func

    return decorator


def on_function(name: str):
    """功能函数注册"""

    def decorator(func):
        register.register_function(name, func)
        return func

    return decorator


def on_load():
    """
    插件加载装饰器，在插件被加载时调用
    
    使用示例:
        @on_load()
        async def plugin_load():
            print("插件正在加载...") # 插件加载时执行的初始化代码
    """
    def decorator(func):
        # 标记函数为加载钩子
        func._is_load_hook = True
        return func
    return decorator


def on_unload():
    """
    插件卸载装饰器，在插件被卸载时调用
    
    使用示例:
        @on_unload()
        async def plugin_unload():
            print("插件正在卸载...") # 插件卸载时执行的清理代码
    """
    def decorator(func):
        # 标记函数为卸载钩子
        func._is_unload_hook = True
        return func
    return decorator


def get_bot(self_id: str) -> Optional[Bot]:
    """根据self_id获取机器人实例"""
    if adapter_manager:
        return adapter_manager.get_bot(self_id)
    return None


def get_bots_by_platform(platform: str) -> List[Bot]:
    """根据平台获取所有机器人实例"""
    if adapter_manager:
        return adapter_manager.get_bots_by_platform(platform)
    return []
