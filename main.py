import os
import sys
import subprocess
import logging

logging.basicConfig(level=logging.INFO, format="[%(asctime)s-%(name)s] [%(levelname)s] %(message)s", datefmt="%H:%M:%S")

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
            logging.error("Failed to check requirement: {}".format(line.strip()))
            logging.error("Did you install it?")
            sys.exit(1)

from Coral import Coral

if __name__ == '__main__':
    logging.info("Starting Coral...")
    Coral()