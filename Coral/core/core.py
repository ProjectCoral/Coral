"""
Coral Core 核心实现
将核心功能的对外接口集中在此模块中，方便外部调用
"""

import sys
import os
import logging
import time

logger = logging.getLogger(__name__)

from ..plugin import PLUGINMANAGER_VERSION
from ..protocol import PROTOCOL_VERSION
from .commands import CoreCommands

# 设置全局异常钩子
from ..exception import global_exception_handler

sys.excepthook = global_exception_handler

# 导入核心模块
from ..config import Config
from ..register import Register
from ..plugin import PluginManager
from ..permission import PermSystem
from ..event_bus import EventBus
from ..adapter import AdapterManager
from ..driver import DriverManager

# 导入常量（已在 __init__.py 中定义）
from . import CORAL_VERSION, PLUGIN_DIR, CONFIG_FILE

# 导入 DI 容器
from ..di import Container, Lifetime

# 创建根容器
_container = Container()

# 注册基础组件（无依赖）
_container.register_instance(Config, Config(CONFIG_FILE))
_container.register_instance(EventBus, EventBus())


def _create_register(container: Container) -> Register:
    """创建 Register 实例"""
    event_bus = container.resolve(EventBus)
    register = Register(event_bus)
    return register


def _create_perm_system(container: Container) -> PermSystem:
    """创建 PermSystem 实例"""
    config = container.resolve(Config)
    perm_system = PermSystem(config)
    # Hook perm_system into register (resolve register AFTER perm_system creation)
    register = container.resolve(Register)
    register.hook_perm_system(perm_system)
    return perm_system


def _create_plugin_manager(container: Container) -> PluginManager:
    """创建 PluginManager 实例"""
    register = container.resolve(Register)
    config = container.resolve(Config)
    perm_system = container.resolve(PermSystem)
    plugin_manager = PluginManager(register, config, perm_system, PLUGIN_DIR)
    return plugin_manager


def _create_adapter_manager(container: Container) -> AdapterManager:
    """创建 AdapterManager 实例"""
    event_bus = container.resolve(EventBus)
    config = container.resolve(Config)
    adapter_manager = AdapterManager(event_bus, config)
    return adapter_manager


def _create_driver_manager(container: Container) -> DriverManager:
    """创建 DriverManager 实例"""
    config = container.resolve(Config)
    adapter_manager = container.resolve(AdapterManager)
    driver_manager = DriverManager(config, adapter_manager)
    return driver_manager


# 注册单例工厂
_container.register_singleton(Register, _create_register)
_container.register_singleton(PermSystem, _create_perm_system)
_container.register_singleton(PluginManager, _create_plugin_manager)
_container.register_singleton(AdapterManager, _create_adapter_manager)
_container.register_singleton(DriverManager, _create_driver_manager)


# 初始化核心组件 - 按正确顺序解析以触发工厂函数
try:
    # 先解析基础组件（触发无依赖的注册）
    config = _container.resolve(Config)
    event_bus = _container.resolve(EventBus)

    # 解析有依赖的组件（触发工厂函数）
    register = _container.resolve(Register)
    perm_system = _container.resolve(PermSystem)
    plugin_manager = _container.resolve(PluginManager)
    adapter_manager = _container.resolve(AdapterManager)
    driver_manager = _container.resolve(DriverManager)

    # Register core commands
    core_commands = CoreCommands(register, config, perm_system, plugin_manager)
    core_commands.register_commands()

    logger.info("Coral Core initialized successfully")
except Exception as e:
    logger.critical(f"[red]Failed to initialize Coral Core: {e}[/]")
    # 重新抛出异常以便全局异常处理器捕获
    raise e


async def core_reload():
    """核心热重载，清除所有注册状态"""
    register = _container.resolve(Register)
    perm_system = _container.resolve(PermSystem)

    # Clear all registries
    register.event_registry.clear()
    register.command_registry.clear()
    register.function_registry.clear()
    register.crash_tracker.clear()

    # Clear event bus subscribers for MessageEvent and NoticeEvent
    from ..protocol import MessageEvent, NoticeEvent

    event_bus = _container.resolve(EventBus)
    event_bus.clear_subscribers(MessageEvent)
    event_bus.clear_subscribers(NoticeEvent)

    # Save and reload permissions
    perm_system.save_user_perms()
    perm_system.registered_perms = {}
    logger.info("All events, commands, functions and permissions have been unloaded.")
    perm_system.load_user_perms()

    # Reload builtin plugins (set externally by Loader)
    if (
        hasattr(core_reload, "load_buildin_plugins")
        and core_reload.load_buildin_plugins
    ):
        core_reload.load_buildin_plugins()
    logger.info("Coral Core has been reloaded.")
