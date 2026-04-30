"""
Plugin Context
==============

Tracks all resources registered by a plugin for unified cleanup on unload.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Callable, Any, Optional


@dataclass
class RegisteredCommand:
    """Represents a command registered by a plugin."""

    name: str
    handler: Callable
    permission: Optional[Any] = None


@dataclass
class RegisteredFunction:
    """Represents a function registered by a plugin."""

    name: str
    handler: Callable


@dataclass
class RegisteredEvent:
    """Represents an event subscription registered by a plugin."""

    event_name: str  # Event name string (e.g., "message", "notice")
    listener_name: str  # Listener name
    event_type: type  # Event type class (e.g., GenericEvent)
    handler: Callable  # Original handler function
    wrapper: Callable  # Wrapper function that was subscribed
    priority: int = 5


class PluginContext:
    """
    Tracks all resources registered by a plugin for unified cleanup on unload.

    This class is created when a plugin is loaded and is used to track:
    - Commands registered via @on_command
    - Functions registered via @on_function
    - Event subscriptions via @on_message, @on_notice, @on_event
    - Load/unload hooks marked via @on_load/@on_unload

    When the plugin is unloaded, cleanup() is called to remove all tracked
    registrations from the registries.
    """

    def __init__(
        self,
        plugin_name: str,
        command_registry=None,
        function_registry=None,
        event_registry=None,
        crash_tracker=None,
    ):
        """
        Initialize a PluginContext for a plugin.

        Args:
            plugin_name: Name of the plugin
            command_registry: CommandRegistry instance
            function_registry: FunctionRegistry instance
            event_registry: EventRegistry instance
            crash_tracker: CrashTracker instance
        """
        self.plugin_name = plugin_name
        self.command_registry = command_registry
        self.function_registry = function_registry
        self.event_registry = event_registry
        self.crash_tracker = crash_tracker

        self.commands: Dict[str, RegisteredCommand] = {}
        self.functions: Dict[str, RegisteredFunction] = {}
        self.events: List[RegisteredEvent] = []
        self.load_hooks: List[Callable] = []
        self.unload_hooks: List[Callable] = []

    def register_command(
        self, name: str, handler: Callable, permission: Optional[Any] = None
    ):
        """
        Track a command registration and register it with CommandRegistry.

        Args:
            name: Command name
            handler: Command handler function
            permission: Optional permission required
        """
        self.commands[name] = RegisteredCommand(name, handler, permission)
        if self.command_registry:
            self.command_registry.register_command(name, "", handler, permission)

    def register_function(self, name: str, handler: Callable):
        """
        Track a function registration and register it with FunctionRegistry.

        Args:
            name: Function name
            handler: Function handler
        """
        self.functions[name] = RegisteredFunction(name, handler)
        if self.function_registry:
            self.function_registry.register_function(name, handler)

    def register_event(
        self,
        event_name: str,
        listener_name: str,
        event_type: type,
        handler: Callable,
        wrapper: Callable,
        priority: int = 5,
    ):
        """
        Track an event subscription and register it with EventRegistry.

        Args:
            event_name: Name of the event (e.g., "message")
            listener_name: Name of the listener
            event_type: Type of event (e.g., GenericEvent)
            handler: Original handler function
            wrapper: Wrapper function that was subscribed
            priority: Subscription priority
        """
        self.events.append(
            RegisteredEvent(
                event_name, listener_name, event_type, handler, wrapper, priority
            )
        )
        if self.event_registry:
            self.event_registry.register_event(
                event_name, listener_name, handler, priority
            )

    def register_load_hook(self, hook: Callable):
        """Track a load hook."""
        self.load_hooks.append(hook)

    def register_unload_hook(self, hook: Callable):
        """Track an unload hook."""
        self.unload_hooks.append(hook)

    async def cleanup(self):
        """
        Unregister all tracked resources from registries.

        This should be called when a plugin is unloaded, before calling
        the plugin's unload hooks.
        """
        # Unregister commands
        for name in list(self.commands.keys()):
            if self.command_registry:
                self.command_registry.unregister_command(name)

        # Unregister functions
        for name in list(self.functions.keys()):
            if self.function_registry:
                self.function_registry.unregister_function(name)

        # Unregister events - use wrapper for precise cleanup
        for evt in self.events:
            if self.event_registry:
                self.event_registry.unregister_by_wrapper(evt.wrapper)

    def __repr__(self) -> str:
        return (
            f"PluginContext({self.plugin_name}, "
            f"commands={len(self.commands)}, "
            f"functions={len(self.functions)}, "
            f"events={len(self.events)})"
        )
