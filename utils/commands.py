import os

def register_command(register, config, perm_system):
    perm_system.register_perm("base_commands", "Base Permission")
    perm_system.register_perm("base_commands.help", "User can use the help command")
    perm_system.register_perm("base_commands.clear", "User can clear the cache")
    perm_system.register_perm("base_commands.status", "User can see the status of Coral")
    register.register_command('help', 'Show help message', base_commands(register, config, perm_system).show_help, ["base_commands", "base_commands.help"])
    register.register_command('clear', 'Clear cache', base_commands(register, config, perm_system).clear_cache, ["base_commands", "base_commands.clear"])
    register.register_command('status', 'Show status of Coral', base_commands(register, config, perm_system).status, ["base_commands", "base_commands.status"])

class base_commands:
    register = None
    config = None
    perm_system = None

    def __init__(self, register, config, perm_system):
        self.register = register
        self.config = config
        self.perm_system = perm_system

    def show_help(self, *args):
        return "List of available commands:\n" + "\n".join([f"{command_name}: {self.register.get_command_description(command_name)}" for command_name in self.register.commands])
    
    def clear_cache(self, *args):
        if os.path.exists("cache"):
            for file in os.listdir("cache"):
                os.remove(os.path.join("cache", file))
        return "Cache cleared"
    
    def status(self, *args):
        message = "Status:\n"
        message += "Coral Version: " + self.config.get("coral_version") + "\n"
        message += self.register.execute_command('plugins', "Console", -1)
        message += "Total registered " + str(len(self.perm_system.registered_perms)) + " permissions\n"
        message += f"Hello from Coral!"
        return message
