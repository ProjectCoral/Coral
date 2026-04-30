"""
Coral Core - 核心模块

此模块包含 Coral 的核心常量和组件。
常量（CORAL_VERSION, PLUGIN_DIR, CONFIG_FILE）在模块加载时即可访问，
无需等待核心组件完全初始化。
"""

# Constants - defined first for lazy access
CORAL_VERSION = "260430_early_development"
PLUGIN_DIR = "./plugins"
CONFIG_FILE = "./config.json"

# Version imports from submodules
from ..protocol import PROTOCOL_VERSION
from ..plugin import PLUGINMANAGER_VERSION

__all__ = [
    "CORAL_VERSION",
    "PLUGIN_DIR",
    "CONFIG_FILE",
    "PROTOCOL_VERSION",
    "PLUGINMANAGER_VERSION",
    "get_container",
    "core_reload",
]


# Lazy import - only load heavy components when explicitly accessed
def __getattr__(name):
    if name in (
        "config",
        "event_bus",
        "register",
        "perm_system",
        "plugin_manager",
        "adapter_manager",
        "driver_manager",
    ):
        from . import core

        return getattr(core, name)
    if name == "get_container":
        from . import core

        return core._container.resolve
    if name == "core_reload":
        from . import core

        return core.core_reload
    raise AttributeError(f"module 'Coral.core' has no attribute '{name}'")
