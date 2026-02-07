"""
Plugin Manager Module
=====================

A refactored plugin management system with dependency-aware concurrent loading
and comprehensive plugin management commands.
"""

from .manager import (
    PluginManager,
    PLUGINMANAGER_META,
    PLUGINMANAGER_VERSION
)
from .exceptions import (
    PluginError,
    PluginNotFoundError,
    PluginDependencyError,
    PluginCompatibilityError,
    PluginLoadError
)


__all__ = [
    'PluginManager',
    'PluginError',
    'PluginNotFoundError',
    'PluginDependencyError',
    'PluginCompatibilityError',
    'PluginLoadError',
    'PLUGINMANAGER_VERSION'
]

__version__ = PLUGINMANAGER_VERSION

__meta__ = PLUGINMANAGER_META