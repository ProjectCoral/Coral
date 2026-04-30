"""
Function Registry
=================

Manages function registration and execution.
"""

import logging
from typing import Dict, Callable

logger = logging.getLogger(__name__)


class FunctionRegistry:
    """Registry for managing functions."""

    def __init__(self, event_bus):
        """
        Initialize function registry.

        Args:
            event_bus: Event bus instance
        """
        self.event_bus = event_bus
        self.functions: Dict[str, Callable] = {}
        self.crash_tracker = None

    def set_crash_tracker(self, crash_tracker):
        """Set crash tracker for error reporting."""
        self.crash_tracker = crash_tracker

    def register_function(self, function_name: str, function: Callable):
        """
        Register a function.

        Args:
            function_name: Name of the function
            function: Function handler
        """
        if function_name in self.functions:
            logger.error(
                f"[red bold]Function [/]{function_name}[red bold] already registered[/]"
            )
            return
        self.functions[function_name] = function

    def unregister_function(self, function_name: str):
        """
        Unregister a function.

        Args:
            function_name: Name of the function to unregister
        """
        if function_name in self.functions:
            del self.functions[function_name]

    def get_all_functions(self) -> Dict[str, Callable]:
        """Get all registered functions."""
        return self.functions.copy()

    async def execute_function(self, function_name: str, *args, **kwargs):
        """
        Execute a registered function.

        Args:
            function_name: Name of the function to execute
            *args: Positional arguments
            **kwargs: Keyword arguments

        Returns:
            Function result or None on error

        Raises:
            ValueError: If function not found
        """
        if function_name in self.functions:
            try:
                result = await self.functions[function_name](*args, **kwargs)
                return result
            except Exception as e:
                logger.exception(
                    f"[red]Error executing function {function_name}: {e}[/]"
                )
                if self.crash_tracker:
                    import traceback

                    self.crash_tracker.record_crash(
                        "function",
                        function_name,
                        str(e),
                        traceback.format_exc(),
                    )
                return None
        raise ValueError(
            f"Function {function_name} not found, " f"probably you forget register it"
        )

    def clear(self):
        """Clear all functions."""
        self.functions.clear()
