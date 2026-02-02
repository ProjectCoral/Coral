import os
import logging
import importlib
import asyncio
import weakref
import gc
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, Set, List
from contextlib import asynccontextmanager
from .adapter import BaseAdapter

logger = logging.getLogger(__name__)


class BaseDriver(ABC):
    """驱动器基类 - 处理与平台的实际通信"""
    PROTOCOL = "unknown"  # 默认协议

    def __init__(self, adapter: BaseAdapter, config: Dict[str, Any]):
        self.config = config
        self.adapter = adapter
        self._running = False
        self._tasks: Set[asyncio.Task] = set()
        self._cleanup_callbacks: List[callable] = []
        self.adapter.add_driver(self)
        self.self_id = config.get("self_id", "unknown")  # 从配置中获取self_id
        logger.debug(f"Driver initialized with self_id: {self.self_id}")

    @abstractmethod
    async def start(self):
        """启动驱动器"""
        raise NotImplementedError

    @abstractmethod
    async def stop(self):
        """停止驱动器"""
        raise NotImplementedError

    @abstractmethod
    async def send_action(self, action: Dict[str, Any]):
        """发送动作到平台"""
        raise NotImplementedError

    async def handle_receive(self, raw_data: Dict[str, Any]):
        """处理接收到的原始数据"""
        if self.adapter:
            await self.adapter.handle_incoming(raw_data)
        else:
            logger.warning("No adapter set, cannot handle incoming data")

    def on_connect(self):
        """当驱动器连接时调用"""
        logger.info(f"Driver connected with self_id: {self.self_id}")
        if self.adapter:
            # 通知适配器创建Bot对象
            self.adapter.create_bot_for_driver(self)

    def on_disconnect(self):
        """当驱动器断开连接时调用"""
        logger.info(f"Driver disconnected with self_id: {self.self_id}")
        if self.adapter:
            # 通知适配器移除Bot对象
            self.adapter.remove_bot_for_driver(self)

    def add_cleanup_callback(self, callback: callable):
        """添加清理回调函数"""
        self._cleanup_callbacks.append(callback)

    async def _cleanup(self):
        """执行清理操作"""
        # 取消所有任务
        for task in self._tasks:
            if not task.done():
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
        
        # 执行清理回调
        for callback in self._cleanup_callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback()
                else:
                    callback()
            except Exception as e:
                logger.error(f"Cleanup callback error: {e}")
        
        # 清空集合和列表
        self._tasks.clear()
        self._cleanup_callbacks.clear()
        
        # 强制垃圾回收
        gc.collect()

    def create_task(self, coro, name: Optional[str] = None) -> asyncio.Task:
        """创建并跟踪任务"""
        task = asyncio.create_task(coro, name=name)
        self._tasks.add(task)
        task.add_done_callback(lambda t: self._tasks.discard(t))
        return task

    @asynccontextmanager
    async def connection_context(self):
        """连接上下文管理器，确保资源正确释放"""
        try:
            yield self
        finally:
            await self._cleanup()


