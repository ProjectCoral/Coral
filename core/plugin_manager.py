import os
import sys
import time
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
        self.config.set("pluginmanager_version", "250608_early_developement")
        self.pluginmanager_version = self.config.get("pluginmanager_version")
        self.pluginmanager_meta = "250606"
        self.register = register
        self.plugins = []
        self._loaded = set()

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
        self.register.register_command("reload", "Reload all plugins", self.reload_command, ["pluginmanager"])
        logger.info(f"Loaded {len(self.plugins)} plugins.")

    async def load_plugin(self, plugin_name):
        if plugin_name in self._loaded:
            logger.warning(f"[yellow]Plugin {plugin_name} is already loaded, skipping...[/]")
            return None
        
        plugin_path = os.path.join(self.plugin_dir, plugin_name)
        if not os.path.isdir(plugin_path):
            return None
        init_file = os.path.join(plugin_path, '__init__.py')
        if not os.path.exists(init_file):
            return None

        requirements_file = os.path.join(plugin_path,'requirements.txt')
        if os.path.exists(requirements_file):
            if not os.path.exists(requirements_file + ".coral_installed") and not await self.register.execute_function("check_pip_requirements", requirements_file):
                logger.warning("[yellow]Plugin [/]" + str(plugin_name) + "[yellow] has unmet requirements, trying to install them...[/]")
                if not await self.register.execute_function("install_pip_requirements", requirements_file):
                    logger.error("[red]Failed to install requirements for plugin [/]" + str(plugin_name) + "[red] , skipping...[/]")
                    return None

        try:
            spec = importlib.util.spec_from_file_location(f"plugins.{plugin_name}", init_file)
            module = importlib.util.module_from_spec(spec)
            if hasattr(module, "__plugin_meta__"):
                meta = getattr(module, "__plugin_meta__")
                if "conpatibility" in meta and meta["conpatibility"] < self.pluginmanager_meta:
                    logger.error("[red]Plugin [/]" + str(plugin_name) + "[red] is not compatible with this version of the Plugin Manager, skipping...[/]")
                    return None
            else:
                logger.warning("[yellow]Plugin [/]" + str(plugin_name) + "[yellow] did not provide a compatibility check, which is deprecated and might be broken in a future version.[/]")
                
            sys.modules[f"plugins.{plugin_name}"] = module

            spec.loader.exec_module(module)
            self._loaded.add(plugin_name)
            self.plugins[plugin_name] = module
        except Exception as e:
            logger.exception(f"[red]During plugin loading, an error occurred: {e}[/]")
            logger.error("[red]Failed to load plugin [/]" + str(plugin_name) + "[red] , skipping...[/]")
            if os.path.exists(requirements_file + ".coral_installed"):
                os.remove(requirements_file + ".coral_installed")
            return None
        
        self.plugins.append(plugin_name)

    async def show_plugins(self, *args):
        return  "Available plugins:\n" + str(self.plugins) + "\n Running Plugin Manager Version " + self.pluginmanager_version + "\n"
    
    async def reload_plugins(self):
        if not os.path.exists(self.plugin_dir):
            logger.warning(f"[yellow]Plugin directory {self.plugin_dir} does not exist, skipping plugin reloading...[/]")
        else:
            self.plugins = []
            await self.register.core_reload()
            logger.info(f"Reloading plugins from {self.plugin_dir}")
            reload_tasks = [self.load_plugin(plugin_name) for plugin_name in os.listdir(self.plugin_dir)]
            await asyncio.gather(*reload_tasks)
        self.perm_system.register_perm("pluginmanager", "Base Permission")
        self.perm_system.register_perm("pluginmanager.show_plugins", "Permission to show available plugins")
        self.register.register_command("plugins", "List all available plugins", self.show_plugins, ["pluginmanager", "pluginmanager.show_plugins"])
        self.register.register_command("reload", "Reload all plugins", self.reload_command, ["pluginmanager"])
        logger.info(f"Reloaded {len(self.plugins)} plugins.")
            
        
    async def reload_command(self, *args, **kwargs):
        start_time = time.time()
        task = asyncio.create_task(self.reload_plugins())
        await task
        end_time = time.time()
        logger.warning(f"[yellow]It's not recommended to reload frequently, as it can cause issues. Please use the reload command only when necessary.[/]")
        return f"Reloaded in {end_time - start_time:.2f} s"

    async def reload_plugin(self, plugin_name):
        plugin_path = os.path.join(self.plugin_dir, plugin_name)
        if not os.path.isdir(plugin_path):
            return None
        init_file = os.path.join(plugin_path, '__init__.py')
        if not os.path.exists(init_file):
            return None
        
        try:
            if f"plugins.{plugin_name}" in sys.modules:
                importlib.reload(sys.modules[f"plugins.{plugin_name}"])
            else:
                await self.load_plugin(plugin_name)
        except ModuleNotFoundError:
            try:
                await self.load_plugin(plugin_name)
            except:
                return None
        except Exception as e:
            logger.exception(f"[red]During plugin reloading, an error occurred: {e}[/]")
            logger.error("[red]Failed to reload plugin [/]" + str(plugin_name) + "[red] , skipping...[/]")
            return None
