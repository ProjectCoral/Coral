"""
Registry Module
===============

Plugin registries for managing commands, functions, and events.
"""

from .command import CommandRegistry
from .function import FunctionRegistry
from .event import EventRegistry

__all__ = ["CommandRegistry", "FunctionRegistry", "EventRegistry"]
