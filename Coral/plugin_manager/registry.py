"""
Plugin Registry
===============

Manages plugin state, tracking, and lifecycle.
"""

import os
import time
import logging
from typing import Dict, Set, Optional, List, Any
from dataclasses import dataclass, field

from .models import PluginMeta, PluginMetrics, PluginState, PluginInfo, PluginLoadStatus
from .exceptions import PluginStateError, PluginNotFoundError

logger = logging.getLogger(__name__)


@dataclass
class PluginEntry:
    """Entry for a plugin in the registry."""
    name: str
    meta: PluginMeta
    state: PluginState = PluginState.UNLOADED
    metrics: PluginMetrics = field(default_factory=PluginMetrics)
    load_status: Optional[PluginLoadStatus] = None
    error_message: Optional[str] = None
    dependencies_met: bool = False
    loaded_at: Optional[float] = None
    
    @property
    def is_loaded(self) -> bool:
        """Check if plugin is loaded."""
        return self.state == PluginState.LOADED
    
    @property
    def is_disabled(self) -> bool:
        """Check if plugin is disabled."""
        return self.state == PluginState.DISABLED or self.meta.disabled
    
    @property
    def can_load(self) -> bool:
        """Check if plugin can be loaded."""
        return (
            not self.is_loaded 
            and not self.is_disabled 
            and self.dependencies_met
            and self.load_status != PluginLoadStatus.FAILED
        )
    
    def to_info(self) -> PluginInfo:
        """Convert to PluginInfo object."""
        return PluginInfo(
            name=self.name,
            meta=self.meta,
            state=self.state,
            metrics=self.metrics,
            load_status=self.load_status,
            error_message=self.error_message,
            dependencies_met=self.dependencies_met
        )


