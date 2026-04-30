"""
Register Module
===============

Register serves as the unified facade for all registries.
This module provides backward compatibility while delegating to specialized registries.
"""

import logging
import datetime
import random
from typing import Union, List, Callable, Optional

from .protocol import (
    CommandEvent,
    MessageEvent,
    NoticeEvent,
    GenericEvent,
    MessageBase,
)
from .event_bus import EventBus
from .permission import PermissionType, PermSystem
from .registry import CommandRegistry, FunctionRegistry, EventRegistry
from .crash_tracker import CrashTracker

logger = logging.getLogger(__name__)


class Register:
    """注册器类，作为各 Registry 的统一对外入口"""

    event_bus: EventBus

    def __init__(self, event_bus: EventBus):
        """
        初始化注册器

        Args:
            event_bus: 事件总线实例
        """
        self.event_bus = event_bus

        # Initialize crash tracker first
        self.crash_tracker = CrashTracker(event_bus)

        # Initialize registries
        self.command_registry = CommandRegistry(event_bus)
        self.function_registry = FunctionRegistry(event_bus)
        self.event_registry = EventRegistry(event_bus)

        # Set crash tracker on registries for error reporting
        self.command_registry.crash_tracker = self.crash_tracker
        self.function_registry.crash_tracker = self.crash_tracker
        self.event_registry.crash_tracker = self.crash_tracker

        # Register unregister handlers for crash tracker
        self.crash_tracker.register_unregister_handler(
            "command", self.command_registry.unregister_command
        )
        self.crash_tracker.register_unregister_handler(
            "function", self.function_registry.unregister_function
        )
        self.crash_tracker.register_unregister_handler(
            "event", self._event_unregister_wrapper
        )

        # Backward compatible property proxies
        self.commands = self.command_registry.commands
        self.functions = self.function_registry.functions
        self._event_handlers = self.event_registry._event_handlers
        self.crash_times = self.crash_tracker.crash_times
        self.command_descriptions = self.command_registry.command_descriptions

        # Legacy state
        self.crash_times = self.crash_tracker.crash_times

    def _event_unregister_wrapper(self, event_name: str, listener_name: str = None):
        """Wrapper for event unregister to match crash tracker callback signature."""
        self.event_registry.unregister_event(event_name, listener_name)

    def hook_perm_system(self, perm_system: PermSystem):
        """
        挂载权限系统

        Args:
            perm_system: 权限系统实例
        """
        self.perm_system = perm_system
        self.command_registry.perm_system = perm_system
        logger.debug("Permission system has been hooked with Register.")

    # === Command Registry delegation ===

    def register_command(
        self,
        command_name: str,
        description: str,
        function: Callable,
        permission: Optional[PermissionType] = None,
    ):
        """注册命令"""
        self.command_registry.register_command(
            command_name, description, function, permission
        )

    def unregister_command(self, command_name: str):
        """取消注册命令"""
        self.command_registry.unregister_command(command_name)

    def get_command_description(self, command_name: str):
        """获取命令描述"""
        return self.command_registry.get_command_description(command_name)

    # === Function Registry delegation ===

    def register_function(self, function_name: str, function: Callable):
        """注册功能函数"""
        self.function_registry.register_function(function_name, function)

    def unregister_function(self, function_name: str):
        """取消注册功能函数"""
        self.function_registry.unregister_function(function_name)

    async def execute_function(self, function_name: str, *args, **kwargs):
        """执行功能函数"""
        return await self.function_registry.execute_function(
            function_name, *args, **kwargs
        )

    # === Event Registry delegation ===

    def register_event(
        self, event_name: str, listener_name: str, function: Callable, priority: int = 1
    ):
        """注册事件处理器"""
        self.event_registry.register_event(
            event_name, listener_name, function, priority
        )

    def unregister_event(self, listener_name: str, event_name: str):
        """取消注册事件"""
        self.event_registry.unregister_event(event_name, listener_name)

    async def execute_event(self, event_name: str, platform: str = "coral"):
        """执行事件（通过发布GenericEvent）"""
        await self.event_registry.execute_event(event_name, platform)

    # === Execute methods ===

    async def execute_command(self, event: CommandEvent) -> Union[MessageBase, None]:
        """执行命令"""
        return await self.command_registry.execute_command(event)

    # === Reload and cleanup ===

    # === Crash record (delegates to crash tracker) ===

    def crash_record(
        self, type: str, function_name: str, error: str, traceback: str, *listener_queue
    ):
        """
        记录崩溃信息（转发给 CrashTracker）

        Args:
            type: 资源类型 ("command", "function", "event")
            function_name: 资源名称
            error: 错误信息
            traceback: 堆栈跟踪
            listener_queue: 额外参数（事件用，包含 listener_name）
        """
        context = None
        if type == "event" and listener_queue:
            context = {"listener_name": listener_queue[0]}

        self.crash_tracker.record_crash(type, function_name, error, traceback, context)

    # === Backward compatibility properties ===

    @property
    def no_command(self):
        """Backward compatible no_command method reference."""
        return self.command_registry.no_command

    @no_command.setter
    def no_command(self, value):
        """No-op setter for backward compatibility."""
        pass

    def __getattr__(self, name: str):
        """Proxy undefined attributes to registries for backward compatibility."""
        if name in ("command_descriptions",):
            return getattr(self.command_registry, name, None)
        raise AttributeError(
            f"'{type(self).__name__}' object has no attribute '{name}'"
        )
