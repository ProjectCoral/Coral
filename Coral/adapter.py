import os
import logging
import importlib
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, List, Union
from .protocol import MessageEvent, ActionRequest, MessageRequest, NoticeEvent, BotResponse, Bot

logger = logging.getLogger(__name__)


class BaseAdapter(ABC):
    """适配器基类 - 处理平台消息的转换和路由"""
    PROTOCOL = "unknown"  # 默认协议

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.drivers: List[ABC] = []
        self.event_bus = None
        self._handlers = {}
        self.bots: Dict[str, Bot] = {}  # 存储平台上的机器人实例

    def set_event_bus(self, event_bus):
        """设置事件总线"""
        self.event_bus = event_bus

    def add_driver(self, driver: ABC):
        """添加驱动器"""
        self.drivers.append(driver)

    def create_bot_for_driver(self, driver):
        """为连接的驱动器创建Bot对象"""
        # 使用驱动器的self_id创建Bot对象
        self_id = getattr(driver, 'self_id', 'unknown')
        if self_id not in self.bots:
            bot = self.add_bot(self_id, self.config, driver)
            # 添加到全局注册表
            if hasattr(self, 'event_bus') and self.event_bus:
                # 通过事件总线获取AdapterManager并注册Bot
                try:
                    # 假设event_bus有一个指向AdapterManager的引用
                    if hasattr(self.event_bus, '_adapter_manager'):
                        self.event_bus._adapter_manager.add_bot(bot)
                except Exception as e:
                    logger.warning(f"Failed to register bot in global registry: {e}")
            logger.info(f"Created bot {self_id} for connected driver")
        else:
            logger.info(f"Bot {self_id} already exists for connected driver")

    def remove_bot_for_driver(self, driver):
        """为断开连接的驱动器移除Bot对象"""
        self_id = getattr(driver, 'self_id', 'unknown')
        if self_id in self.bots:
            # 从全局注册表中移除
            if hasattr(self, 'event_bus') and self.event_bus:
                try:
                    if hasattr(self.event_bus, '_adapter_manager'):
                        adapter_manager = self.event_bus._adapter_manager
                        if self_id in adapter_manager.bots:
                            del adapter_manager.bots[self_id]
                except Exception as e:
                    logger.warning(f"Failed to unregister bot from global registry: {e}")
            
            # 从本地注册表中移除
            del self.bots[self_id]
            logger.info(f"Removed bot {self_id} for disconnected driver")
        else:
            logger.info(f"Bot {self_id} not found for disconnected driver")

    def add_bot(self, self_id: str, config: Dict[str, Any] = {}, driver: Any = None) -> Bot:
        """添加机器人实例"""
        bot = Bot(
            platform=self.PROTOCOL,
            self_id=self_id,
            adapter=self,
            config=config
        )
        self.bots[self_id] = bot
        logger.info(f"Added bot {self_id} for platform {bot.platform}")
        return bot

    def get_bot(self, self_id: str) -> Optional[Bot]:
        """获取机器人实例"""
        return self.bots.get(self_id)

    async def send_to_driver(self, data: Dict[str, Any]):
        for driver in self.drivers:
            await driver.send_action(data)

    @abstractmethod
    async def handle_incoming(self, raw_data: Dict[str, Any]):
        """处理来自驱动器的原始数据"""
        raise NotImplementedError

    @abstractmethod
    def convert_to_protocol(self, event: Any) -> Union[MessageEvent, NoticeEvent, None]:
        """将平台原生事件转换为协议事件"""

    @abstractmethod
    async def handle_outgoing_action(self, action: ActionRequest) -> Union[BotResponse, None]:
        """处理发往平台的主动动作"""
        raise NotImplementedError

    @abstractmethod
    async def handle_outgoing_message(self, message: MessageRequest) -> Union[BotResponse, None]:
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
        self.bots: Dict[str, Bot] = {}  # 全局机器人实例映射
        
        # 将AdapterManager引用添加到event_bus，以便适配器可以访问
        self.event_bus._adapter_manager = self

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
    
    def add_bot(self, bot: Bot):
        """添加全局机器人实例"""
        self.bots[bot.self_id] = bot
        logger.debug(f"Registered bot {bot.self_id} in global registry")

    def get_bot(self, self_id: str) -> Optional[Bot]:
        """根据self_id获取机器人实例"""
        return self.bots.get(self_id)

    def get_bots_by_platform(self, platform: str) -> List[Bot]:
        """根据平台获取所有机器人实例"""
        platform = platform.lower()
        return [bot for bot in self.bots.values() if bot.platform.lower() == platform]

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
            adapter_name = None
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
                adapter_protocol = getattr(adapter_class, "PROTOCOL", None)
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