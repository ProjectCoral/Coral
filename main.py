import os
import sys
import subprocess
import logging
import shutil
from colorama import Fore

logging.basicConfig(level=logging.INFO, format="[%(asctime)s] [%(levelname)s:%(name)s] %(message)s", datefmt="%H:%M:%S")

if not os.path.exists('config.json'):
    logging.info("Checking requirements...")
    with open('./requirements.txt', 'r') as f:
        lines = f.readlines()
    for line in lines:
        if line.startswith('#') or line.strip() == '':
            continue
        try:
            subprocess.check_call([sys.executable, '-m', 'pip', 'show', line.strip()], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except subprocess.CalledProcessError as e:
            logging.critical(Fore.RED + "Failed to check requirement: {}".format(line.strip()) + Fore.RESET)
            logging.error("Did you install it?\U0001F605")
            sys.exit(1)

logging.info("Cleaning up __pycache__ directories...")
for root, dirs, files in os.walk('./'):
    for dir_name in dirs:
        if dir_name == "__pycache__":
            pycache_dir = os.path.join(root, dir_name)
            shutil.rmtree(pycache_dir)
            logging.debug("Removed {}".format(pycache_dir))

from Coral import Coral

if __name__ == '__main__':
    logging.info("Starting Coral...")
    Coral()