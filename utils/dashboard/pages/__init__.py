"""
Dashboard页面模块

提供各个功能页面的实现。
"""

from .overview import OverviewPage
from .plugins import PluginsPage
from .adapters import AdaptersPage
from .drivers import DriversPage
from .config import ConfigPage
from .permissions import PermissionsPage
from .event_bus import EventBusPage
from .terminal import TerminalPage

__all__ = [
    "OverviewPage",
    "PluginsPage",
    "AdaptersPage",
    "DriversPage",
    "ConfigPage",
    "PermissionsPage",
    "EventBusPage",
    "TerminalPage",
]