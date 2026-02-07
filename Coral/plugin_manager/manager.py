"""
Plugin Manager
==============

Main plugin manager class that coordinates all plugin management functionality.
"""

import os
import time
import asyncio
import logging
from typing import Dict, List, Optional, Tuple, Set

from .metadata import PluginMetadata
from .loader import PluginLoader
from .registry import PluginRegistry
from .commands import PluginCommands
from .models import PluginMeta, DependencyGraph, PluginState
from .exceptions import (
    PluginError, PluginNotFoundError, PluginDependencyError,
    PluginCompatibilityError, PluginLoadError, DependencyCycleError
)

logger = logging.getLogger(__name__)

PLUGINMANAGER_VERSION = "260207_early_development"
PLUGINMANAGER_META = 250606


class PluginManager:
    """Main plugin manager with dependency-aware concurrent loading."""
    
    def __init__(self, register, config, perm_system, plugin_dir="./plugins"):
        """
        Initialize plugin manager.
        
        Args:
            register: Register object
            config: Configuration object
            perm_system: Permission system object
            plugin_dir: Plugin directory path
        """
        self.config = config
        self.perm_system = perm_system
        self.register = register
        
        # Set plugin directory from config or use default
        self.plugin_dir = self.config.get("plugin_dir", plugin_dir)
        self.config.set("pluginmanager_version", PLUGINMANAGER_VERSION)
        
        # Initialize components
        self.metadata = PluginMetadata()
        self.loader = PluginLoader(config, register)
        self.registry = PluginRegistry(self.plugin_dir)
        self.commands = PluginCommands(self)
        
        # Plugin manager state
        self.pluginmanager_version = self.config.get("pluginmanager_version")
        self.pluginmanager_meta = PLUGINMANAGER_META
        self._is_loading = False
        
        # Create plugin directory if it doesn't exist
        if not os.path.exists(self.plugin_dir):
            os.makedirs(self.plugin_dir, exist_ok=True)
            logger.info(f"Created plugin directory: {self.plugin_dir}")
    
    async def load_all_plugins(self) -> Tuple[bool, str]:
        """
        Load all enabled plugins with dependency-aware concurrent loading.
        
        Returns:
            Tuple of (success, message)
        """
        if self._is_loading:
            return False, "Plugin loading already in progress"
        
        self._is_loading = True
        start_time = time.time()
        
        try:
            if not os.path.exists(self.plugin_dir):
                logger.warning(f"Plugin directory {self.plugin_dir} does not exist")
                return False, f"Plugin directory {self.plugin_dir} does not exist"
            
            logger.info(f"Loading plugins from {self.plugin_dir}")
            
            # 1. Discover and parse all plugin metadata
            plugin_dirs = self.metadata.get_enabled_plugin_dirs(self.plugin_dir)
            if not plugin_dirs:
                logger.info("No plugins found to load")
                return True, "No plugins found to load"
            
            plugins_meta = {}
            for plugin_dir_path in plugin_dirs:
                plugin_name = os.path.basename(plugin_dir_path)
                meta = self.metadata.get_plugin_meta(plugin_dir_path, plugin_name)
                if meta:
                    plugins_meta[plugin_name] = meta
                    # Register plugin in registry
                    self.registry.register_plugin(plugin_name, meta)
            
            if not plugins_meta:
                logger.info("No valid plugins found")
                return True, "No valid plugins found"
            
            # 2. Build dependency graph
            dependency_graph = self.metadata.build_dependency_graph(plugins_meta)
            
            # 3. Check for circular dependencies
            if dependency_graph.has_cycle():
                return False, "Circular dependency detected in plugins"
            
            # 4. Get topological sort (loading order by layers)
            try:
                load_layers = dependency_graph.topological_sort()
            except DependencyCycleError as e:
                return False, f"Dependency error: {str(e)}"
            
            # 5. Load plugins layer by layer (plugins in same layer can load concurrently)
            total_loaded = 0
            total_failed = 0
            loaded_plugins: Set[str] = set()
            
            for layer_index, layer_plugins in enumerate(load_layers):
                logger.info(f"Loading plugin layer {layer_index + 1}/{len(load_layers)}: {layer_plugins}")
                
                # Prepare plugins for this layer
                plugins_to_load = []
                for plugin_name in layer_plugins:
                    if plugin_name in plugins_meta:
                        meta = plugins_meta[plugin_name]
                        plugin_path = meta.path or os.path.join(self.plugin_dir, plugin_name)
                        plugins_to_load.append((plugin_name, plugin_path, meta))
                        
                        # Mark dependencies as met
                        deps_met = all(dep in loaded_plugins for dep in meta.dependencies)
                        self.registry.update_dependencies_met(plugin_name, deps_met)
                
                # Load plugins in this layer concurrently
                results = await self.loader.load_plugins_concurrently(
                    plugins_to_load, loaded_plugins
                )
                
                # Process results
                for plugin_name, (success, error, load_time) in results.items():
                    if success:
                        self.registry.mark_as_loaded(plugin_name, load_time)
                        total_loaded += 1
                        logger.info(f"✓ Loaded plugin {plugin_name} in {load_time:.2f}s")
                    else:
                        self.registry.mark_as_error(plugin_name, error or "Unknown error")
                        total_failed += 1
                        logger.error(f"✗ Failed to load plugin {plugin_name}: {error}")
            
            # 6. Register plugin manager commands
            self._register_commands()
            
            # 7. Log loading metrics
            load_time = time.time() - start_time
            self._log_loading_metrics(total_loaded, total_failed, load_time)
            
            message = f"Loaded {total_loaded} plugins, {total_failed} failed in {load_time:.2f}s"
            logger.info(message)
            
            return True, message
            
        except Exception as e:
            logger.exception(f"Error loading plugins: {e}")
            return False, f"Error loading plugins: {str(e)}"
        finally:
            self._is_loading = False
    
    async def load_plugin(self, plugin_name: str) -> Tuple[bool, str]:
        """
        Load a single plugin.
        
        Args:
            plugin_name: Name of plugin to load
            
        Returns:
            Tuple of (success, message)
        """
        try:
            # Check if plugin exists
            plugin_path = os.path.join(self.plugin_dir, plugin_name)
            if not os.path.isdir(plugin_path):
                # Check for disabled plugin
                disabled_path = plugin_path + ".disabled"
                if os.path.isdir(disabled_path):
                    return False, f"Plugin {plugin_name} is disabled. Use 'plugin enable {plugin_name}' first."
                return False, f"Plugin {plugin_name} not found"
            
            # Get plugin metadata
            meta = self.metadata.get_plugin_meta(plugin_path, plugin_name)
            if not meta:
                return False, f"Failed to parse metadata for plugin {plugin_name}"
            
            # Check compatibility
            if not meta.is_compatible(self.pluginmanager_meta):
                return False, f"Plugin {plugin_name} is not compatible with this version"
            
            # Check dependencies
            missing_deps = []
            for dep in meta.dependencies:
                if not self.registry.is_loaded(dep):
                    missing_deps.append(dep)
            
            if missing_deps:
                return False, f"Missing dependencies: {', '.join(missing_deps)}"
            
            # Register plugin in registry if not already registered
            if not self.registry.is_registered(plugin_name):
                self.registry.register_plugin(plugin_name, meta)
            
            # Load the plugin
            loaded_plugins = set(self.registry.get_loaded_plugins())
            success, error, load_time = await self.loader.load_plugin_with_deps(
                plugin_name, plugin_path, meta, loaded_plugins
            )
            
            if success:
                self.registry.mark_as_loaded(plugin_name, load_time)
                return True, f"Plugin {plugin_name} loaded successfully in {load_time:.2f}s"
            else:
                self.registry.mark_as_error(plugin_name, error or "Unknown error")
                return False, f"Failed to load plugin {plugin_name}: {error}"
                
        except Exception as e:
            logger.exception(f"Error loading plugin {plugin_name}: {e}")
            return False, f"Error loading plugin {plugin_name}: {str(e)}"
    
    async def unload_plugin(self, plugin_name: str) -> Tuple[bool, str]:
        """
        Unload a plugin.
        
        Args:
            plugin_name: Name of plugin to unload
            
        Returns:
            Tuple of (success, message)
        """
        if not self.registry.is_loaded(plugin_name):
            return False, f"Plugin {plugin_name} is not loaded"
        
        try:
            # Check if other plugins depend on this one
            dependents = []
            for plugin_entry in self.registry.get_loaded_plugins():
                if plugin_name in plugin_entry.meta.dependencies:
                    dependents.append(plugin_entry.name)
            
            if dependents:
                return False, f"Cannot unload {plugin_name}: other plugins depend on it: {', '.join(dependents)}"
            
            # Unload the plugin
            success = await self.loader.unload_plugin(plugin_name)
            if success:
                self.registry.mark_as_unloaded(plugin_name)
                return True, f"Plugin {plugin_name} unloaded successfully"
            else:
                return False, f"Failed to unload plugin {plugin_name}"
                
        except Exception as e:
            logger.exception(f"Error unloading plugin {plugin_name}: {e}")
            return False, f"Error unloading plugin {plugin_name}: {str(e)}"
    
    async def enable_plugin(self, plugin_name: str) -> Tuple[bool, str]:
        """
        Enable a disabled plugin.
        
        Args:
            plugin_name: Name of plugin to enable
            
        Returns:
            Tuple of (success, message)
        """
        try:
            # Check if plugin exists (disabled version)
            disabled_path = os.path.join(self.plugin_dir, plugin_name + ".disabled")
            enabled_path = os.path.join(self.plugin_dir, plugin_name)
            
            if not os.path.isdir(disabled_path):
                # Check if already enabled
                if os.path.isdir(enabled_path):
                    return False, f"Plugin {plugin_name} is already enabled"
                return False, f"Plugin {plugin_name} not found"
            
            # Rename directory to enable plugin
            os.rename(disabled_path, enabled_path)
            
            # Update registry
            self.registry.mark_as_enabled(plugin_name)
            
            # Clear metadata cache for this plugin
            self.metadata.clear_cache()
            
            logger.info(f"Enabled plugin {plugin_name}")
            return True, f"Plugin {plugin_name} enabled successfully"
            
        except Exception as e:
            logger.exception(f"Error enabling plugin {plugin_name}: {e}")
            return False, f"Error enabling plugin {plugin_name}: {str(e)}"
    
    async def disable_plugin(self, plugin_name: str) -> Tuple[bool, str]:
        """
        Disable a plugin.
        
        Args:
            plugin_name: Name of plugin to disable
            
        Returns:
            Tuple of (success, message)
        """
        try:
            # Check if plugin exists
            plugin_path = os.path.join(self.plugin_dir, plugin_name)
            disabled_path = plugin_path + ".disabled"
            
            if not os.path.isdir(plugin_path):
                # Check if already disabled
                if os.path.isdir(disabled_path):
                    return False, f"Plugin {plugin_name} is already disabled"
                return False, f"Plugin {plugin_name} not found"
            
            # Unload plugin if it's loaded
            if self.registry.is_loaded(plugin_name):
                success, message = await self.unload_plugin(plugin_name)
                if not success:
                    return False, f"Failed to unload plugin before disabling: {message}"
            
            # Rename directory to disable plugin
            os.rename(plugin_path, disabled_path)
            
            # Update registry
            self.registry.mark_as_disabled(plugin_name)
            
            # Clear metadata cache for this plugin
            self.metadata.clear_cache()
            
            logger.info(f"Disabled plugin {plugin_name}")
            return True, f"Plugin {plugin_name} disabled successfully"
            
        except Exception as e:
            logger.exception(f"Error disabling plugin {plugin_name}: {e}")
            return False, f"Error disabling plugin {plugin_name}: {str(e)}"
    
    async def reload_plugin(self, plugin_name: str) -> Tuple[bool, str]:
        """
        Reload a single plugin.
        
        Args:
            plugin_name: Name of plugin to reload
            
        Returns:
            Tuple of (success, message)
        """
        # First unload if loaded
        if self.registry.is_loaded(plugin_name):
            success, message = await self.unload_plugin(plugin_name)
            if not success:
                return False, f"Failed to unload plugin before reload: {message}"
        
        # Then load again
        return await self.load_plugin(plugin_name)
    
    async def unload_all_plugins(self) -> Tuple[bool, str]:
        """
        Unload all loaded plugins (for framework shutdown).
        
        Returns:
            Tuple of (success, message)
        """
        start_time = time.time()
        loaded_plugins = [entry.name for entry in self.registry.get_loaded_plugins()]
        
        if not loaded_plugins:
            return True, "No plugins to unload"
        
        logger.info(f"Unloading {len(loaded_plugins)} plugins for framework shutdown...")
        
        total_unloaded = 0
        total_failed = 0
        errors = []
        
        # 在框架关闭时，我们需要按依赖关系的逆序卸载插件
        # 即先卸载依赖其他插件的插件，最后卸载被依赖的插件
        # 获取依赖图信息
        from .metadata import PluginMetadata
        temp_metadata = PluginMetadata()
        
        # 收集所有插件的元数据
        plugins_meta = {}
        for plugin_name in loaded_plugins:
            plugin_info = self.registry.get_plugin_info(plugin_name)
            if plugin_info:
                plugins_meta[plugin_name] = plugin_info.meta
        
        if plugins_meta:
            # 构建依赖图
            dependency_graph = temp_metadata.build_dependency_graph(plugins_meta)
            
            # 获取拓扑排序（正向加载顺序）
            try:
                load_layers = dependency_graph.topological_sort()
                # 反转顺序得到卸载顺序（从最后加载的开始卸载）
                unload_layers = list(reversed(load_layers))
                
                # 按层卸载
                for layer_index, layer_plugins in enumerate(unload_layers):
                    logger.info(f"Unloading plugin layer {layer_index + 1}/{len(unload_layers)}: {layer_plugins}")
                    
                    # 卸载这一层的所有插件
                    for plugin_name in layer_plugins:
                        if plugin_name in loaded_plugins:
                            success, message = await self.unload_plugin(plugin_name)
                            if success:
                                total_unloaded += 1
                                logger.info(f"✓ Unloaded plugin {plugin_name}")
                            else:
                                total_failed += 1
                                errors.append(f"{plugin_name}: {message}")
                                logger.error(f"✗ Failed to unload plugin {plugin_name}: {message}")
            except Exception as e:
                logger.warning(f"Failed to determine dependency order for unloading: {e}")
                # 回退到简单顺序卸载
                for plugin_name in loaded_plugins:
                    success, message = await self.unload_plugin(plugin_name)
                    if success:
                        total_unloaded += 1
                        logger.info(f"✓ Unloaded plugin {plugin_name}")
                    else:
                        total_failed += 1
                        errors.append(f"{plugin_name}: {message}")
                        logger.error(f"✗ Failed to unload plugin {plugin_name}: {message}")
        else:
            # 没有元数据信息，简单顺序卸载
            for plugin_name in loaded_plugins:
                success, message = await self.unload_plugin(plugin_name)
                if success:
                    total_unloaded += 1
                    logger.info(f"✓ Unloaded plugin {plugin_name}")
                else:
                    total_failed += 1
                    errors.append(f"{plugin_name}: {message}")
                    logger.error(f"✗ Failed to unload plugin {plugin_name}: {message}")
        
        # 清理注册表和缓存
        self.registry.clear()
        self.metadata.clear_cache()
        
        unload_time = time.time() - start_time
        message = f"Unloaded {total_unloaded} plugins, {total_failed} failed in {unload_time:.2f}s"
        
        if errors:
            message += f". Errors: {', '.join(errors[:3])}"  # 只显示前3个错误
        
        logger.info(message)
        return total_failed == 0, message
    
    async def reload_all_plugins(self) -> Tuple[bool, str]:
        """
        Reload all plugins.
        
        Returns:
            Tuple of (success, message)
        """
        # Unload all loaded plugins
        loaded_plugins = [entry.name for entry in self.registry.get_loaded_plugins()]
        for plugin_name in loaded_plugins:
            await self.unload_plugin(plugin_name)
        
        # Clear registry and metadata cache
        self.registry.clear()
        self.metadata.clear_cache()
        
        # Load all plugins again
        return await self.load_all_plugins()
    
    async def list_plugins(self, filter_type: str = "all") -> str:
        """
        List plugins with optional filter.
        
        Args:
            filter_type: Filter type (all, loaded, enabled, disabled)
            
        Returns:
            Formatted plugin list
        """
        filter_type = filter_type.lower()
        
        if filter_type == "loaded":
            plugins = self.registry.get_loaded_plugins()
            title = "Loaded Plugins"
        elif filter_type == "enabled":
            plugins = self.registry.get_enabled_plugins()
            title = "Enabled Plugins"
        elif filter_type == "disabled":
            plugins = self.registry.get_disabled_plugins()
            title = "Disabled Plugins"
        else:  # "all"
            plugins = self.registry.get_all_plugins()
            title = "All Plugins"
        
        if not plugins:
            return f"{title}: No plugins found"
        
        lines = [f"{title} ({len(plugins)}):"]
        lines.append("-" * 40)
        
        for plugin in plugins:
            status = "✓" if plugin.is_loaded else "✗"
            disabled = " (disabled)" if plugin.is_disabled else ""
            version = f" v{plugin.meta.version}" if plugin.meta.version != "1.0.0" else ""
            
            line = f"{status} {plugin.name}{version}{disabled}"
            if plugin.meta.description:
                line += f" - {plugin.meta.description}"
            
            lines.append(line)
        
        # Add counts summary
        counts = self.registry.get_plugin_count()
        lines.append("-" * 40)
        lines.append(f"Total: {counts['total']}, Loaded: {counts['loaded']}, "
                    f"Enabled: {counts['enabled']}, Disabled: {counts['disabled']}")
        
        return "\n".join(lines)
    
    async def get_plugin_stats(self, plugin_name: str) -> str:
        """
        Get statistics for a specific plugin.
        
        Args:
            plugin_name: Name of plugin
            
        Returns:
            Formatted statistics
        """
        plugin_info = self.registry.get_plugin_info(plugin_name)
        if not plugin_info:
            raise PluginNotFoundError(f"Plugin {plugin_name} not found")
        
        metrics = plugin_info.metrics
        meta = plugin_info.meta
        
        lines = [
            f"Statistics for plugin: {plugin_name}",
            "-" * 40,
            f"Version: {meta.version}",
            f"Author: {meta.author}",
            f"State: {plugin_info.state.value}",
            f"Load Status: {plugin_info.load_status.value if plugin_info.load_status else 'N/A'}",
            "",
            "Performance Metrics:",
            f"  Load Time: {metrics.load_time:.2f}s",
            f"  Load Count: {metrics.load_count}",
            f"  Unload Count: {metrics.unload_count}",
            f"  Last Loaded: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(metrics.last_loaded))}",
            f"  Total Calls: {metrics.total_calls}",
            f"  Avg Execution Time: {metrics.avg_execution_time:.3f}s",
            f"  Total Errors: {metrics.total_errors}",
            f"  Last Error: {metrics.last_error or 'None'}",
            "",
            "Dependencies:",
        ]
        
        if meta.dependencies:
            for dep in meta.dependencies:
                dep_loaded = "✓" if self.registry.is_loaded(dep) else "✗"
                lines.append(f"  {dep_loaded} {dep}")
        else:
            lines.append("  None")
        
        lines.append("")
        lines.append(f"Description: {meta.description}")
        
        return "\n".join(lines)
    
    async def get_overall_stats(self) -> str:
        """
        Get overall plugin statistics.
        
        Returns:
            Formatted statistics
        """
        counts = self.registry.get_plugin_count()
        loaded_plugins = self.registry.get_loaded_plugins()
        
        # Calculate total load time
        total_load_time = sum(plugin.metrics.load_time for plugin in loaded_plugins)
        avg_load_time = total_load_time / len(loaded_plugins) if loaded_plugins else 0
        
        # Calculate total errors
        total_errors = sum(plugin.metrics.total_errors for plugin in loaded_plugins)
        
        # Calculate total calls
        total_calls = sum(plugin.metrics.total_calls for plugin in loaded_plugins)
        avg_execution_time = sum(plugin.metrics.avg_execution_time for plugin in loaded_plugins) / len(loaded_plugins) if loaded_plugins else 0
        
        lines = [
            "Overall Plugin Statistics",
            "-" * 40,
            f"Plugin Manager Version: {self.pluginmanager_version}",
            f"Plugin Directory: {self.plugin_dir}",
            "",
            "Plugin Counts:",
            f"  Total Plugins: {counts['total']}",
            f"  Loaded: {counts['loaded']}",
            f"  Enabled: {counts['enabled']}",
            f"  Disabled: {counts['disabled']}",
            "",
            "Performance Metrics:",
            f"  Total Load Time: {total_load_time:.2f}s",
            f"  Average Load Time: {avg_load_time:.2f}s",
            f"  Total Errors: {total_errors}",
            f"  Total Calls: {total_calls}",
            f"  Average Execution Time: {avg_execution_time:.3f}s",
            "",
            "Plugin Manager Status:",
            f"  Is Loading: {'Yes' if self._is_loading else 'No'}",
            f"  Compatibility Version: {self.pluginmanager_meta}"
        ]
        
        return "\n".join(lines)
    
    async def get_plugin_info(self, plugin_name: str) -> str:
        """
        Get detailed information about a plugin.
        
        Args:
            plugin_name: Name of plugin
            
        Returns:
            Formatted plugin information
        """
        plugin_info = self.registry.get_plugin_info(plugin_name)
        if not plugin_info:
            raise PluginNotFoundError(f"Plugin {plugin_name} not found")
        
        meta = plugin_info.meta
        
        lines = [
            f"Plugin Information: {plugin_name}",
            "-" * 40,
            f"Name: {meta.name}",
            f"Version: {meta.version}",
            f"Author: {meta.author}",
            f"Compatibility: {meta.compatibility}",
            f"State: {plugin_info.state.value}",
            f"Disabled: {'Yes' if plugin_info.is_disabled else 'No'}",
            f"Loaded: {'Yes' if plugin_info.is_loaded else 'No'}",
            f"Can Load: {'Yes' if plugin_info.can_load else 'No'}",
            f"Dependencies Met: {'Yes' if plugin_info.dependencies_met else 'No'}",
            "",
            "Description:",
            f"  {meta.description}",
            "",
            "Dependencies:"
        ]
        
        if meta.dependencies:
            for dep in meta.dependencies:
                dep_loaded = "✓" if self.registry.is_loaded(dep) else "✗"
                dep_exists = "✓" if self.registry.is_registered(dep) else "✗"
                lines.append(f"  {dep_loaded} {dep} (exists: {dep_exists})")
        else:
            lines.append("  None")
        
        lines.append("")
        lines.append("Requirements:")
        
        if meta.requirements:
            for req in meta.requirements:
                lines.append(f"  {req}")
        else:
            lines.append("  None")
        
        lines.append("")
        lines.append(f"Path: {meta.path or 'Unknown'}")
        
        if plugin_info.error_message:
            lines.append("")
            lines.append(f"Last Error: {plugin_info.error_message}")
        
        return "\n".join(lines)
    
    def _register_commands(self):
        """Register plugin manager commands and permissions."""
        # Register permissions
        self.commands.register_permissions(self.perm_system)
        
        # Register plugin command
        self.register.register_command(
            "plugin",
            "Plugin management commands",
            self.commands.handle_plugin_command,
            ["plugin"]
        )
        
        # Register legacy commands for backward compatibility
        self.register.register_command(
            "plugins",
            "List all available plugins (legacy)",
            self._handle_legacy_plugins_command,
            ["plugin", "plugin.list"]
        )
        
        self.register.register_command(
            "plugin_metrics",
            "Show plugin performance metrics (legacy)",
            self._handle_legacy_metrics_command,
            ["plugin", "plugin.stats"]
        )
        
        self.register.register_command(
            "reload",
            "Reload all plugins (legacy)",
            self._handle_legacy_reload_command,
            ["plugin", "plugin.reload"]
        )
        
        logger.debug("Plugin manager commands registered")
    
    async def _handle_legacy_plugins_command(self, event):
        """Handle legacy plugins command."""
        return await self.list_plugins("all")
    
    async def _handle_legacy_metrics_command(self, event):
        """Handle legacy plugin_metrics command."""
        return await self.get_overall_stats()
    
    async def _handle_legacy_reload_command(self, event):
        """Handle legacy reload command."""
        success, message = await self.reload_all_plugins()
        return message
    
    def _log_loading_metrics(self, total_loaded: int, total_failed: int, total_time: float):
        """Log loading performance metrics."""
        logger.info(
            f"Plugin loading completed: "
            f"Loaded: {total_loaded}, Failed: {total_failed}, "
            f"Total time: {total_time:.2f}s"
        )
        
        if total_loaded > 0:
            avg_time = total_time / total_loaded
            logger.info(f"Average load time per plugin: {avg_time:.2f}s")
    
    def cleanup(self):
        """Clean up plugin manager resources."""
        self.loader.cleanup()
        self.registry.clear()
        self.metadata.clear_cache()
        logger.debug("Plugin manager cleaned up")