class DriverManager:
    """驱动器管理器 - 管理驱动器的生命周期"""

    def __init__(self, config, adapter_manager):
        self.config = config
        self.drivers: Dict[str, BaseDriver] = {}
        self._running = False
        self.adapter_manager = adapter_manager
        self._driver_refs = weakref.WeakValueDictionary()  # 弱引用，避免循环引用
        logger.debug("DriverManager initialized")

    def register_driver(self, driver: BaseDriver, driver_name: str):
        """注册驱动器"""
        if driver_name in self.drivers:
            logger.warning(f"Driver {driver_name} already registered, overwriting")
            # 清理旧的驱动器
            old_driver = self.drivers[driver_name]
            asyncio.create_task(old_driver._cleanup())

        self.drivers[driver_name] = driver
        self._driver_refs[driver_name] = driver
        logger.debug(f"Driver registered: {driver_name}")

    async def start_all(self):
        """启动所有驱动器"""
        if self._running:
            logger.warning("Drivers are already running")
            return

        self._running = True
        tasks = []
        for driver_name, driver in self.drivers.items():
            try:
                task = driver.create_task(driver.start(), name=f"driver_{driver_name}")
                tasks.append(task)
                logger.info(f"Starting driver: {driver_name}")
            except Exception as e:
                logger.error(f"Failed to start driver {driver_name}: {e}")
        
        # 等待所有驱动器启动完成
        if tasks:
            try:
                await asyncio.gather(*tasks, return_exceptions=True)
                logger.info("All drivers started")
            except Exception as e:
                logger.error(f"Error during driver startup: {e}")
        else:
            logger.warning("No drivers to start")

    async def stop_all(self):
        """停止所有驱动器"""
        if not self._running:
            logger.warning("Drivers are not running")
            return

        logger.info("Stopping all drivers...")
        stop_tasks = []
        for driver_name, driver in self.drivers.items():
            try:
                stop_task = asyncio.create_task(driver.stop(), name=f"stop_{driver_name}")
                stop_tasks.append(stop_task)
                logger.debug(f"Stopping driver: {driver_name}")
            except Exception as e:
                logger.error(f"Failed to stop driver {driver_name}: {e}")
        
        # 等待所有驱动器停止
        if stop_tasks:
            try:
                await asyncio.gather(*stop_tasks, return_exceptions=True)
            except Exception as e:
                logger.error(f"Error during driver shutdown: {e}")
        
        # 清理所有驱动器
        cleanup_tasks = []
        for driver_name, driver in self.drivers.items():
            try:
                cleanup_task = asyncio.create_task(driver._cleanup(), name=f"cleanup_{driver_name}")
                cleanup_tasks.append(cleanup_task)
            except Exception as e:
                logger.error(f"Failed to cleanup driver {driver_name}: {e}")
        
        if cleanup_tasks:
            await asyncio.gather(*cleanup_tasks, return_exceptions=True)
        
        self._running = False
        logger.info("All drivers stopped and cleaned up")

    def get_driver(self, driver_name: str) -> Optional[BaseDriver]:
        """获取驱动器实例"""
        return self.drivers.get(driver_name.lower(), None)

    async def load_drivers(self):
        """加载所有驱动器"""
        driver_path = "./libraries/drivers"
        if not os.path.exists(driver_path):
            logger.warning(f"Driver directory not found: {driver_path}")
            return

        driver_modules = [
            f.split(".")[0] for f in os.listdir(driver_path) if f.endswith("_driver.py")
        ]
        
        if not driver_modules:
            logger.info("No driver modules found")
            return

        loaded_count = 0
        for module in driver_modules:
            driver_name = None
            try:
                driver_name = module.split("_driver")[0]
                logger.debug(f"Loading driver: {driver_name}")
                
                driver_obj = importlib.import_module(
                    f"libraries.drivers.{driver_name}_driver"
                )
                driver_class = getattr(driver_obj, f"{driver_name.capitalize()}Driver")
                
                if not issubclass(driver_class, BaseDriver):
                    logger.warning(
                        f"Found driver {driver_name} but it is not a subclass of BaseDriver, skipping..."
                    )
                    continue
                
                driver_config = self.config.get(driver_name + "_driver", {})
                driver_protocol = getattr(driver_class, "PROTOCOL", None)
                
                if not driver_protocol:
                    logger.warning(
                        f"Driver {driver_name} did not specify a protocol, skipping..."
                    )
                    continue
                
                pend_adapter = self.adapter_manager.get_adapter(driver_protocol)
                if not pend_adapter:
                    logger.warning(
                        f"Driver {driver_name} requires adapter {driver_protocol}, but it is not registered, skipping..."
                    )
                    continue
                
                # 创建驱动器实例
                driver_instance = driver_class(pend_adapter, driver_config)
                self.register_driver(driver_instance, driver_name)
                loaded_count += 1
                
                logger.info(f"Successfully loaded driver: {driver_name} (protocol: {driver_protocol})")
                
            except ImportError as e:
                logger.error(f"Failed to import driver module {driver_name}: {e}")
            except AttributeError as e:
                logger.error(f"Driver class not found in module {driver_name}: {e}")
            except Exception as e:
                logger.exception(f"Failed to load driver {driver_name}: {e}")
        
        logger.info(f"Loaded {loaded_count}/{len(driver_modules)} drivers.")
        
        # 报告加载统计
        if loaded_count < len(driver_modules):
            logger.warning(f"Failed to load {len(driver_modules) - loaded_count} drivers")

    async def unload_driver(self, driver_name: str) -> bool:
        """卸载指定驱动器"""
        driver = self.drivers.get(driver_name)
        if not driver:
            logger.warning(f"Driver {driver_name} not found")
            return False
        
        try:
            # 停止驱动器
            if self._running:
                await driver.stop()
            
            # 清理资源
            await driver._cleanup()
            
            # 从管理器中移除
            del self.drivers[driver_name]
            if driver_name in self._driver_refs:
                del self._driver_refs[driver_name]
            
            logger.info(f"Successfully unloaded driver: {driver_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to unload driver {driver_name}: {e}")
            return False

    def get_driver_stats(self) -> Dict[str, Any]:
        """获取驱动器统计信息"""
        stats = {
            "total_drivers": len(self.drivers),
            "running": self._running,
            "driver_names": list(self.drivers.keys()),
            "weak_ref_count": len(self._driver_refs)
        }
        
        # 收集每个驱动器的详细信息
        driver_details = {}
        for name, driver in self.drivers.items():
            driver_details[name] = {
                "self_id": driver.self_id,
                "protocol": getattr(driver, "PROTOCOL", "unknown"),
                "running": driver._running,
                "active_tasks": len(driver._tasks),
                "cleanup_callbacks": len(driver._cleanup_callbacks)
            }
        
        stats["driver_details"] = driver_details
        return stats

    async def __aenter__(self):
        """异步上下文管理器入口"""
        await self.load_drivers()
        await self.start_all()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口"""
        await self.stop_all()
        # 清理所有引用
        self.drivers.clear()
        self._driver_refs.clear()
        gc.collect()