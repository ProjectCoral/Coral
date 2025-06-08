import os
import time
from Coral import register, config, perm_system
from core.protocol import CommandEvent, MessageSegment, UserInfo

def register_plugin():
    perm_system.register_perm("base_commands", "Base Permission")
    perm_system.register_perm("base_commands.help", "User can use the help command")
    perm_system.register_perm("base_commands.clear", "User can clear the cache")
    perm_system.register_perm("base_commands.status", "User can see the status of Coral")
    register.register_command('help', 'Show help message', base_commands(register, config, perm_system).show_help, ["base_commands", "base_commands.help"])
    register.register_command('clear', 'Clear cache', base_commands(register, config, perm_system).clear_cache, ["base_commands", "base_commands.clear"])
    register.register_command('status', 'Show status of Coral', base_commands(register, config, perm_system).status, ["base_commands", "base_commands.status"])
    register.register_event("coral_initialized", "init_time", base_commands(register, config, perm_system).init_timer, 1)

class base_commands:
    register = None
    config = None
    perm_system = None

    def __init__(self, register, config, perm_system):
        self.register = register
        self.config = config
        self.perm_system = perm_system
        self.init_time = None
        
    async def init_timer(self, *args):
        global init_time
        init_time = time.time()
        return None, False, 1
    
    async def show_help(self, *args):
        return "List of available commands:\n" + "\n".join([f"{command_name}: {self.register.get_command_description(command_name)}" for command_name in self.register.commands])
    
    async def clear_cache(self, *args):
        if os.path.exists("cache"):
            for file in os.listdir("cache"):
                os.remove(os.path.join("cache", file))
        return "Cache cleared"
    
    async def status(self, *args):
        message = "Status:\n"
        message += "Coral Version: " + self.config.get("coral_version") + "\n"
        plugin_message = await self.register.execute_command(
                        CommandEvent(
                            event_id = "Console-" + str(time.time()),
                            platform = "system",
                            self_id= "Console",
                            command="plugins",
                            raw_message=MessageSegment(type="text", data="plugins"),
                            user=UserInfo(platform="system", user_id="Console"),
                            group=None,
                            args=[]
                        ))
        message += plugin_message.message.to_plain_text() + "\n"
        message += "Total registered " + str(len(self.perm_system.registered_perms)) + " permissions\n"
        uptime = time.time() - init_time
        day, hour, minute, second = uptime // (24 * 3600), uptime // 3600 % 24, uptime // 60 % 60, uptime % 60
        message += f"Uptime: {int(day)} day(s) {int(hour)} hour(s) {int(minute)} minute(s) {int(second)} second(s)\n"
        message += f"Hello from Coral!\U0001F60B"
        return message