class PluginRegistry:
    """Plugin registry for tracking plugin state and lifecycle."""
    
    def __init__(self, plugin_dir: str = "./plugins"):
        """
        Initialize plugin registry.
        
        Args:
            plugin_dir: Base plugin directory
        """
        self.plugin_dir = plugin_dir
        self._plugins: Dict[str, PluginEntry] = {}
        self._loaded_plugins: Set[str] = set()
        self._disabled_plugins: Set[str] = set()
        
        # Create plugin directory if it doesn't exist
        if not os.path.exists(self.plugin_dir):
            os.makedirs(self.plugin_dir, exist_ok=True)
            logger.info(f"Created plugin directory: {self.plugin_dir}")
    
    def register_plugin(self, name: str, meta: PluginMeta) -> PluginEntry:
        """
        Register a plugin in the registry.
        
        Args:
            name: Plugin name
            meta: Plugin metadata
            
        Returns:
            PluginEntry object
        """
        if name in self._plugins:
            logger.debug(f"Plugin {name} already registered, updating metadata")
            self._plugins[name].meta = meta
        else:
            entry = PluginEntry(name=name, meta=meta)
            self._plugins[name] = entry
        
        # Update disabled state
        if meta.disabled:
            self._disabled_plugins.add(name)
        elif name in self._disabled_plugins:
            self._disabled_plugins.remove(name)
        
        return self._plugins[name]
    
    def get_plugin(self, name: str) -> Optional[PluginEntry]:
        """Get plugin entry by name."""
        return self._plugins.get(name)
    
    def get_plugin_info(self, name: str) -> Optional[PluginInfo]:
        """Get plugin info by name."""
        entry = self.get_plugin(name)
        return entry.to_info() if entry else None
    
    def get_all_plugins(self) -> List[PluginEntry]:
        """Get all registered plugins."""
        return list(self._plugins.values())
    
    def get_loaded_plugins(self) -> List[PluginEntry]:
        """Get all loaded plugins."""
        return [entry for entry in self._plugins.values() if entry.is_loaded]
    
    def get_enabled_plugins(self) -> List[PluginEntry]:
        """Get all enabled (not disabled) plugins."""
        return [entry for entry in self._plugins.values() if not entry.is_disabled]
    
    def get_disabled_plugins(self) -> List[PluginEntry]:
        """Get all disabled plugins."""
        return [entry for entry in self._plugins.values() if entry.is_disabled]
    
    def mark_as_loaded(self, name: str, load_time: float = 0.0) -> bool:
        """
        Mark a plugin as loaded.
        
        Args:
            name: Plugin name
            load_time: Load time in seconds
            
        Returns:
            True if successful, False if plugin not found
        """
        entry = self.get_plugin(name)
        if not entry:
            return False
        
        entry.state = PluginState.LOADED
        entry.load_status = PluginLoadStatus.SUCCESS
        entry.loaded_at = time.time()
        entry.metrics.record_load(load_time)
        self._loaded_plugins.add(name)
        
        logger.debug(f"Marked plugin {name} as loaded")
        return True
    
    def mark_as_unloaded(self, name: str) -> bool:
        """
        Mark a plugin as unloaded.
        
        Args:
            name: Plugin name
            
        Returns:
            True if successful, False if plugin not found
        """
        entry = self.get_plugin(name)
        if not entry:
            return False
        
        entry.state = PluginState.UNLOADED
        entry.load_status = None
        entry.loaded_at = None
        entry.metrics.unload_count += 1
        
        if name in self._loaded_plugins:
            self._loaded_plugins.remove(name)
        
        logger.debug(f"Marked plugin {name} as unloaded")
        return True
    
    def mark_as_error(self, name: str, error_message: str) -> bool:
        """
        Mark a plugin as in error state.
        
        Args:
            name: Plugin name
            error_message: Error message
            
        Returns:
            True if successful, False if plugin not found
        """
        entry = self.get_plugin(name)
        if not entry:
            return False
        
        entry.state = PluginState.ERROR
        entry.load_status = PluginLoadStatus.FAILED
        entry.error_message = error_message
        entry.metrics.record_error(error_message)
        
        if name in self._loaded_plugins:
            self._loaded_plugins.remove(name)
        
        logger.debug(f"Marked plugin {name} as error: {error_message}")
        return True
    
    def mark_as_disabled(self, name: str) -> bool:
        """
        Mark a plugin as disabled.
        
        Args:
            name: Plugin name
            
        Returns:
            True if successful, False if plugin not found
        """
        entry = self.get_plugin(name)
        if not entry:
            return False
        
        entry.state = PluginState.DISABLED
        entry.meta.disabled = True
        self._disabled_plugins.add(name)
        
        # If plugin was loaded, mark it as unloaded
        if entry.is_loaded:
            self.mark_as_unloaded(name)
        
        logger.debug(f"Marked plugin {name} as disabled")
        return True
    
    def mark_as_enabled(self, name: str) -> bool:
        """
        Mark a plugin as enabled.
        
        Args:
            name: Plugin name
            
        Returns:
            True if successful, False if plugin not found
        """
        entry = self.get_plugin(name)
        if not entry:
            return False
        
        entry.state = PluginState.ENABLED
        entry.meta.disabled = False
        
        if name in self._disabled_plugins:
            self._disabled_plugins.remove(name)
        
        logger.debug(f"Marked plugin {name} as enabled")
        return True
    
    def update_dependencies_met(self, name: str, dependencies_met: bool) -> bool:
        """
        Update whether plugin dependencies are met.
        
        Args:
            name: Plugin name
            dependencies_met: Whether dependencies are met
            
        Returns:
            True if successful, False if plugin not found
        """
        entry = self.get_plugin(name)
        if not entry:
            return False
        
        entry.dependencies_met = dependencies_met
        return True
    
    def is_loaded(self, name: str) -> bool:
        """Check if plugin is loaded."""
        entry = self.get_plugin(name)
        return entry.is_loaded if entry else False
    
    def is_disabled(self, name: str) -> bool:
        """Check if plugin is disabled."""
        entry = self.get_plugin(name)
        return entry.is_disabled if entry else False
    
    def is_registered(self, name: str) -> bool:
        """Check if plugin is registered."""
        return name in self._plugins
    
    def get_plugin_count(self) -> Dict[str, int]:
        """Get plugin counts by state."""
        total = len(self._plugins)
        loaded = len(self._loaded_plugins)
        disabled = len(self._disabled_plugins)
        enabled = total - disabled
        
        return {
            "total": total,
            "loaded": loaded,
            "enabled": enabled,
            "disabled": disabled
        }
    
    def clear(self):
        """Clear the registry."""
        self._plugins.clear()
        self._loaded_plugins.clear()
        self._disabled_plugins.clear()
        logger.debug("Plugin registry cleared")
    
    def remove_plugin(self, name: str) -> bool:
        """
        Remove a plugin from the registry.
        
        Args:
            name: Plugin name
            
        Returns:
            True if successful, False if plugin not found
        """
        if name not in self._plugins:
            return False
        
        del self._plugins[name]
        
        if name in self._loaded_plugins:
            self._loaded_plugins.remove(name)
        
        if name in self._disabled_plugins:
            self._disabled_plugins.remove(name)
        
        logger.debug(f"Removed plugin {name} from registry")
        return True