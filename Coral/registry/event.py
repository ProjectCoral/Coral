"""
Event Registry
==============

Manages event subscription and execution.
"""

import logging
from collections import defaultdict
from typing import Dict, Callable

from ..protocol import GenericEvent

logger = logging.getLogger(__name__)


class EventRegistry:
    """Registry for managing event subscriptions."""

    def __init__(self, event_bus):
        """
        Initialize event registry.

        Args:
            event_bus: Event bus instance
        """
        self.event_bus = event_bus
        self._event_handlers: Dict[str, Dict[Callable, Callable]] = defaultdict(
            dict
        )  # event_name: handler_func -> wrapper_func
        self.crash_tracker = None

    def set_crash_tracker(self, crash_tracker):
        """Set crash tracker for error reporting."""
        self.crash_tracker = crash_tracker

    def register_event(
        self,
        event_name: str,
        listener_name: str,
        function: Callable,
        priority: int = 1,
    ):
        """
        Register an event handler.

        Args:
            event_name: Name of the event
            listener_name: Name of the listener
            function: Handler function
            priority: Subscription priority (default 1)
        """
        if (
            event_name in self._event_handlers
            and function in self._event_handlers[event_name]
        ):
            logger.error(
                f"[red bold]Event [/]{event_name}[red bold] already registered for [/]{listener_name}"
            )
            return

        async def wrapper(event: GenericEvent):
            if event.name == event_name:
                try:
                    await function(event)
                except Exception as e:
                    logger.exception(f"[red]Error in event handler: {e}[/]")
                    if self.crash_tracker:
                        import traceback

                        self.crash_tracker.record_crash(
                            "event",
                            event_name,
                            str(e),
                            traceback.format_exc(),
                            {"listener_name": listener_name},
                        )

        self._event_handlers[event_name][function] = wrapper
        self.event_bus.subscribe(GenericEvent, wrapper, priority)

    def unregister_event(self, event_name: str, listener_name: str = None):
        """
        Unregister event handlers.

        Args:
            event_name: Name of the event
            listener_name: Name of the listener (optional, if None unregisters all
                          handlers for this event_name)
        """
        if event_name in self._event_handlers:
            for function, wrapper in list(self._event_handlers[event_name].items()):
                self.event_bus.unsubscribe(GenericEvent, wrapper)
            del self._event_handlers[event_name]

    def unregister_by_wrapper(self, wrapper: Callable):
        """
        Unregister a specific event handler by its wrapper.

        Args:
            wrapper: The wrapper function to unsubscribe
        """
        for event_name, handlers in self._event_handlers.items():
            if wrapper in handlers.values():
                # Find the original handler and its wrapper
                for func, w in list(handlers.items()):
                    if w == wrapper:
                        self.event_bus.unsubscribe(GenericEvent, w)
                        del handlers[func]
                        # If event_name dict is empty, remove it
                        if not handlers:
                            del self._event_handlers[event_name]
                        return
        logger.debug(f"Wrapper not found for unregister_by_wrapper")

    def get_event_handlers(self) -> Dict[str, Dict[Callable, Callable]]:
        """Get all event handlers."""
        return dict(self._event_handlers)

    async def execute_event(self, event_name: str, platform: str = "coral"):
        """
        Execute an event by publishing a GenericEvent.

        Args:
            event_name: Name of the event to execute
            platform: Platform identifier (default "coral")
        """
        event = GenericEvent(name=event_name, platform=platform)
        await self.event_bus.publish(event)

    def clear(self):
        """Clear all event subscriptions."""
        for _, handlers in self._event_handlers.items():
            for _, wrapper in handlers.items():
                self.event_bus.unsubscribe(GenericEvent, wrapper)
        self._event_handlers.clear()
