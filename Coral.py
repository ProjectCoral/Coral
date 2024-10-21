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
        start_time = time.time()

        plugin_dir = "./plugins"
        config_file = "./config.json"
        self.config = Config(config_file)
        self.register = Register()
        self.perm_system = PermSystem(self.register, self.config)
        self.plugin_manager = PluginManager(self.register, self.config, self.perm_system)

        self.config.set("coral_version", "241021_early_developement")

        self.register_buildin_plugins()

        await self.plugin_manager.load_plugins()

        self.process_reply = ProcessReply(self.register, self.config)

        if 'coral_initialized' in self.register.event_queues:
            await self.register.execute_event('coral_initialized')
        
        end_time = time.time()

        logger.info(Fore.GREEN + f"Coral initialized in {end_time - start_time:.2f} seconds." + Fore.RESET)

        last_init_time = self.config.get("last_init_time", end_time - start_time)
        if end_time - start_time < last_init_time:
            logger.info(Fore.CYAN + f"Coral initialize boosted\U0001F680 by {last_init_time - end_time + start_time:.2f} seconds." + Fore.RESET)
        self.config.set("last_init_time", end_time - start_time)

        logger.info("All things works fine\U0001F60B, starting client...")
        threading.Thread(target=self.ws_thread, args=(self.config,self.register,self.process_reply.process_message),).start()
        
        AutoPrompt.load_commands(self.register.commands)

    def register_buildin_plugins(self):
        self.plugin_manager.plugins.append("base_commands")
        utils.commands.register_plugin(self.register, self.config, self.perm_system)
        self.plugin_manager.plugins.append("install_requirements")
        utils.install_requirements.register_plugin(self.register, self.config, self.perm_system)
        self.plugin_manager.plugins.append("chat_command")
        utils.chat_command.register_plugin(self.register, self.config, self.perm_system)

    def run(self):
        time.sleep(3) # 等待适配器加载完成
        try:
            while True:
                try:
                    im_text = AutoPrompt.prompt()
                except Exception:
                    logger.error(Fore.RED + "Error in AutoPrompt, console input will not be available." + Fore.RESET)
                    logger.warning(Fore.YELLOW + "After disabled input, some unexpected errors may occur." + Fore.RESET)  
                    disabled_console = True
                    break
                try:
                    command, *args = im_text.split(" ", 1)
                except ValueError:
                    command = im_text
                    args = []
                try:
                    response = self.register.execute_command(command, "Console", -1, *args)
                    print(response)
                except Exception as e:
                    logger.exception(Fore.RED + f"Error executing command: {e}" + Fore.RESET)
                    logger.warning(Fore.YELLOW + f"You can continue to use Console, but we recommand you to check your command or plugin." + Fore.RESET)  
                    continue                  
        except KeyboardInterrupt:
            self.stopping()
        except Exception as e:
            logger.exception(Fore.RED + f"Unknown error occured: {e}" + Fore.RESET)
            logger.exception("This error should not happen.\U0001F630")
            logger.error("Coral will be stopped.")
            self.stopping()

        try:
            if disabled_console:
                try:
                    while True:
                        time.sleep(5)
                except KeyboardInterrupt:
                    self.stopping()
        except Exception as e:
            logger.exception(Fore.RED + f"Unknown error occured: {e}" + Fore.RESET)
            logger.critical("This error should not happen.\U0001F630")
            logger.error("Coral will be stopped.")
            self.stopping()

    def stopping(self):
        logger.info("Stopping Coral...")
        if 'coral_shutdown' in self.register.event_queues:
            asyncio.run(self.register.execute_event('coral_shutdown'))
        os._exit(0)

    def ws_thread(self, config, register, process_reply):
        logger.info("Starting WebSocket Server...")
        while True:
            try:
                ReverseWS(config, register, process_reply).start()
            except KeyboardInterrupt:
                break
            except Exception as e:
                logger.exception(Fore.RED + f"Error in WebSocket Server: {e}" + Fore.RESET)
                time.sleep(3)
                logger.warning(Fore.YELLOW + "Restarting WebSocket Server..." + Fore.RESET)