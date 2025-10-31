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

        # logger.info("Initializing nonebot2 compatibility layer...")

        # from Coral.nonebot_compat import init_nonebot_compat

        # init_nonebot_compat(self.event_bus, self.register, self.perm_system)

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
        self.plugin_manager.plugins.append("base_commands")
        utils.commands.register_plugin()
        self.plugin_manager.plugins.append("install_requirements")
        utils.install_requirements.register_plugin()
        self.plugin_manager.plugins.append("chat_command")
        utils.chat_command.register_plugin()
        self.register.register_command("stop", "Stop Coral", self.stopping, "ALL")
        logger.info("Buildin plugins Loaded.")

    async def run(self):
        dashboard_config = config.get(
            "dashboard", {"enable": False, "listen": False, "port": 9000}
        )
        if not isinstance(dashboard_config, dict) or not dashboard_config.get(
            "enable", False
        ):
            return
        from utils.dashboard import run_dashboard

        try:
            await run_dashboard(dashboard_config)
        except KeyboardInterrupt:
            await self.stopping()

    async def stopping(self, *args, **kwargs):
        logger.info("Stopping Coral...")
        await self.event_bus.publish(
            GenericEvent(name="coral_shutdown", platform="coral")
        )
        await driver_manager.stop_all()
        os._exit(0)