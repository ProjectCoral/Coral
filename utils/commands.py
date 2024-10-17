import os


class base_commands:
    register = None

    def __init__(self, register):
        self.register = register

    def register_command(self):
        self.register.register_command('help', 'Show help message', self.show_help)
        self.register.register_command('clear', 'Clear cache', self.clear_cache)

    def show_help(self):
        return "List of available commands:\n" + "\n".join([f"{command_name}: {self.register.get_command_description(command_name)}" for command_name in self.register.commands])
    
    def clear_cache(self):
        if os.path.exists("cache"):
            for file in os.listdir("cache"):
                os.remove(os.path.join("cache", file))
        return "Cache cleared"