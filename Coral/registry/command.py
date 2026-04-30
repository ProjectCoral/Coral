"""
Command Registry
================

Manages command registration and execution.
"""

import logging
from typing import Optional, Callable, Dict, Any

from ..protocol import CommandEvent, MessageBase

logger = logging.getLogger(__name__)


class CommandRegistry:
    """Registry for managing commands."""

    def __init__(self, event_bus, perm_system=None):
        """
        Initialize command registry.

        Args:
            event_bus: Event bus instance
            perm_system: Optional permission system for permission checks
        """
        self.event_bus = event_bus
        self.perm_system = perm_system
        self.commands: Dict[str, tuple] = {}  # command_name -> (handler, permission)
        self.command_descriptions: Dict[str, str] = {}
        self.crash_tracker = None

        # Subscribe to CommandEvent
        self.event_bus.subscribe(CommandEvent, self.execute_command)

    def set_crash_tracker(self, crash_tracker):
        """Set crash tracker for error reporting."""
        self.crash_tracker = crash_tracker

    def register_command(
        self,
        command_name: str,
        description: str,
        function: Callable,
        permission: Optional[Any] = None,
    ):
        """
        Register a command.

        Args:
            command_name: Name of the command
            description: Command description
            function: Command handler function
            permission: Optional permission required
        """
        if command_name in self.commands:
            logger.warning(
                f"[yellow]Command [/]{command_name}[yellow] already registered, overwriting...[/]"
            )
        self.commands[command_name] = (function, permission)
        self.command_descriptions[command_name] = description

    def unregister_command(self, command_name: str):
        """
        Unregister a command.

        Args:
            command_name: Name of the command to unregister
        """
        if command_name in self.commands:
            del self.commands[command_name]
        if command_name in self.command_descriptions:
            del self.command_descriptions[command_name]

    def get_command_description(self, command_name: str) -> str:
        """Get description for a command."""
        return self.command_descriptions.get(command_name, "No description found")

    def get_all_commands(self) -> Dict[str, tuple]:
        """Get all registered commands."""
        return self.commands.copy()

    async def execute_command(self, event: CommandEvent) -> Optional[MessageBase]:
        """
        Execute a command from a CommandEvent.

        Args:
            event: The command event

        Returns:
            MessageBase response or None
        """
        logger.debug(
            f"Executing command {event.command} from {event.user.user_id} "
            f"in {event.group.group_id if event.group else None} with args {event.args}"
        )

        if event.command not in self.commands:
            return event.reply(self.no_command())

        handler, permission = self.commands[event.command]

        # Permission check
        if (
            permission
            and self.perm_system
            and not self.perm_system.check_perm(
                permission,
                event.user.user_id,
                event.group.group_id if event.group else -1,
            )
        ):
            return event.reply("Permission denied")

        try:
            result = await handler(event)
            if isinstance(result, MessageBase):
                return result
            else:
                return event.reply(result)
        except Exception as e:
            logger.exception(f"[red]Error executing command {event.command}: {e}[/]")
            if self.crash_tracker:
                import traceback

                self.crash_tracker.record_crash(
                    "command",
                    event.command,
                    str(e),
                    traceback.format_exc(),
                )
            return event.reply(f"Error executing command {event.command}: {e}")

    def no_command(self):
        """Default message when command not found."""
        return "No command found"

    def clear(self):
        """Clear all commands."""
        self.commands.clear()
        self.command_descriptions.clear()
