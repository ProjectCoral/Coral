import os
import time
import logging
import asyncio
from typing import Union, List
from pyfiglet import Figlet
from colorama import Fore

from Coral import (
    config,
    event_bus,
    register,
    perm_system,
    plugin_manager,
    driver_manager,
    adapter_manager,
    CORAL_VERSION,
)

from Coral.protocol import *

import utils.commands
import utils.install_requirements
import utils.chat_command

logger = logging.getLogger(__name__)


class CoralLoader:
    def __init__(self):
        textrender = Figlet(font="larry3d")
        print(Fore.GREEN + textrender.renderText("Project Coral") + Fore.RESET)
        asyncio.run(self.initialize())

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

        await self.event_bus.publish(
            GenericEvent(name="coral_initialized", platform="coral")
        )

        end_time = time.time()

        logger.info(
            f"[green]Coral initialized in {end_time - start_time:.2f} seconds.[/]"
        )

        last_init_time = self.config.get("last_init_time", end_time - start_time)
        if last_init_time and end_time - start_time < last_init_time:
            logger.info(
                f"[cyan]Coral initialize boosted\U0001f680 by {last_init_time - end_time + start_time:.2f} seconds.[/]"
            )
        self.config.set("last_init_time", end_time - start_time)

        logger.info("All things works fine\U0001f60b, starting drivers...")

        await driver_manager.start_all()

        await self.run()

    def register_buildin_plugins(self):
        """Register built-in system functions."""
        # Note: base_commands functionality is now integrated into core.py
        # as CoreCommands class, so we don't need to register it here
        
        # Register install_requirements functionality
        utils.install_requirements.register_plugin()
        
        # Register chat_command functionality
        utils.chat_command.register_plugin()
        
        # Register stop command
        self.register.register_command("stop", "Stop Coral", self.stopping, "ALL")
        
        logger.info("Built-in functions registered.")

    async def run(self):
        dashboard_config = config.get(
            "dashboard", {"enable": False, "listen": False, "port": 9000}
        )
        if not isinstance(dashboard_config, dict) or not dashboard_config.get(
            "enable", False
        ):
            # 如果没有启用dashboard，保持程序运行
            logger.info("Coral is running. Press Ctrl+C to stop.")
            try:
                # 无限等待，保持程序运行
                while True:
                    await asyncio.sleep(3600)  # 每小时检查一次
            except KeyboardInterrupt:
                await self.stopping()
            return
        
        from utils.dashboard import run_dashboard

        try:
            await run_dashboard(dashboard_config)
        except KeyboardInterrupt:
            await self.stopping()

    async def stopping(self, *args, **kwargs):
        logger.info("Stopping Coral...")
        
        # 发布框架关闭事件
        await self.event_bus.publish(
            GenericEvent(name="coral_shutdown", platform="coral")
        )
        
        # 卸载所有插件（执行插件的on_unload钩子）
        logger.info("Unloading all plugins...")
        try:
            success, message = await self.plugin_manager.unload_all_plugins()
            if success:
                logger.info(f"✓ {message}")
            else:
                logger.warning(f"⚠ {message}")
        except Exception as e:
            logger.error(f"Error unloading plugins: {e}")
        
        # 关闭事件总线
        if hasattr(self.event_bus, 'shutdown'):
            await self.event_bus.shutdown()
        
        # 停止所有驱动程序
        await driver_manager.stop_all()
        
        logger.info("Coral stopped successfully.")
        os._exit(0)
