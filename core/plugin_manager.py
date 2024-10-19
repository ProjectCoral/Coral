import os
import importlib.util
import logging
from colorama import Fore

logger = logging.getLogger(__name__)

class PluginManager:
    register = None
    config = None
    perm_system = None

    def __init__(self, register, config, perm_system):
        self.config = config
        self.perm_system = perm_system
        self.plugin_dir = self.config.get("plugin_dir", "./plugins")
        self.pluginmanager_version = self.config.get("pluginmanager_version", "241019_early_developement")
        self.register = register
        self.plugins = []

    async def load_plugins(self):
        if not os.path.exists(self.plugin_dir):
            logger.warning(Fore.YELLOW + f"Plugin directory {self.plugin_dir} does not exist, skipping plugin loading" + Fore.RESET)
        else:
            for plugin_name in os.listdir(self.plugin_dir):
                plugin_path = os.path.join(self.plugin_dir, plugin_name)
                if not os.path.isdir(plugin_path):
                    continue
                main_file = os.path.join(plugin_path, 'main.py')
                if not os.path.exists(main_file):
                    continue
                requirements_file = os.path.join(plugin_path,'requirements.txt')
                if os.path.exists(requirements_file):
                    if not await self.register.execute_function("check_pip_requirements", requirements_file):
                        logger.warning(Fore.YELLOW + "Plugin " + Fore.RESET + str(plugin_name) + Fore.YELLOW + " has unmet requirements, trying to install them" + Fore.RESET)
                        if not await self.register.execute_function("install_pip_requirements", requirements_file):
                            logger.error(Fore.RED + "Failed to install requirements for plugin " + Fore.RESET + str(plugin_name) + Fore.RED + " , skipping" + Fore.RESET)
                            continue
                spec = importlib.util.spec_from_file_location("main", main_file)
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                if hasattr(module, 'check_conpatibility'):
                    if not module.check_conpatibility(self.pluginmanager_version):
                        logger.error(Fore.RED + "Plugin " + Fore.RESET + str(plugin_name) + Fore.RED + " is not compatible with this version of the Plugin Manager, skipping" + Fore.RESET)
                        continue
                else:
                    logger.warning(Fore.YELLOW + "Plugin " + Fore.RESET + str(plugin_name) + Fore.YELLOW + " did not provide a compatibility check, which is deprecated and will be broken in a future version" + Fore.RESET)
                self.plugins.append(plugin_name)
                if hasattr(module, 'register_command'):
                    module.register_command(self.register, self.config, self.perm_system)
                if hasattr(module, 'register_event'):
                    module.register_event(self.register, self.config, self.perm_system)
                if hasattr(module, 'register_function'):
                    module.register_function(self.register, self.config, self.perm_system)
        self.register.register_command("plugins", "List all available plugins", self.show_plugins)
        self.perm_system.register_perm("pluginmanager", "Base Permission")
        self.perm_system.register_perm("pluginmanager.show_plugins", "Permission to show available plugins")
        logger.info(f"Loaded {len(self.plugins)} plugins")

    def show_plugins(self, user_id, group_id, *args):
        if not self.perm_system.check_perm(["pluginmanager", "pluginmanager.show_plugins"], user_id, group_id):
            return "You do not have permission."
        return  "Available plugins:\n" + str(self.plugins) + "\n Running Plugin Manager version " + self.pluginmanager_version + "\n"