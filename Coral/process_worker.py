import os
import time
import logging
from pyfiglet import Figlet
from colorama import Fore
from multiprocessing import Process
import subprocess

logger = logging.getLogger(__name__)

class ProcessWorker(Process):
    def __init__(self, target, args=()):
        super().__init__()
        self.target = target
        self.args = args
        self.name = f"ProcessWorker-{os.getpid()}"
    def run(self):
        textrender=Figlet(font="larry3d")
        print(Fore.GREEN + textrender.renderText("Project Coral") + Fore.RESET)
        logger.info(f"Starting process {self.name}")
        self.target(*self.args)
