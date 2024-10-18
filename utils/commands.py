import os

def register_command(register, config):
    register.register_command('help', 'Show help message', base_commands(register).show_help)
    register.register_command('clear', 'Clear cache', base_commands(register).clear_cache)

class base_commands:
    register = None

    def __init__(self, register):
        self.register = register

    def show_help(self):
        return "List of available commands:\n" + "\n".join([f"{command_name}: {self.register.get_command_description(command_name)}" for command_name in self.register.commands])
    
    def clear_cache(self):
        if os.path.exists("cache"):
            for file in os.listdir("cache"):
                os.remove(os.path.join("cache", file))
        return "Cache cleared"