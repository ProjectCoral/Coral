from __future__ import annotations

"""
Core Commands Module

This module contains the core commands for Coral, including help, clear cache, and status.
"""

import os
import time
import logging
from typing import Tuple, Generator, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from ..register import Register
    from ..config import Config
    from ..permission import PermSystem
    from ..event_bus import EventBus
    from ..plugin import PluginManager

logger = logging.getLogger(__name__)


# Core Commands Class
class CoreCommands:
    """Core system commands integrated into Coral core."""

    def __init__(
        self,
        register: "Register",
        config: "Config",
        perm_system: "PermSystem",
        plugin_manager: "PluginManager",
    ):
        self.register = register
        self.config = config
        self.perm_system = perm_system
        self.plugin_manager = plugin_manager
        self.init_time = None

    def register_commands(self):
        """Register core commands."""
        from ..permission import Permission

        # 注册权限
        ROOT_PERMISSION = Permission("core", "", "Core system permission")
        HELP_PERMISSION = Permission("core", "help", "Permission to use help command")
        CLEAR_PERMISSION = Permission("core", "clear", "Permission to clear cache")
        STATUS_PERMISSION = Permission(
            "core", "status", "Permission to see system status"
        )

        self.perm_system.register_perm(ROOT_PERMISSION)
        self.perm_system.register_perm(HELP_PERMISSION)
        self.perm_system.register_perm(CLEAR_PERMISSION)
        self.perm_system.register_perm(STATUS_PERMISSION)

        self.register.register_command(
            "perms",
            "权限管理命令\n"
            "用法:\n"
            "  perms show - 显示所有已注册权限\n"
            "  perms list - 列出用户和群组权限\n"
            "  perms add <权限名> <用户ID> [群组ID] - 添加权限\n"
            "  perms remove <权限名> <用户ID> [群组ID] - 移除权限\n"
            "  perms grant <权限名> <用户ID> - 授予用户全局权限\n"
            "  perms revoke <权限名> <用户ID> - 撤销用户全局权限",
            self.perm_system.perm_command,
            Permission("permission_system", "", "权限系统基础权限"),
        )

        # 注册命令
        self.register.register_command(
            "help", "Show help message", self.show_help, HELP_PERMISSION
        )
        self.register.register_command(
            "clear", "Clear cache", self.clear_cache, CLEAR_PERMISSION
        )
        self.register.register_command(
            "status", "Show system status", self.status, STATUS_PERMISSION
        )

        # 注册初始化事件
        self.register.register_event(
            "coral_initialized", "init_time", self.init_timer, 1
        )

    async def init_timer(self, *args):
        """Initialize timer when Coral starts."""
        self.init_time = time.time()
        logger.debug("Core commands timer initialized")
        return None, False, 1

    async def show_help(self, event):
        """Show help message with all available commands."""
        try:
            commands_list = []
            for command_name in self.register.commands:
                description = self.register.get_command_description(command_name)
                commands_list.append(f"{command_name}: {description}")

            return "List of available commands:\n" + "\n".join(commands_list)
        except Exception as e:
            logger.error(f"Error generating help message: {e}")
            return "Error: Unable to generate help message"

    async def clear_cache(self, event):
        """Clear the cache directory."""
        cache_dir = "cache"
        try:
            if os.path.exists(cache_dir):
                cleared_count = 0
                for file in os.listdir(cache_dir):
                    file_path = os.path.join(cache_dir, file)
                    try:
                        os.remove(file_path)
                        cleared_count += 1
                    except Exception as e:
                        logger.warning(f"Failed to remove {file_path}: {e}")

                logger.debug(f"Cache cleared: {cleared_count} files removed")
                return f"Cache cleared: {cleared_count} files removed"
            else:
                return "Cache directory does not exist"
        except Exception as e:
            logger.error(f"Error clearing cache: {e}")
            return f"Error clearing cache: {e}"

    async def status(self, event):
        """Show system status including version, plugins, permissions, and uptime."""
        try:
            message = "Status:\n"

            # Coral version
            coral_version = self.config.get("coral_version", "Unknown")
            message += f"Coral Version: {coral_version}\n"

            # Plugin information using new plugin list command
            try:
                # Create a mock event for plugin list command
                from ..protocol import (
                    CommandEvent,
                    UserInfo,
                    MessageChain,
                    MessageSegment,
                )

                mock_event = CommandEvent(
                    event_id=f"Console-{time.time()}",
                    platform="system",
                    self_id="Console",
                    command="plugin",
                    raw_message=MessageChain(
                        [MessageSegment(type="text", data="plugin list")]
                    ),
                    user=UserInfo(platform="system", user_id="Console"),
                    group=None,
                    args=["list", "all"],
                )

                # Use the new plugin command handler
                response = await self.plugin_manager.commands.handle_plugin_command(
                    mock_event
                )
                if hasattr(response, "message"):
                    message += response.message.to_plain_text() + "\n"
                else:
                    message += "Plugins: Information unavailable\n"
            except Exception as e:
                logger.warning(f"Failed to get plugin information: {e}")
                message += "Plugins: Error retrieving information\n"

            # Permission count
            perm_count = len(self.perm_system.registered_perms)
            message += f"Total registered {perm_count} permissions\n"

            # Uptime
            if self.init_time is None:
                message += "Uptime: System not fully initialized\n"
            else:
                uptime = time.time() - self.init_time
                day, hour, minute, second = (
                    uptime // (24 * 3600),
                    uptime // 3600 % 24,
                    uptime // 60 % 60,
                    uptime % 60,
                )
                message += f"Uptime: {int(day)} day(s) {int(hour)} hour(s) {int(minute)} minute(s) {int(second)} second(s)\n"

            message += "Hello from Coral!😋"
            return message

        except Exception as e:
            logger.error(f"Error generating status: {e}")
            return f"Error generating status: {e}"
