"""
Plugin Loader
=============

Handles plugin loading, dependency checking, and module management.
"""

import os
import sys
import time
import asyncio
import importlib.util
import logging
from typing import Dict, Any, Optional, List, Set, Tuple
from concurrent.futures import ThreadPoolExecutor

from .models import PluginMeta, PluginMetrics, PluginState, PluginLoadStatus
from .exceptions import PluginLoadError, PluginDependencyError

logger = logging.getLogger(__name__)


class PluginLoader:
    """Plugin loader with dependency-aware concurrent loading."""
    
    def __init__(self, config, register, max_concurrent_loads: int = 5):
        """
        Initialize plugin loader.
        
        Args:
            config: Configuration object
            register: Register object for executing functions
            max_concurrent_loads: Maximum number of concurrent plugin loads
        """
        self.config = config
        self.register = register
        self.max_concurrent_loads = max_concurrent_loads
        self._semaphore = asyncio.Semaphore(max_concurrent_loads)
        self._thread_pool = ThreadPoolExecutor(max_workers=4)
        
        # Cache for loaded modules
        self._loaded_modules: Dict[str, Any] = {}
    
    async def load_plugin_with_deps(
        self, 
        plugin_name: str, 
        plugin_path: str,
        meta: PluginMeta,
        loaded_plugins: Set[str]
    ) -> Tuple[bool, Optional[str], float]:
        """
        Load a plugin with its dependencies.
        
        Args:
            plugin_name: Name of the plugin
            plugin_path: Path to plugin directory
            meta: Plugin metadata
            loaded_plugins: Set of already loaded plugins
            
        Returns:
            Tuple of (success, error_message, load_time)
        """
        start_time = time.time()
        
        try:
            # Check if plugin is already loaded
            if plugin_name in loaded_plugins:
                logger.debug(f"Plugin {plugin_name} is already loaded")
                return True, None, 0.0
            
            # Check dependencies
            missing_deps = []
            for dep in meta.dependencies:
                if dep not in loaded_plugins:
                    missing_deps.append(dep)
            
            if missing_deps:
                error_msg = f"Missing dependencies: {', '.join(missing_deps)}"
                logger.warning(f"Cannot load plugin {plugin_name}: {error_msg}")
                return False, error_msg, 0.0
            
            # Check and install requirements
            if not await self._check_and_install_dependencies(plugin_name, plugin_path):
                error_msg = "Failed to install dependencies"
                return False, error_msg, 0.0
            
            # Load the plugin module
            module = await self._load_plugin_module(plugin_name, plugin_path)
            if not module:
                error_msg = "Failed to load module"
                return False, error_msg, 0.0
            
            # Record successful load
            load_time = time.time() - start_time
            logger.debug(f"Successfully loaded plugin {plugin_name} in {load_time:.2f}s")
            
            # Cache the module
            self._loaded_modules[plugin_name] = module
            
            return True, None, load_time
            
        except Exception as e:
            load_time = time.time() - start_time
            error_msg = str(e)
            logger.exception(f"Failed to load plugin {plugin_name}: {e}")
            return False, error_msg, load_time
    
    async def load_plugins_concurrently(
        self,
        plugins_to_load: List[Tuple[str, str, PluginMeta]],
        loaded_plugins: Set[str]
    ) -> Dict[str, Tuple[bool, Optional[str], float]]:
        """
        Load multiple plugins concurrently.
        
        Args:
            plugins_to_load: List of (plugin_name, plugin_path, meta) tuples
            loaded_plugins: Set of already loaded plugins
            
        Returns:
            Dictionary mapping plugin_name to (success, error, load_time)
        """
        results = {}
        
        async def load_with_semaphore(plugin_name: str, plugin_path: str, meta: PluginMeta):
            async with self._semaphore:
                success, error, load_time = await self.load_plugin_with_deps(
                    plugin_name, plugin_path, meta, loaded_plugins
                )
                return plugin_name, success, error, load_time
        
        # Create load tasks
        tasks = [
            load_with_semaphore(plugin_name, plugin_path, meta)
            for plugin_name, plugin_path, meta in plugins_to_load
        ]
        
        # Execute concurrently
        if tasks:
            task_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Process results
            for result in task_results:
                if isinstance(result, Exception):
                    logger.error(f"Task failed with exception: {result}")
                    continue
                
                plugin_name, success, error, load_time = result
                results[plugin_name] = (success, error, load_time)
                
                if success:
                    loaded_plugins.add(plugin_name)
        
        return results
    
    async def _check_and_install_dependencies(self, plugin_name: str, plugin_path: str) -> bool:
        """Check and install plugin dependencies."""
        requirements_file = os.path.join(plugin_path, "requirements.txt")
        if not os.path.exists(requirements_file):
            return True
        
        # Check if dependencies are already installed
        installed_flag = requirements_file + ".coral_installed"
        if os.path.exists(installed_flag):
            # Verify dependencies are still valid
            if await self._verify_dependencies(requirements_file):
                return True
            else:
                # Dependencies are invalid, reinstall
                os.remove(installed_flag)
        
        # Install dependencies
        logger.info(f"Installing dependencies for plugin {plugin_name}...")
        if not await self._install_dependencies(requirements_file):
            logger.error(f"Failed to install dependencies for plugin {plugin_name}")
            return False
        
        # Create installation marker
        try:
            with open(installed_flag, 'w') as f:
                f.write(str(time.time()))
        except Exception as e:
            logger.warning(f"Failed to create installation marker: {e}")
        
        return True
    
    async def _verify_dependencies(self, requirements_file: str) -> bool:
        """Verify that dependencies are installed and compatible."""
        try:
            # Use register to execute dependency check
            if hasattr(self.register, 'execute_function'):
                return await self.register.execute_function("check_pip_requirements", requirements_file)
            return True
        except Exception as e:
            logger.debug(f"Failed to verify dependencies: {e}")
            return False
    
    async def _install_dependencies(self, requirements_file: str) -> bool:
        """Install dependencies from requirements file."""
        try:
            # Use register to execute installation
            if hasattr(self.register, 'execute_function'):
                return await self.register.execute_function("install_pip_requirements", requirements_file)
            
            # Fallback: use pip directly
            import subprocess
            result = subprocess.run(
                [sys.executable, "-m", "pip", "install", "-r", requirements_file],
                capture_output=True,
                text=True
            )
            return result.returncode == 0
        except Exception as e:
            logger.exception(f"Failed to install dependencies: {e}")
            return False
    
    async def _load_plugin_module(self, plugin_name: str, plugin_path: str):
        """Load plugin module from file."""
        init_file = os.path.join(plugin_path, "__init__.py")
        
        try:
            # Create module spec
            spec = importlib.util.spec_from_file_location(
                f"plugins.{plugin_name}", init_file
            )
            if not spec:
                logger.error(f"Failed to create spec for plugin {plugin_name}")
                return None
            
            # Create and execute module
            module = importlib.util.module_from_spec(spec)
            sys.modules[f"plugins.{plugin_name}"] = module
            
            # Execute module in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                self._thread_pool,
                lambda: spec.loader.exec_module(module)
            )
            
            # 调用插件的加载钩子函数
            await self._call_load_hooks(plugin_name, module)
            
            return module
            
        except Exception as e:
            logger.exception(f"Failed to load module for plugin {plugin_name}: {e}")
            # Clean up sys.modules reference
            module_key = f"plugins.{plugin_name}"
            if module_key in sys.modules:
                del sys.modules[module_key]
            return None
    
    async def _call_load_hooks(self, plugin_name: str, module):
        """调用插件的加载钩子函数"""
        try:
            load_hooks = []
            
            # 查找所有标记为加载钩子的函数
            for attr_name in dir(module):
                attr = getattr(module, attr_name)
                if callable(attr) and hasattr(attr, '_is_load_hook'):
                    load_hooks.append(attr)
            
            if load_hooks:
                logger.debug(f"Found {len(load_hooks)} load hook(s) for plugin {plugin_name}")
                
                # 异步调用所有加载钩子
                for hook in load_hooks:
                    try:
                        if asyncio.iscoroutinefunction(hook):
                            await hook()
                        else:
                            # 如果是同步函数，在线程池中执行
                            loop = asyncio.get_event_loop()
                            await loop.run_in_executor(self._thread_pool, hook)
                        logger.debug(f"Executed load hook: {hook.__name__} for plugin {plugin_name}")
                    except Exception as e:
                        logger.error(f"Error executing load hook {hook.__name__} for plugin {plugin_name}: {e}")
                        # 继续执行其他钩子，不中断
            else:
                logger.debug(f"No load hooks found for plugin {plugin_name}")
                
        except Exception as e:
            logger.error(f"Error finding load hooks for plugin {plugin_name}: {e}")
    
    async def _call_unload_hooks(self, plugin_name: str, module):
        """调用插件的卸载钩子函数"""
        try:
            unload_hooks = []
            
            # 查找所有标记为卸载钩子的函数
            for attr_name in dir(module):
                attr = getattr(module, attr_name)
                if callable(attr) and hasattr(attr, '_is_unload_hook'):
                    unload_hooks.append(attr)
            
            if unload_hooks:
                logger.debug(f"Found {len(unload_hooks)} unload hook(s) for plugin {plugin_name}")
                
                # 异步调用所有卸载钩子
                for hook in unload_hooks:
                    try:
                        if asyncio.iscoroutinefunction(hook):
                            await hook()
                        else:
                            # 如果是同步函数，在线程池中执行
                            loop = asyncio.get_event_loop()
                            await loop.run_in_executor(self._thread_pool, hook)
                        logger.debug(f"Executed unload hook: {hook.__name__} for plugin {plugin_name}")
                    except Exception as e:
                        logger.error(f"Error executing unload hook {hook.__name__} for plugin {plugin_name}: {e}")
                        # 继续执行其他钩子，不中断
            else:
                logger.debug(f"No unload hooks found for plugin {plugin_name}")
                
        except Exception as e:
            logger.error(f"Error finding unload hooks for plugin {plugin_name}: {e}")
    
    async def unload_plugin(self, plugin_name: str) -> bool:
        """
        Unload a plugin.
        
        Args:
            plugin_name: Name of plugin to unload
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # 获取插件模块
            module = self._loaded_modules.get(plugin_name)
            
            # 调用卸载钩子
            if module:
                await self._call_unload_hooks(plugin_name, module)
            
            # Remove from loaded modules cache
            if plugin_name in self._loaded_modules:
                del self._loaded_modules[plugin_name]
            
            # Remove from sys.modules
            module_key = f"plugins.{plugin_name}"
            if module_key in sys.modules:
                del sys.modules[module_key]
            
            logger.debug(f"Successfully unloaded plugin {plugin_name}")
            return True
            
        except Exception as e:
            logger.exception(f"Failed to unload plugin {plugin_name}: {e}")
            return False
    
    def get_loaded_module(self, plugin_name: str):
        """Get loaded module for plugin."""
        return self._loaded_modules.get(plugin_name)
    
    def cleanup(self):
        """Clean up resources."""
        self._thread_pool.shutdown(wait=False)
        self._loaded_modules.clear()