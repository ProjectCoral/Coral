import os
import sys
import subprocess

def register_command(register, config):
    register.register_command('help', 'Show help message', base_commands(register, config).show_help)
    register.register_command('clear', 'Clear cache', base_commands(register, config).clear_cache)
    register.register_command('status', 'Show status of Coral', base_commands(register, config).status)

class base_commands:
    register = None
    config = None

    def __init__(self, register, config):
        self.register = register
        self.config = config

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
        message += self.register.execute_command('plugins')
        message += f"Python version: {sys.version}\n"
        try:
            commit_hash = subprocess.check_output(["git", "rev-parse", "HEAD"], shell=False, encoding='utf8').strip()
        except Exception:
            commit_hash = "<none>"
        message += f"Git commit hash: {commit_hash}\n"
        message += f"Hello from Coral!\n"
        return message
