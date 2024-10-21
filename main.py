import os
import sys
import subprocess
import logging
import shutil
from colorama import Fore

logging.basicConfig(level=logging.INFO, format="[%(asctime)s] [%(levelname)s:%(name)s] %(message)s", datefmt="%H:%M:%S")

if not os.path.exists('config.json'):
    logging.info("Checking requirements, this may take a while...")
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

    from prompt_toolkit.shortcuts import yes_no_dialog
    coral_eula ="""
        By using this software, you agree to the following EULA:
         1. Coral is an open source project under the AGPL-3.0 protocol.
         2. This project is not intended for commercial use.
         3. Derivative projects must clearly state that they are derived from Coral.
         4. It is not allowed to distort or hide the fact that this project is free and open source.
        """
    try:
        result = yes_no_dialog(
        title="Coral EULA", text=coral_eula
    ).run()
        if not result:
            logging.critical("You must agree to the EULA to use Coral.")
            sys.exit(1)
    except Exception as e:
        logging.warning("Your device may not support prompt_toolkit dialog.")
        print(coral_eula)
        result = input("Do you agree to the Coral EULA? (y/n): ")
        if result.lower() not in ['y', 'yes']:
            logging.critical("You must agree to the EULA to use Coral.")
            sys.exit(1)

logging.info("Cleaning up __pycache__ directories...")
for root, dirs, files in os.walk('./'):
    for dir_name in dirs:
        if dir_name == "__pycache__":
            pycache_dir = os.path.join(root, dir_name)
            shutil.rmtree(pycache_dir)
            logging.debug("Removed {}".format(pycache_dir))
      

if __name__ == '__main__':
    logging.info("Starting Coral...")
    try:
        from Coral import Coral
        Coral()
    except Exception as e:
        logging.exception(Fore.RED + "An error occurred: {}".format(str(e)) + Fore.RESET)
        logging.critical("Oops, Coral has crashed.\U0001F605 Please check the logs for more information.")
        os._exit(1)