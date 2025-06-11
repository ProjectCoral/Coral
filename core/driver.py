import os
import logging
import importlib
import asyncio
from .adapter import BaseAdapter
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, List

logger = logging.getLogger(__name__)

class BaseDriver(ABC):
    """驱动器基类 - 处理与平台的实际通信"""
    
    def __init__(self, adapter: BaseAdapter, config: Dict[str, Any]):
        self.config = config
        self.adapter = adapter
        self._running = False
        self.adapter.add_driver(self)
    @abstractmethod
    async def start(self):
        """启动驱动器"""
        pass
    
    @abstractmethod
    async def stop(self):
        """停止驱动器"""
        pass
    
    @abstractmethod
    async def send_action(self, action: Dict[str, Any]):
        """发送动作到平台"""
        pass
    
    async def handle_receive(self, raw_data: Dict[str, Any]):
        """处理接收到的原始数据"""
        if self.adapter:
            await self.adapter.handle_incoming(raw_data)
        else:
            logger.warning("No adapter set, cannot handle incoming data")

class DriverManager:
    """驱动器管理器 - 管理驱动器的生命周期"""
    
    def __init__(self, config, adapter_manager):
        self.config = config
        self.drivers = {}
        self._running = False
        self.adapter_manager = adapter_manager
    
    def register_driver(self, driver: BaseDriver, driver_name: str):
        """注册驱动器"""
        if driver_name in self.drivers:
            logger.warning(f"Driver {driver_name} already registered, overwriting")
        
        self.drivers[driver_name] = driver
        logger.debug(f"Driver registered: {driver_name}")
    
    async def start_all(self):
        """启动所有驱动器"""
        if self._running:
            return
        
        self._running = True
        tasks = [driver.start() for driver in self.drivers.values()]
        await asyncio.gather(*tasks)
        logger.info("All drivers started")
    
    async def stop_all(self):
        """停止所有驱动器"""
        if not self._running:
            return
        
        await asyncio.gather(*(driver.stop() for driver in self.drivers.values()))
        self._running = False
        logger.info("All drivers stopped")
    
    def get_driver(self, driver_name: str) -> Optional[BaseDriver]:
        """获取驱动器实例"""
        return self.drivers.get(driver_name.lower(), None)
    
    async def load_drivers(self):
        """加载所有驱动器"""
        driver_path = "./libraries/drivers"
        driver_modules = [f.split(".")[0] for f in os.listdir(driver_path) if f.endswith("_driver.py")]
        for module in driver_modules:
            try:
                driver_name = module.split("_driver")[0]
                driver_obj = importlib.import_module(f"libraries.drivers.{driver_name}_driver")
                driver_class = getattr(driver_obj, f"{driver_name.capitalize()}Driver")
                if not issubclass(driver_class, BaseDriver):
                    logger.warning(f"Found driver {driver_name} but it is not a subclass of BaseDriver, skipping...")
                driver_config = self.config.get(driver_name + "_driver", {})
                driver_protocol = getattr(driver_obj, "PROTOCOL", None)
                if not driver_protocol:
                    logger.warning(f"Driver {driver_name} did not specify a protocol, skipping...")
                    continue
                pend_adapter = self.adapter_manager.get_adapter(driver_protocol)
                if not pend_adapter:
                    logger.warning(f"Driver {driver_name} requires adapter {driver_protocol}, but it is not registered, skipping...")
                    continue
                self.register_driver(driver_class(pend_adapter, driver_config), driver_name)
            except Exception as e:
                logger.exception(f"Failed to load driver {driver_name}: {e}")
                continue
        logger.info(f"Loaded {len(self.drivers)} drivers.")
    

