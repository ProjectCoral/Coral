import os
import subprocess
import sys
import logging
import re
import time
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeRemainingColumn
from Coral import register, config

logger = logging.getLogger(__name__)

def register_plugin():
    """Register the requirements installation plugin."""
    requirements_instance = InstallRequirements(config)
    register.register_function('install_pip_requirements', requirements_instance.install_pip_requirements)
    register.register_function('check_pip_requirements', requirements_instance.check_pip_requirements)

class InstallRequirements:
    """Handle pip requirements installation and checking."""
    
    def __init__(self, config):
        self.config = config
        self.progress = None  # Initialize lazily
    
    def _get_progress(self):
        """Get or create progress bar instance."""
        if self.progress is None:
            self.progress = Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
                TimeRemainingColumn(),
                transient=True,
            )
        return self.progress
    
    async def install_pip_requirements(self, requirements_file):
        """Install pip requirements from a file."""
        if not os.path.exists(requirements_file):
            logger.error(f"Requirements file not found: {requirements_file}")
            return False
        
        progress = self._get_progress()
        task = progress.add_task("[green]Installing plugin requirements...", total=None)
        
        try:
            with progress:
                index_url = self.config.get('index_url', 'https://pypi.tuna.tsinghua.edu.cn/simple')
                
                # Build command
                cmd = [sys.executable, '-m', 'pip', 'install', '-i', index_url, '-r', requirements_file]
                
                # Execute with timeout
                try:
                    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, 
                                  stderr=subprocess.DEVNULL, timeout=300)
                except subprocess.TimeoutExpired:
                    logger.error(f"Installation timed out for {requirements_file}")
                    return False
                except subprocess.CalledProcessError as e:
                    logger.error(f"Failed to install requirements: {e}")
                    return False
                
                progress.update(task, completed=True)
                logger.info(f"Successfully installed requirements from {requirements_file}")
                return True
                
        except Exception as e:
            logger.error(f"Unexpected error during installation: {e}")
            return False
    
    async def check_pip_requirements(self, requirements_file):
        """Check if pip requirements are installed."""
        if not os.path.exists(requirements_file):
            logger.error(f"Requirements file not found: {requirements_file}")
            return False
        
        # Check cache
        cache_file = requirements_file + ".coral_installed"
        if os.path.exists(cache_file):
            # Verify cache is not too old (1 day)
            cache_age = time.time() - os.path.getmtime(cache_file)
            if cache_age < 86400:  # 24 hours
                return True
        
        try:
            with open(requirements_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
        except Exception as e:
            logger.error(f"Failed to read requirements file: {e}")
            return False
        
        progress = self._get_progress()
        task = progress.add_task("[green]Checking plugin requirements...", total=len(lines))
        
        try:
            with progress:
                for line in lines:
                    line = line.strip()
                    
                    # Skip comments and empty lines
                    if line.startswith('#') or not line:
                        progress.update(task, advance=1)
                        continue
                    
                    # Parse package name (handle extras and version specifiers)
                    package_name = self._parse_package_name(line)
                    
                    if not package_name:
                        logger.warning(f"Could not parse package name from: {line}")
                        progress.update(task, advance=1)
                        continue
                    
                    # Check if package is installed
                    try:
                        subprocess.run(
                            [sys.executable, '-m', 'pip', 'show', package_name],
                            check=True,
                            stdout=subprocess.DEVNULL,
                            stderr=subprocess.DEVNULL,
                            timeout=30
                        )
                    except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
                        logger.warning(f"Package not installed: {package_name}")
                        return False
                    
                    progress.update(task, advance=1)
                
                # Update cache
                try:
                    with open(cache_file, 'w', encoding='utf-8') as f:
                        f.write(f"Installed at {time.strftime('%Y-%m-%d %H:%M:%S')}")
                except Exception as e:
                    logger.warning(f"Failed to update cache file: {e}")
                
                return True
                
        except Exception as e:
            logger.error(f"Unexpected error during requirement check: {e}")
            return False
    
    def _parse_package_name(self, requirement_line):
        """Parse package name from a requirement line."""
        # Remove version specifiers
        line = requirement_line.strip()
        
        # Handle extras (e.g., package[extra])
        if '[' in line and ']' in line:
            line = line.split('[')[0]
        
        # Remove version specifiers
        for spec in ['>=', '>', '<=', '<', '==', '!=', '~=']:
            if spec in line:
                line = line.split(spec)[0]
        
        # Remove whitespace and @ for direct URLs
        line = line.split('@')[0].strip()
        
        return line if line else None
