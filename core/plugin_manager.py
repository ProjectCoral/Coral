import os
import importlib.util
import logging

PluginManager_Version = "1.0"

class PluginManager:
    plugin_dir: str = "./plugins"
    register = None

    def __init__(self, plugin_dir, register):
        self.plugin_dir = plugin_dir
        self.register = register
        self.plugins = []

    def load_plugins(self):
        if not os.path.exists(self.plugin_dir):
            logging.warning(f"Plugin directory {self.plugin_dir} does not exist, skipping plugin loading")
        else:
            for plugin_name in os.listdir(self.plugin_dir):
                plugin_path = os.path.join(self.plugin_dir, plugin_name)
                if not os.path.isdir(plugin_path):
                    continue
                main_file = os.path.join(plugin_path, 'main.py')
                if not os.path.exists(main_file):
                    continue
                spec = importlib.util.spec_from_file_location("main", main_file)
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                self.plugins.append(plugin_name)
                if hasattr(module, 'register_command'):
                    module.register_command(self.register)
                if hasattr(module, 'register_event'):
                    module.register_event(self.register)
                if hasattr(module, 'register_function'):
                    module.register_function(self.register)
        self.register.register_command("plugins", "List all available plugins", self.show_plugins)
        logging.info(f"Loaded {len(self.plugins)} plugins")

    def show_plugins(self, *args):
        return  "Available plugins:" + "\n".join(self.plugins) + "\n Running Plugin Manager version "+ PluginManager_Version