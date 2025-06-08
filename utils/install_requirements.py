import os
import subprocess
import sys
import logging
import re
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeRemainingColumn
from Coral import register, config

logger = logging.getLogger(__name__)

def register_plugin():
    register.register_function('install_pip_requirements', InstallRequirements(config).install_pip_requirements)
    register.register_function('check_pip_requirements', InstallRequirements(config).check_pip_requirements)

class InstallRequirements:
    config = None

    def __init__(self, config):
        self.config = config
        self.progress = Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TimeRemainingColumn(),
            transient=True,
        )
        
    async def install_pip_requirements(self, requirements_file):
        if not os.path.exists(requirements_file):
            logger.error("[red]Requirements file not found: {}[/]".format(requirements_file))
            return False
        task = self.progress.add_task("[green]Installing plugin requirements...", total=None)
        with self.progress:
            index_url = self.config.get('index_url', 'https://pypi.tuna.tsinghua.edu.cn/simple')
            try:
                subprocess.check_call([sys.executable, '-m', 'pip', 'install', '-i', index_url, '-r', requirements_file], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            except subprocess.CalledProcessError as e:
                logger.error("[red]Failed to install requirements: {}[/]".format(e))
                self.progress.stop()
                return False
            self.progress.update(task)
            self.progress.stop()
            return True
    
    async def check_pip_requirements(self, requirements_file):
        if not os.path.exists(requirements_file):
            logger.error("[red]Requirements file not found: {}[/]".format(requirements_file))
            return False
        
        if os.path.exists(requirements_file + ".coral_installed"):
            return True

        with open(requirements_file, 'r') as f:
            lines = f.readlines()
        
        task = self.progress.add_task("[green]Checking plugin requirements...", total=len(lines))

        with self.progress:
            for line in lines:
                if line.startswith('#') or line.strip() == '':
                    continue
                
                # 解析包名
                package_name = re.split('>=|>|<=|<|==|!=', line.strip())[0].strip()
                
                try:
                    subprocess.check_call([sys.executable, '-m', 'pip', 'show', package_name], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                except subprocess.CalledProcessError as e:
                    logger.error("[red]Failed to check requirement: {}[/]".format(line.strip()))
                    self.progress.stop()
                    return False
                self.progress.update(task, advance=1)
        self.progress.stop()
        
        with open(requirements_file + ".coral_installed", 'w') as f:
            f.write("Installed")

        return True