import os
import importlib.util
import logging
import asyncio

logger = logging.getLogger(__name__)

class PluginManager:
    register = None
    config = None
    perm_system = None

    def __init__(self, register, config, perm_system):
        self.config = config
        self.perm_system = perm_system
        self.plugin_dir = self.config.get("plugin_dir", "./plugins")
        self.config.set("pluginmanager_version", "241108_early_developement")
        self.pluginmanager_version = self.config.get("pluginmanager_version")
        self.register = register
        self.plugins = []

    async def load_all_plugins(self):
        if not os.path.exists(self.plugin_dir):
            logger.warning(f"[yellow]Plugin directory {self.plugin_dir} does not exist, skipping plugin loading...[/]")
        else:
            logger.info(f"Loading plugins from {self.plugin_dir}")
            load_tasks = [self.load_plugin(plugin_name) for plugin_name in os.listdir(self.plugin_dir)]
            await asyncio.gather(*load_tasks)
                
        self.perm_system.register_perm("pluginmanager", "Base Permission")
        self.perm_system.register_perm("pluginmanager.show_plugins", "Permission to show available plugins")
        self.register.register_command("plugins", "List all available plugins", self.show_plugins, ["pluginmanager", "pluginmanager.show_plugins"])
        logger.info(f"Loaded {len(self.plugins)} plugins")

    async def load_plugin(self, plugin_name):
        plugin_path = os.path.join(self.plugin_dir, plugin_name)
        if not os.path.isdir(plugin_path):
            return None
        main_file = os.path.join(plugin_path, 'main.py')
        if not os.path.exists(main_file):
            return None

        requirements_file = os.path.join(plugin_path,'requirements.txt')
        if os.path.exists(requirements_file):
            if not os.path.exists(requirements_file + ".coral_installed") and not await self.register.execute_function("check_pip_requirements", requirements_file):
                logger.warning("[yellow]Plugin [/]" + str(plugin_name) + "[yellow] has unmet requirements, trying to install them...[/]")
                if not await self.register.execute_function("install_pip_requirements", requirements_file):
                    logger.error("[red]Failed to install requirements for plugin [/]" + str(plugin_name) + "[red] , skipping...[/]")
                    return None

        try:
            spec = importlib.util.spec_from_file_location("main", main_file)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
        except Exception as e:
            logger.exception(f"[red]During plugin loading, an error occurred: {e}[/]")
            logger.error("[red]Failed to load plugin [/]" + str(plugin_name) + "[red] , skipping...[/]")
            if os.path.exists(requirements_file + ".coral_installed"):
                os.remove(requirements_file + ".coral_installed")
            return None

        if hasattr(module, 'check_conpatibility'):
            if not module.check_conpatibility(self.pluginmanager_version):
                logger.error("[red]Plugin [/]" + str(plugin_name) + "[red] is not compatible with this version of the Plugin Manager, skipping...[/]")
                return None
        else:
            logger.warning("[yellow]Plugin [/]" + str(plugin_name) + "[yellow] did not provide a compatibility check, which is deprecated and might be broken in a future version.[/]")
        self.plugins.append(plugin_name)
        if hasattr(module, 'register_plugin'):
            try:
                module.register_plugin(self.register, self.config, self.perm_system)
            except Exception as e:
                logger.exception(f"[red]During plugin registration, an error occurred: {e}[/]")
                logger.error("[red]Failed to register plugin [/]" + str(plugin_name) + "[red] , skipping...[/]")
                return None
        else:
            logger.warning("[yellow]Plugin [/]" + str(plugin_name) + "[yellow] did not provide a register function, will not do anything.[/]")

    def show_plugins(self, *args):
        return  "Available plugins:\n" + str(self.plugins) + "\n Running Plugin Manager Version " + self.pluginmanager_version + "\n"