import os
import threading
import time
import logging
import asyncio
from pyfiglet import Figlet
from colorama import Fore

import utils.commands
import utils.install_requirements
import utils.chat_command
from utils.auto_prompt import AutoPrompt
from utils.reverse_ws import ReverseWS
from utils.config import Config
from utils.process_reply import ProcessReply

from core.register import Register
from core.plugin_manager import PluginManager
from core.perm_system import PermSystem

logger = logging.getLogger(__name__)

class Coral:
    def __init__(self):
        textrender=Figlet(font="larry3d")
        print(Fore.GREEN + textrender.renderText("Project Coral") + Fore.RESET)
        asyncio.run(self.initialize())
        self.run()
        
    async def initialize(self):
        plugin_dir = "./plugins"
        config_file = "./config.json"
        self.config = Config(config_file)
        self.register = Register()
        self.perm_system = PermSystem(self.register, self.config)
        self.plugin_manager = PluginManager(self.register, self.config, self.perm_system)

        self.config.set("coral_version", "241019_early_developement")

        self.register_buildin_plugins()

        await self.plugin_manager.load_plugins()

        self.process_reply = ProcessReply(self.register, self.config)

        logger.info("All things works fine, starting client...")
        threading.Thread(target=self.ws_thread, args=(self.config,self.register,self.process_reply.process_message),).start()
        
        AutoPrompt.load_commands(self.register.commands)

    def register_buildin_plugins(self):
        self.plugin_manager.plugins.append("base_commands")
        utils.commands.register_command(self.register, self.config, self.perm_system)
        self.plugin_manager.plugins.append("install_requirements")
        utils.install_requirements.register_function(self.register, self.config, self.perm_system)
        self.plugin_manager.plugins.append("chat_command")
        utils.chat_command.register_event(self.register, self.config, self.perm_system)

    def run(self):
        time.sleep(3) # 等待适配器加载完成
        try:
            while True:
                im_text = AutoPrompt.prompt()
                try:
                    command, *args = im_text.split(" ", 1)
                except ValueError:
                    command = im_text
                    args = []
                try:
                    response = self.register.execute_command(command, "Console", -1, *args)
                    print(response)
                except Exception as e:
                    logger.error(Fore.RED + f"Error executing command: {e}" + Fore.RESET)
                    logger.warning(Fore.YELLOW + f"You can continue to use Console, but we recommand you to check your command or plugin." + Fore.RESET)                    
        except KeyboardInterrupt:
            self.stopping()

    def stopping(self):
        logger.info("Stopping Coral...")
        os._exit(0)

    def ws_thread(self, config, register, process_reply):
        logger.info("Starting WebSocket Server...")
        try:
            ReverseWS(config, register, process_reply).start()
        except KeyboardInterrupt:
            pass
