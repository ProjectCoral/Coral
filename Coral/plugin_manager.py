import os
import sys
import ast
import time
import importlib.util
import logging
import asyncio
import hashlib
from typing import Dict, Any, Optional, List, Set
from dataclasses import dataclass
from functools import lru_cache

PLUGINMANAGER_VERSION = "260131_early_developement"

logger = logging.getLogger(__name__)


@dataclass
class PluginMetrics:
    """插件性能指标"""
    load_time: float = 0.0
    total_calls: int = 0
    avg_execution_time: float = 0.0
    total_errors: int = 0
    last_error: Optional[str] = None
    last_loaded: float = 0.0


@dataclass
class PluginMeta:
    """插件元数据"""
    name: str
    version: str = "1.0.0"
    author: str = "Unknown"
    description: str = ""
    compatibility: int = 250606
    dependencies: List[str] = None
    requirements: List[str] = None
    
    def __post_init__(self):
        if self.dependencies is None:
            self.dependencies = []
        if self.requirements is None:
            self.requirements = []


class PluginManager:
    plugin_dir = "./plugins"

    def __init__(self, register, config, perm_system, plugin_dir="./plugins"):
        self.config = config
        self.perm_system = perm_system
        self.plugin_dir = self.config.get("plugin_dir", plugin_dir)
        self.config.set("pluginmanager_version", PLUGINMANAGER_VERSION)
        self.pluginmanager_version = self.config.get("pluginmanager_version")
        self.pluginmanager_meta = 250606
        self.register = register
        self.plugins: List[str] = []
        self._loaded: Set[str] = set()
        self._plugin_metrics: Dict[str, PluginMetrics] = {}
        self._plugin_meta_cache: Dict[str, PluginMeta] = {}
        self._max_concurrent_loads = 5  # 最大并发加载数
        
        # 创建插件目录如果不存在
        if not os.path.exists(self.plugin_dir):
            os.makedirs(self.plugin_dir, exist_ok=True)
            logger.info(f"Created plugin directory: {self.plugin_dir}")

    async def load_all_plugins(self):
        """加载所有插件（改进的错误处理和并发控制）"""
        if not os.path.exists(self.plugin_dir):
            logger.warning(
                f"[yellow]Plugin directory {self.plugin_dir} does not exist, skipping plugin loading...[/]"
            )
            return

        logger.info(f"Loading plugins from {self.plugin_dir}")
        
        # 获取所有插件目录
        plugin_dirs = []
        for item in os.listdir(self.plugin_dir):
            plugin_path = os.path.join(self.plugin_dir, item)
            if os.path.isdir(plugin_path):
                init_file = os.path.join(plugin_path, "__init__.py")
                if os.path.exists(init_file):
                    plugin_dirs.append(item)
        
        if not plugin_dirs:
            logger.info("No plugins found to load.")
            return
        
        # 使用信号量控制并发加载数量
        semaphore = asyncio.Semaphore(self._max_concurrent_loads)
        
        async def load_with_semaphore(plugin_name):
            async with semaphore:
                return await self.load_plugin(plugin_name)
        
        # 创建加载任务
        load_tasks = [
            load_with_semaphore(plugin_name)
            for plugin_name in plugin_dirs
        ]
        
        # 使用asyncio.gather但设置return_exceptions=True，避免一个插件失败影响其他
        results = await asyncio.gather(*load_tasks, return_exceptions=True)
        
        # 处理结果
        successful_loads = 0
        for plugin_name, result in zip(plugin_dirs, results):
            if isinstance(result, Exception):
                logger.error(f"Failed to load plugin {plugin_name}: {result}")
            elif result is not None:
                successful_loads += 1
        
        # 注册插件管理器命令和权限
        self._register_plugin_manager_commands()
        
        logger.info(f"Successfully loaded {successful_loads}/{len(plugin_dirs)} plugins.")
        
        # 记录性能指标
        self._log_loading_metrics()

    async def load_plugin(self, plugin_name: str) -> Optional[str]:
        """加载单个插件（改进版本）"""
        if plugin_name in self._loaded:
            logger.warning(
                f"[yellow]Plugin {plugin_name} is already loaded, skipping...[/]"
            )
            return None

        start_time = time.time()
        plugin_path = os.path.join(self.plugin_dir, plugin_name)
        
        # 检查插件目录
        if not os.path.isdir(plugin_path):
            return None
        
        init_file = os.path.join(plugin_path, "__init__.py")
        if not os.path.exists(init_file):
            return None

        try:
            # 1. 检查并安装依赖
            if not await self._check_and_install_dependencies(plugin_name, plugin_path):
                logger.error(
                    f"[red]Failed to install dependencies for plugin {plugin_name}, skipping...[/]"
                )
                return None

            # 2. 获取插件元数据（使用缓存）
            meta = await self._get_plugin_meta_cached(init_file)
            if not meta:
                logger.warning(
                    f"[yellow]Plugin {plugin_name} did not declare compatibility"
                    ", which is deprecated and might be broken in a future version.[/]"
                )
            elif meta.compatibility < self.pluginmanager_meta:
                logger.error(
                    f"[red]Plugin {plugin_name} (v{meta.version}) is not compatible "
                    f"with this version of Plugin Manager (requires {self.pluginmanager_meta}+), skipping...[/]"
                )
                return None
                
            # 3. 加载插件模块
            module = await self._load_plugin_module(plugin_name, init_file)
            if not module:
                return None

            # 4. 注册插件
            self._loaded.add(plugin_name)
            self.plugins.append(plugin_name)
            
            # 5. 记录性能指标
            load_time = time.time() - start_time
            self._plugin_metrics[plugin_name] = PluginMetrics(
                load_time=load_time,
                last_loaded=time.time()
            )
            
            logger.info(f"Successfully loaded plugin {plugin_name} in {load_time:.2f}s")
            
            # 6. 触发插件加载完成事件
            await self._trigger_plugin_loaded_event(plugin_name, meta)
            
            return plugin_name
            
        except Exception as e:
            logger.exception(f"[red]Failed to load plugin {plugin_name}: {e}[/]")
            # 清理可能的部分加载状态
            if plugin_name in self._loaded:
                self._loaded.remove(plugin_name)
            if plugin_name in self.plugins:
                self.plugins.remove(plugin_name)
            
            # 记录错误指标
            if plugin_name not in self._plugin_metrics:
                self._plugin_metrics[plugin_name] = PluginMetrics()
            self._plugin_metrics[plugin_name].total_errors += 1
            self._plugin_metrics[plugin_name].last_error = str(e)
            
            return None

    async def _check_and_install_dependencies(self, plugin_name: str, plugin_path: str) -> bool:
        """检查并安装插件依赖"""
        requirements_file = os.path.join(plugin_path, "requirements.txt")
        if not os.path.exists(requirements_file):
            return True

        # 检查依赖是否已安装
        installed_flag = requirements_file + ".coral_installed"
        if os.path.exists(installed_flag):
            # 验证依赖是否仍然有效
            if await self.register.execute_function("check_pip_requirements", requirements_file):
                return True
            else:
                # 依赖已失效，重新安装
                os.remove(installed_flag)

        # 安装依赖
        logger.info(f"Installing dependencies for plugin {plugin_name}...")
        if not await self.register.execute_function("install_pip_requirements", requirements_file):
            logger.error(f"Failed to install dependencies for plugin {plugin_name}")
            return False

        # 创建安装标记
        with open(installed_flag, 'w') as f:
            f.write(str(time.time()))
        
        return True

    @lru_cache(maxsize=32)
    def _get_file_hash(self, filepath: str) -> str:
        """获取文件哈希值用于缓存"""
        if not os.path.exists(filepath):
            return ""
        with open(filepath, 'rb') as f:
            return hashlib.md5(f.read()).hexdigest()

    async def _get_plugin_meta_cached(self, init_file: str) -> Optional[PluginMeta]:
        """获取插件元数据（带缓存）"""
        file_hash = self._get_file_hash(init_file)
        cache_key = f"{init_file}:{file_hash}"
        
        # 检查缓存
        if cache_key in self._plugin_meta_cache:
            return self._plugin_meta_cache[cache_key]
        
        # 解析元数据
        meta_dict = self._parse_plugin_meta(init_file)
        if not meta_dict:
            return None
        
        # 转换为PluginMeta对象
        try:
            meta = PluginMeta(
                name=meta_dict.get('name', os.path.basename(os.path.dirname(init_file))),
                version=meta_dict.get('version', '1.0.0'),
                author=meta_dict.get('author', 'Unknown'),
                description=meta_dict.get('description', ''),
                compatibility=int(meta_dict.get('compatibility', self.pluginmanager_meta)),
                dependencies=meta_dict.get('dependencies', []),
                requirements=meta_dict.get('requirements', [])
            )
            
            # 缓存结果
            self._plugin_meta_cache[cache_key] = meta
            return meta
            
        except (ValueError, TypeError) as e:
            logger.warning(f"Invalid plugin metadata in {init_file}: {e}")
            return None

    def _parse_plugin_meta(self, plugin_init_file: str) -> Optional[Dict[str, Any]]:
        """解析插件元数据"""
        if not os.path.exists(plugin_init_file):
            return None

        with open(plugin_init_file, "r", encoding="utf-8") as f:
            source = f.read()

        try:
            tree = ast.parse(source)
        except SyntaxError:
            return None

        for node in tree.body:
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name) and target.id == "__plugin_meta__":
                        value_node = node.value
                        if isinstance(value_node, ast.Dict):
                            # 将AST字典转换为Python字典
                            result = {}
                            for key_node, value_node in zip(value_node.keys, value_node.values):
                                if isinstance(key_node, ast.Constant):
                                    key = key_node.value
                                elif isinstance(key_node, ast.Name):
                                    key = key_node.id
                                else:
                                    continue
                                    
                                if isinstance(value_node, ast.Constant):
                                    value = value_node.value
                                elif isinstance(value_node, ast.List):
                                    value = []
                                    for item in value_node.elts:
                                        if isinstance(item, ast.Constant):
                                            value.append(item.value)
                                else:
                                    value = ast.unparse(value_node) if hasattr(ast, 'unparse') else repr(value_node)
                                    
                                result[key] = value
                            return result
        return None

    async def _load_plugin_module(self, plugin_name: str, init_file: str):
        """加载插件模块"""
        try:
            spec = importlib.util.spec_from_file_location(
                f"plugins.{plugin_name}", init_file
            )
            if not spec:
                logger.error(f"Failed to create spec for plugin {plugin_name}")
                return None
            
            module = importlib.util.module_from_spec(spec)
            sys.modules[f"plugins.{plugin_name}"] = module
            
            # 执行模块
            spec.loader.exec_module(module)
            return module
            
        except Exception as e:
            logger.exception(f"Failed to load module for plugin {plugin_name}: {e}")
            # 清理sys.modules中的引用
            module_key = f"plugins.{plugin_name}"
            if module_key in sys.modules:
                del sys.modules[module_key]
            return None

    async def _trigger_plugin_loaded_event(self, plugin_name: str, meta: Optional[PluginMeta]):
        """触发插件加载完成事件"""
        try:
            from Coral.protocol import GenericEvent
            from Coral import event_bus
            
            event_data = {
                "plugin_name": plugin_name,
                "plugin_version": meta.version if meta else "unknown",
                "timestamp": time.time()
            }
            
            await event_bus.publish(
                GenericEvent(
                    name="plugin_loaded",
                    platform="coral",
                    data=event_data
                )
            )
        except Exception as e:
            logger.debug(f"Failed to trigger plugin loaded event: {e}")

    def _register_plugin_manager_commands(self):
        """注册插件管理器命令"""
        self.perm_system.register_perm("pluginmanager", "Base Permission")
        self.perm_system.register_perm(
            "pluginmanager.show_plugins", "Permission to show available plugins"
        )
        self.perm_system.register_perm(
            "pluginmanager.metrics", "Permission to view plugin metrics"
        )
        
        self.register.register_command(
            "plugins",
            "List all available plugins",
            self.show_plugins,
            ["pluginmanager", "pluginmanager.show_plugins"],
        )
        self.register.register_command(
            "reload",
            "Reload all plugins",
            self.reload_command,
            ["pluginmanager"]
        )
        self.register.register_command(
            "plugin_metrics",
            "Show plugin performance metrics",
            self.show_plugin_metrics,
            ["pluginmanager", "pluginmanager.metrics"]
        )

    def _log_loading_metrics(self):
        """记录加载性能指标"""
        if not self._plugin_metrics:
            return
        
        total_load_time = sum(metrics.load_time for metrics in self._plugin_metrics.values())
        avg_load_time = total_load_time / len(self._plugin_metrics) if self._plugin_metrics else 0
        
        logger.info(
            f"Plugin loading metrics: "
            f"Total plugins: {len(self.plugins)}, "
            f"Total load time: {total_load_time:.2f}s, "
            f"Average load time: {avg_load_time:.2f}s"
        )

    async def show_plugins(self, *args):
        """显示已加载的插件"""
        plugins_info = []
        for plugin in self.plugins:
            metrics = self._plugin_metrics.get(plugin)
            load_time = f"{metrics.load_time:.2f}s" if metrics else "unknown"
            plugins_info.append(f"  • {plugin} (load time: {load_time})")
        
        plugins_list = "\n".join(plugins_info) if plugins_info else "  No plugins loaded"
        
        return (
            f"Available plugins ({len(self.plugins)} loaded):\n"
            f"{plugins_list}\n\n"
            f"Plugin Manager Version: {self.pluginmanager_version}"
        )

    async def show_plugin_metrics(self, *args):
        """显示插件性能指标"""
        if not self._plugin_metrics:
            return "No plugin metrics available."
        
        metrics_info = []
        for plugin_name, metrics in self._plugin_metrics.items():
            metrics_info.append(
                f"  • {plugin_name}:\n"
                f"    - Load time: {metrics.load_time:.2f}s\n"
                f"    - Last loaded: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(metrics.last_loaded))}\n"
                f"    - Total errors: {metrics.total_errors}\n"
                f"    - Last error: {metrics.last_error or 'None'}"
            )
        
        return "Plugin Performance Metrics:\n" + "\n".join(metrics_info)

    async def reload_plugins(self):
        """重新加载所有插件"""
        if not os.path.exists(self.plugin_dir):
            logger.warning(
                f"[yellow]Plugin directory {self.plugin_dir} does not exist, skipping plugin reloading...[/]"
            )
            return

        logger.info(f"Reloading plugins from {self.plugin_dir}")
        
        # 清空当前状态
        old_plugins = self.plugins.copy()
        self.plugins.clear()
        self._loaded.clear()
        
        # 重新加载所有插件
        await self.load_all_plugins()
        
        # 记录重新加载的插件
        reloaded_count = len(self.plugins)
        logger.info(f"Reloaded {reloaded_count} plugins (previously had {len(old_plugins)})")

    async def reload_command(self, *args, **kwargs):
        """重新加载命令"""
        start_time = time.time()
        
        try:
            await self.reload_plugins()
        except Exception as e:
            logger.error(f"Failed to reload plugins: {e}")
            return f"Failed to reload plugins: {e}"
        
        end_time = time.time()
        reload_time = end_time - start_time
        
        logger.warning(
            "[yellow]It's not recommended to reload frequently, as it can cause issues. "
            "Please use the reload command only when necessary.[/]"
        )
        
        return f"Plugins reloaded in {reload_time:.2f}s. Loaded {len(self.plugins)} plugins."

    async def reload_plugin(self, plugin_name: str):
        """重新加载单个插件"""
        plugin_path = os.path.join(self.plugin_dir, plugin_name)
        if not os.path.isdir(plugin_path):
            return None
        
        init_file = os.path.join(plugin_path, "__init__.py")
        if not os.path.exists(init_file):
            return None

        try:
            # 从已加载集合中移除
            if plugin_name in self._loaded:
                self._loaded.remove(plugin_name)
            
            # 从插件列表中移除
            if plugin_name in self.plugins:
                self.plugins.remove(plugin_name)
            
            # 清理sys.modules中的引用
            module_key = f"plugins.{plugin_name}"
            if module_key in sys.modules:
                del sys.modules[module_key]
            
            # 清理元数据缓存
            file_hash = self._get_file_hash(init_file)
            cache_key = f"{init_file}:{file_hash}"
            if cache_key in self._plugin_meta_cache:
                del self._plugin_meta_cache[cache_key]
            
            # 重新加载插件
            return await self.load_plugin(plugin_name)
            
        except Exception as e:
            logger.exception(f"[red]During plugin reloading, an error occurred: {e}[/]")
            logger.error(
                f"[red]Failed to reload plugin {plugin_name}, skipping...[/]"
            )
            return None