import os
import logging
import importlib
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, List
from .protocol import MessageEvent, ActionRequest, MessageRequest

logger = logging.getLogger(__name__)


class BaseAdapter(ABC):
    """适配器基类 - 处理平台消息的转换和路由"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.drivers: List[ABC] = []
        self.event_bus = None
        self._handlers = {}

    def set_event_bus(self, event_bus):
        """设置事件总线"""
        self.event_bus = event_bus

    def add_driver(self, driver: ABC):
        """添加驱动器"""
        self.drivers.append(driver)

    async def send_to_driver(self, data: Dict[str, Any]):
        for driver in self.drivers:
            await driver.send_action(data)

    @abstractmethod
    async def handle_incoming(self, raw_data: Dict[str, Any]):
        """处理来自驱动器的原始数据"""
        raise NotImplementedError

    @abstractmethod
    def convert_to_protocol(self, event: Any):
        """将平台原生事件转换为协议事件"""

    @abstractmethod
    async def handle_outgoing_action(self, action: ActionRequest):
        """处理发往平台的主动动作"""
        raise NotImplementedError

    @abstractmethod
    async def handle_outgoing_message(self, messgage: MessageRequest):
        """处理消息回复"""
        raise NotImplementedError

    def register_event_handler(self, event_type: type, handler: object):
        """注册特定事件类型的处理函数"""
        self._handlers[event_type] = handler

    async def publish_event(self, event):
        """发布事件到总线"""
        if self.event_bus:
            return await self.event_bus.publish(event)
        logger.warning("Event bus not set, cannot publish event")
        return None


class AdapterManager:
    """适配器管理器 - 加载和协调多个适配器"""

    def __init__(self, event_bus, config):
        self.adapters = {}
        self.event_bus = event_bus
        self.config = config

        self.event_bus.subscribe(ActionRequest, self.handle_action)
        self.event_bus.subscribe(MessageRequest, self.handle_message)

    def register_adapter(self, adapter: BaseAdapter, adapter_protocol: str):
        """注册适配器"""
        if adapter_protocol in self.adapters:
            logger.warning(
                f"Adapter {adapter_protocol} already registered, overwriting"
            )

        adapter.set_event_bus(self.event_bus)
        self.adapters[adapter_protocol] = adapter
        logger.debug(f"Adapter registered: {adapter_protocol}")

    def get_adapter(self, adapter_name: str) -> Optional[BaseAdapter]:
        """获取适配器实例"""
        return self.adapters.get(adapter_name.lower())

    async def handle_message(self, message: MessageEvent):
        """处理消息请求"""
        platform_name = message.platform.lower()
        if platform_name in self.adapters:
            return await self.adapters[platform_name].handle_outgoing_message(message)
        logger.warning(f"No adapter found for platform: {platform_name}")

    async def handle_action(self, action: ActionRequest):
        """处理主动动作请求"""
        platform_name = action.platform.lower()
        if platform_name in self.adapters:
            return await self.adapters[platform_name].handle_outgoing_action(action)
        logger.warning(f"No adapter found for platform: {platform_name}")

    async def load_adapters(self):
        """加载所有适配器"""
        adapter_path = "./libraries/adapters"
        adapter_modules = [
            f.split(".")[0]
            for f in os.listdir(adapter_path)
            if f.endswith("_adapter.py")
        ]
        for module in adapter_modules:
            try:
                adapter_name = module.split("_adapter")[0]
                adapter_obj = importlib.import_module(
                    f"libraries.adapters.{adapter_name}_adapter"
                )
                adapter_class = getattr(
                    adapter_obj, f"{adapter_name.capitalize()}Adapter"
                )
                if not issubclass(adapter_class, BaseAdapter):
                    logger.warning(
                        f"Found adapter {adapter_name} but it is not a subclass of BaseAdapter, skipping..."
                    )
                adapter_config = self.config.get(adapter_name + "_adapter", {})
                adapter_protocol = getattr(adapter_obj, "PROTOCOL", None)
                if not adapter_protocol:
                    logger.warning(
                        f"Adapter {adapter_name} did not specify a protocol, skipping..."
                    )
                    continue
                adapter_obj = adapter_class(adapter_config)
                adapter_obj.set_event_bus(self.event_bus)
                self.register_adapter(adapter_obj, str(adapter_protocol))
            except Exception as e:
                logger.exception(f"Error loading adapter {adapter_name}: {e}")
                continue
        logger.info(f"Loaded {len(self.adapters)} adapters.")
