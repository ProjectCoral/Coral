import os
import subprocess

def register_command(register, config, perm_system):
    perm_system.register_perm("base_commands", "Base Permission")
    register.register_command('help', 'Show help message', base_commands(register, config, perm_system).show_help)
    perm_system.register_perm("base_commands.help", "User can use the help command")
    register.register_command('clear', 'Clear cache', base_commands(register, config, perm_system).clear_cache)
    perm_system.register_perm("base_commands.clear", "User can clear the cache")
    register.register_command('status', 'Show status of Coral', base_commands(register, config, perm_system).status)
    perm_system.register_perm("base_commands.status", "User can see the status of Coral")

class base_commands:
    register = None
    config = None
    perm_system = None

    def __init__(self, register, config, perm_system):
        self.register = register
        self.config = config
        self.perm_system = perm_system

    def show_help(self, user_id, group_id, *args):
        if not self.perm_system.check_perm(["base_commands", "base_commands.help"], user_id, group_id):
            return "You do not have permission."
        return "List of available commands:\n" + "\n".join([f"{command_name}: {self.register.get_command_description(command_name)}" for command_name in self.register.commands])
    
    def clear_cache(self, user_id, group_id, *args):
        if not self.perm_system.check_perm(["base_commands", "base_commands.clear"], user_id, group_id):
            return "You do not have permission."
        if os.path.exists("cache"):
            for file in os.listdir("cache"):
                os.remove(os.path.join("cache", file))
        return "Cache cleared"
    
    def status(self, user_id, group_id, *args):
        if not self.perm_system.check_perm(["base_commands", "base_commands.status"], user_id, group_id):
            return "You do not have permission."
        message = "Status:\n"
        message += "Coral Version: " + self.config.get("coral_version") + "\n"
        message += self.register.execute_command('plugins', "Console", -1)
        message += "Total registered " + str(len(self.perm_system.registered_perms)) + " Permissions.\n"
        try:
            commit_hash = subprocess.check_output(["git", "rev-parse", "HEAD"], shell=False, encoding='utf8').strip()
        except Exception:
            commit_hash = "<none>"
        message += f"Git commit hash: {commit_hash}\n"
        message += f"Hello from Coral!\n"
        return message
