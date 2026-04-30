"""
Crash Tracker
=============

Centralized crash tracking and auto-disable logic for Coral components.
"""

import datetime
import random
import logging
from typing import Dict, Callable, Optional, Any

logger = logging.getLogger(__name__)


class CrashTracker:
    """
    Centralized crash tracking service.

    Tracks crashes for commands, functions, and events. When a crash threshold
    is reached, automatically calls the registered unregister handler to disable
    the problematic component.
    """

    def __init__(self, event_bus: Any = None):
        """
        Initialize crash tracker.

        Args:
            event_bus: Optional event bus instance for publishing crash events
        """
        self.event_bus = event_bus
        self._unregister_handlers: Dict[str, Callable] = {}
        self.crash_times: Dict[str, Dict[str, int]] = {}
        self._crash_context: Dict[str, Dict[str, Any]] = {}
        self._crash_tips = [
            "Oops!",
            "No worries, Coral is still running.",
            "No, this shouldn't happen.",
            "Smells like a *bug*.",
            "I'm sorry, Dave. I'm afraid I can't do that.",
            "What the heck is going on here?",
            "Houston, we have a problem.",
            "You're not supposed to be here.",
            "Yet another bug has been found.",
        ]

    def register_unregister_handler(self, resource_type: str, handler: Callable):
        """
        Register an unregister handler for a resource type.

        Args:
            resource_type: Type of resource ("command", "function", "event")
            handler: Callback function to call when auto-disable is triggered
        """
        self._unregister_handlers[resource_type] = handler
        logger.debug(f"Registered unregister handler for {resource_type}")

    def record_crash(
        self,
        resource_type: str,
        resource_name: str,
        error: str,
        traceback_str: str,
        context: Optional[Dict[str, Any]] = None,
    ):
        """
        Record a crash for a resource.

        Args:
            resource_type: Type of resource ("command", "function", "event")
            resource_name: Name of the resource
            error: Error message
            traceback_str: Traceback string
            context: Additional context (e.g., listener_name for events)
        """
        if resource_type not in self.crash_times:
            self.crash_times[resource_type] = {}
        if resource_name not in self.crash_times[resource_type]:
            self.crash_times[resource_type][resource_name] = 0

        self.crash_times[resource_type][resource_name] += 1

        # Store context for events
        if context:
            self._crash_context[resource_name] = context

        # Write crash log
        self._write_crash_log(resource_type, resource_name, error, traceback_str)

        # Check threshold and auto-disable
        if self.crash_times[resource_type][resource_name] >= 3:
            self._auto_disable(resource_type, resource_name)

    def get_crash_count(self, resource_type: str, resource_name: str) -> int:
        """Get crash count for a resource."""
        return self.crash_times.get(resource_type, {}).get(resource_name, 0)

    def clear(self):
        """Clear all crash records."""
        self.crash_times.clear()
        self._crash_context.clear()
        logger.debug("Crash tracker cleared")

    def _write_crash_log(
        self, resource_type: str, resource_name: str, error: str, traceback_str: str
    ):
        """Write crash information to a log file."""
        try:
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            log_path = f"./logs/crash_{resource_type}_{resource_name}_{timestamp}.log"
            with open(log_path, "w", encoding="utf-8") as f:
                f.write(random.choice(self._crash_tips) + "\n")
                f.write(
                    f"Coral Core has crashed in {resource_type} {resource_name} "
                    f"at {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
                )
                f.write("-" * 40 + "\n")
                f.write(f"Error: {error}\nTraceback:\n{traceback_str}")
        except Exception as e:
            logger.warning(f"Failed to write crash log: {e}")

    def _auto_disable(self, resource_type: str, resource_name: str):
        """
        Auto-disable a resource after too many crashes.

        Args:
            resource_type: Type of resource
            resource_name: Name of the resource
        """
        logger.error(
            f"[red] Auto-disabling {resource_type} [/]{resource_name}[red] "
            f"due to frequent crashes.[/]"
        )

        handler = self._unregister_handlers.get(resource_type)
        if not handler:
            logger.warning(f"No unregister handler for {resource_type}")
            return

        try:
            if resource_type == "event":
                # Events need special handling with context (listener_name)
                ctx = self._crash_context.get(resource_name, {})
                listener_name = ctx.get("listener_name")
                if listener_name:
                    handler(resource_name, listener_name)
                else:
                    logger.warning(
                        f"Event {resource_name} crash context missing listener_name"
                    )
            else:
                handler(resource_name)
        except Exception as e:
            logger.exception(f"Error during auto-disable of {resource_name}: {e}")
