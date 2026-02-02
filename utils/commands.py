import os
import time
import logging
from typing import List, Optional, Tuple, Any
from Coral import register, config, perm_system
from Coral.protocol import CommandEvent, MessageSegment, UserInfo, MessageChain, MessageRequest

logger = logging.getLogger(__name__)

def register_plugin() -> None:
    """
    Register the base commands plugin with the Coral system.
    
    This function registers permissions and commands for basic system operations
    including help, cache clearing, and status display.
    """
    # Register permissions
    perm_system.register_perm("base_commands", "Base Permission")
    perm_system.register_perm("base_commands.help", "User can use the help command")
    perm_system.register_perm("base_commands.clear", "User can clear the cache")
    perm_system.register_perm("base_commands.status", "User can see the status of Coral")
    
    # Create instance and register commands
    commands_instance = base_commands(register, config, perm_system)
    
    register.register_command('help', 'Show help message', 
                             commands_instance.show_help, 
                             ["base_commands", "base_commands.help"])
    register.register_command('clear', 'Clear cache', 
                             commands_instance.clear_cache, 
                             ["base_commands", "base_commands.clear"])
    register.register_command('status', 'Show status of Coral', 
                             commands_instance.status, 
                             ["base_commands", "base_commands.status"])
    register.register_event("coral_initialized", "init_time", 
                           commands_instance.init_timer, 1)

class base_commands:
    """Base commands plugin providing essential system commands."""
    
    def __init__(self, register, config, perm_system):
        """
        Initialize the base commands plugin.
        
        Args:
            register: Coral register instance
            config: Coral config instance
            perm_system: Coral permission system instance
        """
        self.register = register
        self.config = config
        self.perm_system = perm_system
        self.init_time: Optional[float] = None
        
    async def init_timer(self, *args: Any) -> Tuple[None, bool, int]:
        """
        Initialize the timer when Coral starts.
        
        Returns:
            Tuple containing (None, False, 1) as expected by event system
        """
        self.init_time = time.time()
        logger.debug("Base commands timer initialized")
        return None, False, 1
    
    async def show_help(self, *args: Any) -> str:
        """
        Show help message with all available commands.
        
        Returns:
            Formatted help string listing all registered commands
        """
        try:
            commands_list = []
            for command_name in self.register.commands:
                description = self.register.get_command_description(command_name)
                commands_list.append(f"{command_name}: {description}")
            
            return "List of available commands:\n" + "\n".join(commands_list)
        except Exception as e:
            logger.error(f"Error generating help message: {e}")
            return "Error: Unable to generate help message"
    
    async def clear_cache(self, *args: Any) -> str:
        """
        Clear the cache directory.
        
        Returns:
            Status message indicating success or failure
        """
        cache_dir = "cache"
        try:
            if os.path.exists(cache_dir):
                cleared_count = 0
                for file in os.listdir(cache_dir):
                    file_path = os.path.join(cache_dir, file)
                    try:
                        os.remove(file_path)
                        cleared_count += 1
                    except Exception as e:
                        logger.warning(f"Failed to remove {file_path}: {e}")
                
                logger.info(f"Cache cleared: {cleared_count} files removed")
                return f"Cache cleared: {cleared_count} files removed"
            else:
                return "Cache directory does not exist"
        except Exception as e:
            logger.error(f"Error clearing cache: {e}")
            return f"Error clearing cache: {e}"
    
    async def status(self, *args: Any) -> str:
        """
        Show system status including version, plugins, permissions, and uptime.
        
        Returns:
            Formatted status string
        """
        try:
            message = "Status:\n"
            
            # Coral version
            coral_version = self.config.get("coral_version", "Unknown")
            message += f"Coral Version: {coral_version}\n"
            
            # Plugin information
            try:
                plugin_message = await self.register.execute_command(
                    CommandEvent(
                        event_id=f"Console-{time.time()}",
                        platform="system",
                        self_id="Console",
                        command="plugins",
                        raw_message=MessageChain([MessageSegment(type="text", data="plugins")]),
                        user=UserInfo(platform="system", user_id="Console"),
                        group=None,
                        args=[]
                    )
                )
                if isinstance(plugin_message, MessageRequest):
                    message += plugin_message.message.to_plain_text() + "\n"
                else:
                    message += "Plugins: Information unavailable\n"
            except Exception as e:
                logger.warning(f"Failed to get plugin information: {e}")
                message += "Plugins: Error retrieving information\n"
            
            # Permission count
            perm_count = len(self.perm_system.registered_perms)
            message += f"Total registered {perm_count} permissions\n"
            
            # Uptime
            if self.init_time is None:
                message += "Uptime: System not fully initialized\n"
            else:
                uptime = time.time() - self.init_time
                day, hour, minute, second = (
                    uptime // (24 * 3600),
                    uptime // 3600 % 24,
                    uptime // 60 % 60,
                    uptime % 60
                )
                message += f"Uptime: {int(day)} day(s) {int(hour)} hour(s) {int(minute)} minute(s) {int(second)} second(s)\n"
            
            message += "Hello from Coral!😋"
            return message
            
        except Exception as e:
            logger.error(f"Error generating status: {e}")
            return f"Error generating status: {e}"
