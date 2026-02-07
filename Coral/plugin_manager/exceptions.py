"""
Plugin Manager Exceptions
=========================

Custom exceptions for the plugin management system.
"""


class PluginError(Exception):
    """Base exception for all plugin-related errors."""
    pass


class PluginNotFoundError(PluginError):
    """Raised when a plugin is not found."""
    pass


class PluginDependencyError(PluginError):
    """Raised when plugin dependencies cannot be resolved."""
    pass


class PluginCompatibilityError(PluginError):
    """Raised when plugin compatibility check fails."""
    pass


class PluginLoadError(PluginError):
    """Raised when plugin loading fails."""
    pass


class PluginUnloadError(PluginError):
    """Raised when plugin unloading fails."""
    pass


class PluginStateError(PluginError):
    """Raised when plugin state operations fail."""
    pass


class PluginMetadataError(PluginError):
    """Raised when plugin metadata is invalid or cannot be parsed."""
    pass


class DependencyCycleError(PluginDependencyError):
    """Raised when a circular dependency is detected."""
    pass