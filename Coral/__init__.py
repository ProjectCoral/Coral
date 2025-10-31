"""
Coral Core对外接口模块
将核心功能的对外接口集中在此模块中，方便外部调用
"""
from typing import Any, List, Union, Callable, Optional
from .protocol import *
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
    "perm_require",
    "on_message",
    "on_notice",
    "on_event",
    "on_command",
    "on_function",
    "get_bot",
    "get_bots_by_platform",
]

def perm_require(permission: Union[str, List[str]]):
    """权限检查装饰器"""

    def decorator(func):
        async def wrapper(event: CommandEvent, *args, **kwargs):
            # 检查权限
            if perm_system and not perm_system.check_perm(
                permission,
                event.user.user_id,
                event.group.group_id if event.group else -1,
            ):
                return None  # Permission denied
            return await func(event, *args, **kwargs)

        return wrapper

    return decorator


def on_message(name: str | None = None, priority: int = 5):
    """消息事件处理器注册"""

    def decorator(func):
        nonlocal name
        if name is None:
            name = func.__name__
        event_bus.subscribe(MessageEvent, func, priority)
        return func

    return decorator


def on_notice(name: str | None = None, priority: int = 5):
    """通知事件处理器注册"""

    def decorator(func):
        nonlocal name
        if name is None:
            name = func.__name__
        event_bus.subscribe(NoticeEvent, func, priority)
        return func

    return decorator


def on_event(name: str | None = None, event_type: Any = MessageEvent, priority: int = 5):
    """事件处理器注册"""

    def decorator(func):
        nonlocal name
        if name is None:
            name = func.__name__
        event_bus.subscribe(event_type, func, priority)
        return func

    return decorator


def on_command(
    name: str, description: str, permission: Union[str, List[str], None] = None
):
    """命令处理器注册"""

    def decorator(func):
        # 注册命令
        register.register_command(name, description, func, permission)

        # 添加权限检查（如果提供了权限）
        if permission:
            func = perm_require(permission)(func)

        return func

    return decorator


def on_function(name: str):
    """功能函数注册"""

    def decorator(func):
        register.register_function(name, func)
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