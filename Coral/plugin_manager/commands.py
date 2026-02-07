"""
Plugin Commands
===============

Command handlers for plugin management commands with 'plugin' prefix.
"""

import logging
from typing import List
from dataclasses import asdict

from Coral.protocol import CommandEvent, MessageRequest, MessageChain, MessageSegment

from .models import PluginState, PluginLoadStatus
from .exceptions import PluginNotFoundError, PluginStateError

logger = logging.getLogger(__name__)


class PluginCommands:
    """Plugin command handlers."""
    
    def __init__(self, plugin_manager):
        """
        Initialize plugin commands.
        
        Args:
            plugin_manager: PluginManager instance
        """
        self.plugin_manager = plugin_manager
    
    async def handle_plugin_command(self, event: CommandEvent) -> MessageRequest:
        """
        Handle plugin command with subcommands.
        
        Args:
            event: Command event
            
        Returns:
            MessageRequest with response
        """
        if not event.args:
            return "Usage: plugin <subcommand> [args]\n" \
                   "Subcommands: load, unload, enable, disable, list, stats, info, reload"
        
        subcommand = event.args[0].lower()
        
        # Map subcommands to handler methods
        handlers = {
            'load': self.handle_load,
            'unload': self.handle_unload,
            'enable': self.handle_enable,
            'disable': self.handle_disable,
            'list': self.handle_list,
            'stats': self.handle_stats,
            'info': self.handle_info,
            'reload': self.handle_reload,
            'help': self.handle_help
        }
        
        handler = handlers.get(subcommand)
        if not handler:
            return f"Unknown subcommand: {subcommand}\n" \
                   f"Available: load, unload, enable, disable, list, stats, info, reload, help"
        
        try:
            # Call handler with remaining args
            result = await handler(event, event.args[1:])
            if isinstance(result, MessageRequest):
                return result
            else:
                return str(result)
        except Exception as e:
            logger.exception(f"Error handling plugin command {subcommand}: {e}")
            return f"Error: {str(e)}"
    
    async def handle_load(self, event: CommandEvent, args: List[str]) -> str:
        """
        Handle plugin load command.
        
        Usage: plugin load <plugin_name>
        """
        if not args:
            return "Usage: plugin load <plugin_name>"
        
        plugin_name = args[0]
        
        try:
            success, message = await self.plugin_manager.load_plugin(plugin_name)
            if success:
                return f"Plugin '{plugin_name}' loaded successfully."
            else:
                return f"Failed to load plugin '{plugin_name}': {message}"
        except PluginNotFoundError:
            return f"Plugin '{plugin_name}' not found."
        except Exception as e:
            return f"Error loading plugin '{plugin_name}': {str(e)}"
    
    async def handle_unload(self, event: CommandEvent, args: List[str]) -> str:
        """
        Handle plugin unload command.
        
        Usage: plugin unload <plugin_name>
        """
        if not args:
            return "Usage: plugin unload <plugin_name>"
        
        plugin_name = args[0]
        
        try:
            success, message = await self.plugin_manager.unload_plugin(plugin_name)
            if success:
                return f"Plugin '{plugin_name}' unloaded successfully."
            else:
                return f"Failed to unload plugin '{plugin_name}': {message}"
        except PluginNotFoundError:
            return f"Plugin '{plugin_name}' not found or not loaded."
        except Exception as e:
            return f"Error unloading plugin '{plugin_name}': {str(e)}"
    
    async def handle_enable(self, event: CommandEvent, args: List[str]) -> str:
        """
        Handle plugin enable command.
        
        Usage: plugin enable <plugin_name>
        """
        if not args:
            return "Usage: plugin enable <plugin_name>"
        
        plugin_name = args[0]
        
        try:
            success, message = await self.plugin_manager.enable_plugin(plugin_name)
            if success:
                return f"Plugin '{plugin_name}' enabled successfully."
            else:
                return f"Failed to enable plugin '{plugin_name}': {message}"
        except PluginNotFoundError:
            return f"Plugin '{plugin_name}' not found."
        except Exception as e:
            return f"Error enabling plugin '{plugin_name}': {str(e)}"
    
    async def handle_disable(self, event: CommandEvent, args: List[str]) -> str:
        """
        Handle plugin disable command.
        
        Usage: plugin disable <plugin_name>
        """
        if not args:
            return "Usage: plugin disable <plugin_name>"
        
        plugin_name = args[0]
        
        try:
            success, message = await self.plugin_manager.disable_plugin(plugin_name)
            if success:
                return f"Plugin '{plugin_name}' disabled successfully."
            else:
                return f"Failed to disable plugin '{plugin_name}': {message}"
        except PluginNotFoundError:
            return f"Plugin '{plugin_name}' not found."
        except Exception as e:
            return f"Error disabling plugin '{plugin_name}': {str(e)}"
    
    async def handle_list(self, event: CommandEvent, args: List[str]) -> str:
        """
        Handle plugin list command.
        
        Usage: plugin list [filter]
        """
        filter_type = args[0].lower() if args else "all"
        
        try:
            plugins_info = await self.plugin_manager.list_plugins(filter_type)
            return plugins_info
        except Exception as e:
            return f"Error listing plugins: {str(e)}"
    
    async def handle_stats(self, event: CommandEvent, args: List[str]) -> str:
        """
        Handle plugin stats command.
        
        Usage: plugin stats [plugin_name]
        """
        plugin_name = args[0] if args else None
        
        try:
            if plugin_name:
                stats = await self.plugin_manager.get_plugin_stats(plugin_name)
                return stats
            else:
                stats = await self.plugin_manager.get_overall_stats()
                return stats
        except PluginNotFoundError:
            return f"Plugin '{plugin_name}' not found." if plugin_name else "No plugins found."
        except Exception as e:
            return f"Error getting stats: {str(e)}"
    
    async def handle_info(self, event: CommandEvent, args: List[str]) -> str:
        """
        Handle plugin info command.
        
        Usage: plugin info <plugin_name>
        """
        if not args:
            return "Usage: plugin info <plugin_name>"
        
        plugin_name = args[0]
        
        try:
            info = await self.plugin_manager.get_plugin_info(plugin_name)
            return info
        except PluginNotFoundError:
            return f"Plugin '{plugin_name}' not found."
        except Exception as e:
            return f"Error getting plugin info: {str(e)}"
    
    async def handle_reload(self, event: CommandEvent, args: List[str]) -> str:
        """
        Handle plugin reload command.
        
        Usage: plugin reload [plugin_name]
        """
        plugin_name = args[0] if args else None
        
        try:
            if plugin_name:
                success, message = await self.plugin_manager.reload_plugin(plugin_name)
                if success:
                    return f"Plugin '{plugin_name}' reloaded successfully."
                else:
                    return f"Failed to reload plugin '{plugin_name}': {message}"
            else:
                success, message = await self.plugin_manager.reload_all_plugins()
                if success:
                    return "All plugins reloaded successfully."
                else:
                    return f"Failed to reload plugins: {message}"
        except PluginNotFoundError:
            return f"Plugin '{plugin_name}' not found." if plugin_name else "No plugins found."
        except Exception as e:
            return f"Error reloading: {str(e)}"
    
    async def handle_help(self, event: CommandEvent, args: List[str]) -> str:
        """
        Handle plugin help command.
        
        Usage: plugin help [command]
        """
        if args:
            command = args[0].lower()
            help_texts = {
                'load': "plugin load <plugin_name>\n  Load a specific plugin.",
                'unload': "plugin unload <plugin_name>\n  Unload a specific plugin.",
                'enable': "plugin enable <plugin_name>\n  Enable a disabled plugin.",
                'disable': "plugin disable <plugin_name>\n  Disable a plugin (adds .disabled suffix).",
                'list': "plugin list [all|loaded|enabled|disabled]\n  List plugins with optional filter.",
                'stats': "plugin stats [plugin_name]\n  Show plugin statistics.",
                'info': "plugin info <plugin_name>\n  Show detailed plugin information.",
                'reload': "plugin reload [plugin_name]\n  Reload plugin(s).",
                'help': "plugin help [command]\n  Show help for plugin commands."
            }
            
            if command in help_texts:
                return help_texts[command]
            else:
                return f"No help available for command: {command}"
        
        # General help
        help_text = """Plugin Management Commands:
        
plugin load <plugin_name>      - Load a specific plugin
plugin unload <plugin_name>    - Unload a specific plugin
plugin enable <plugin_name>    - Enable a disabled plugin
plugin disable <plugin_name>   - Disable a plugin (adds .disabled suffix)
plugin list [filter]           - List plugins (all|loaded|enabled|disabled)
plugin stats [plugin_name]     - Show plugin statistics
plugin info <plugin_name>      - Show detailed plugin information
plugin reload [plugin_name]    - Reload plugin(s)
plugin help [command]          - Show help for plugin commands

Examples:
  plugin list all
  plugin load myplugin
  plugin stats
  plugin info myplugin"""
        
        return help_text
    
    def register_permissions(self, perm_system):
        """Register plugin command permissions."""
        perm_system.register_perm("plugin", "Base plugin management permission")
        perm_system.register_perm("plugin.load", "Permission to load plugins")
        perm_system.register_perm("plugin.unload", "Permission to unload plugins")
        perm_system.register_perm("plugin.enable", "Permission to enable plugins")
        perm_system.register_perm("plugin.disable", "Permission to disable plugins")
        perm_system.register_perm("plugin.list", "Permission to list plugins")
        perm_system.register_perm("plugin.stats", "Permission to view plugin statistics")
        perm_system.register_perm("plugin.info", "Permission to view plugin information")
        perm_system.register_perm("plugin.reload", "Permission to reload plugins")
        
        # Default permission mapping for commands
        self._permission_map = {
            'load': ["plugin", "plugin.load"],
            'unload': ["plugin", "plugin.unload"],
            'enable': ["plugin", "plugin.enable"],
            'disable': ["plugin", "plugin.disable"],
            'list': ["plugin", "plugin.list"],
            'stats': ["plugin", "plugin.stats"],
            'info': ["plugin", "plugin.info"],
            'reload': ["plugin", "plugin.reload"],
            'help': ["plugin", "plugin.list"]  # help requires list permission
        }
    
    def get_permission(self, subcommand: str) -> list:
        """Get required permissions for a subcommand."""
        return self._permission_map.get(subcommand, ["plugin"])