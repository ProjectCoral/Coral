import os
import sys
import threading
import time
import logging
import asyncio
from pyfiglet import Figlet
from colorama import Fore
from typing import Union, List

from core.protocol import *
from core.core import (
    config,
    event_bus,
    register,
    perm_system,
    plugin_manager,
    driver_manager,
    adapter_manager,
    CORAL_VERSION
)

logger = logging.getLogger(__name__)


import utils.commands
import utils.install_requirements
import utils.chat_command

class Coral:
    def __init__(self):
        textrender=Figlet(font="larry3d")
        print(Fore.GREEN + textrender.renderText("Project Coral") + Fore.RESET)
        asyncio.run(self.initialize())
        asyncio.run(self.run())

    async def initialize(self):
        start_time = time.time()

        self.config = config
        self.register = register
        self.perm_system = perm_system
        self.event_bus = event_bus
        self.plugin_manager = plugin_manager
        await self.event_bus.initialize()
        self.register.hook_perm_system(self.perm_system)

        self.register.load_buildin_plugins = self.register_buildin_plugins

        self.config.set("coral_version", CORAL_VERSION)

        self.register_buildin_plugins()

        await self.plugin_manager.load_all_plugins()

        logger.info("Loading adapters and drivers...")

        await adapter_manager.load_adapters()
        await driver_manager.load_drivers()

        logger.info("Initializing nonebot2 compatibility layer...")

        from core.nonebot_compat import init_nonebot_compat
        init_nonebot_compat(self.event_bus, self.register, self.perm_system)

        await self.event_bus.publish(    
            GenericEvent(
                name="coral_initialized",
                platform="coral"
            )
        )
        
        end_time = time.time()

        logger.info(f"[green]Coral initialized in {end_time - start_time:.2f} seconds.[/]")

        last_init_time = self.config.get("last_init_time", end_time - start_time)
        if end_time - start_time < last_init_time:
            logger.info(f"[cyan]Coral initialize boosted\U0001F680 by {last_init_time - end_time + start_time:.2f} seconds.[/]")
        self.config.set("last_init_time", end_time - start_time)

        logger.info("All things works fine\U0001F60B, starting drivers...")

        await driver_manager.start_all()

    def register_buildin_plugins(self):
        self.plugin_manager.plugins.append("base_commands")
        utils.commands.register_plugin()
        self.plugin_manager.plugins.append("install_requirements")
        utils.install_requirements.register_plugin()
        self.plugin_manager.plugins.append("chat_command")
        utils.chat_command.register_plugin()
        self.register.register_command("stop", "Stop Coral", self.stopping, "ALL")
        logger.info("Buildin plugins Loaded.")

    async def run(self):
        try:
            while True:
                await asyncio.sleep(3600)
        except asyncio.CancelledError:
            await self.stopping()
        except KeyboardInterrupt:
            await self.stopping()

    async def stopping(self, *args, **kwargs):
        logger.info("Stopping Coral...")
        await self.event_bus.publish(
                GenericEvent(
                    name="coral_shutdown",
                    platform="coral"
                )
            )
        await driver_manager.stop_all()
        os._exit(0)

def perm_require(permission: Union[str, List[str]]):
    """权限检查装饰器"""
    def decorator(func):
        async def wrapper(event: CommandEvent, *args, **kwargs):
            # 检查权限
            if perm_system and not perm_system.check_perm(
                permission,
                event.user.user_id,
                event.group.group_id if event.group else -1
            ):
                return None # Permission denied
            return await func(event, *args, **kwargs)
        return wrapper
    return decorator

def on_message(name: str = None, priority: int = 5):
    """消息事件处理器注册"""
    def decorator(func):
        nonlocal name
        if name is None:
            name = func.__name__
        event_bus.subscribe(MessageEvent, func, priority)
        return func
    return decorator

def on_notice(name: str = None, priority: int = 5):
    """通知事件处理器注册"""
    def decorator(func):
        nonlocal name
        if name is None:
            name = func.__name__
        event_bus.subscribe(NoticeEvent, func, priority)
        return func
    return decorator

def on_event(name: str = None, event_type: Any = MessageEvent, priority: int = 5):
    """事件处理器注册"""
    def decorator(func):
        nonlocal name
        if name is None:
            name = func.__name__
        event_bus.subscribe(event_type, func, priority)
        return func
    return decorator

def on_command(name: str, description: str, permission: Union[str, List[str], None] = None):
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