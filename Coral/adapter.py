import os
import logging
import importlib
import asyncio
import time
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, List, Union, Set
from contextlib import asynccontextmanager
from .protocol import MessageEvent, ActionRequest, MessageRequest, NoticeEvent, BotResponse, Bot

logger = logging.getLogger(__name__)


class BaseAdapter(ABC):
    """适配器基类 - 处理平台消息的转换和路由"""
    PROTOCOL = "unknown"  # 默认协议

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.drivers: List[Any] = []
        self.event_bus = None
        self._handlers = {}
        self.bots: Dict[str, Bot] = {}  # 存储平台上的机器人实例
        self._pending_requests: Dict[str, asyncio.Future] = {}
        self._request_timeout = config.get("request_timeout", 30.0)  # 默认30秒超时
        self._max_concurrent_requests = config.get("max_concurrent_requests", 10)
        self._semaphore = asyncio.Semaphore(self._max_concurrent_requests)
        self._metrics = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "timeout_requests": 0,
            "avg_response_time": 0.0,
            "last_error": None,
            "last_error_time": None
        }

    def set_event_bus(self, event_bus):
        """设置事件总线"""
        self.event_bus = event_bus

    def add_driver(self, driver: Any):
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
            logger.warning(f"Bot {self_id} already exists for connected driver")

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
            logger.warning(f"Bot {self_id} not found for disconnected driver")

    def add_bot(self, self_id: str, config: Dict[str, Any] = {}, driver: Any = None) -> Bot:
        """添加机器人实例"""
        bot = Bot(
            platform=self.PROTOCOL,
            self_id=self_id,
            adapter=self,
            config=config
        )
        self.bots[self_id] = bot
        logger.debug(f"Added bot {self_id} for platform {bot.platform}")
        return bot

    def get_bot(self, self_id: str) -> Optional[Bot]:
        """获取机器人实例"""
        return self.bots.get(self_id)

    async def send_to_driver(self, data: Dict[str, Any]):
        """发送数据到所有驱动器"""
        if not self.drivers:
            logger.warning("No drivers available to send data")
            return
        
        send_tasks = []
        for driver in self.drivers:
            try:
                send_tasks.append(driver.send_action(data))
            except Exception as e:
                logger.error(f"Failed to send data to driver: {e}")
        
        if send_tasks:
            try:
                await asyncio.gather(*send_tasks, return_exceptions=True)
            except Exception as e:
                logger.error(f"Error during send to drivers: {e}")

    @abstractmethod
    async def handle_incoming(self, raw_data: Dict[str, Any]):
        """处理来自驱动器的原始数据"""
        raise NotImplementedError

    @abstractmethod
    def convert_to_protocol(self, event: Any) -> Union[MessageEvent, NoticeEvent, None]:
        """将平台原生事件转换为协议事件"""
        raise NotImplementedError

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

    async def _execute_with_timeout(self, coro, timeout: Optional[float] = None):
        """带超时执行的异步函数"""
        timeout = timeout or self._request_timeout
        try:
            return await asyncio.wait_for(coro, timeout=timeout)
        except asyncio.TimeoutError:
            self._metrics["timeout_requests"] += 1
            raise
        except Exception as e:
            self._metrics["failed_requests"] += 1
            self._metrics["last_error"] = str(e)
            self._metrics["last_error_time"] = time.time()
            raise

    @asynccontextmanager
    async def request_context(self, request_id: str, timeout: Optional[float] = None):
        """请求上下文管理器，提供超时和并发控制"""
        start_time = time.time()
        async with self._semaphore:
            try:
                yield
                self._metrics["successful_requests"] += 1
            except Exception as e:
                self._metrics["failed_requests"] += 1
                raise
            finally:
                self._metrics["total_requests"] += 1
                response_time = time.time() - start_time
                # 更新平均响应时间
                if self._metrics["total_requests"] > 0:
                    old_avg = self._metrics["avg_response_time"]
                    new_avg = old_avg + (response_time - old_avg) / self._metrics["total_requests"]
                    self._metrics["avg_response_time"] = new_avg

    def get_metrics(self) -> Dict[str, Any]:
        """获取适配器性能指标"""
        return self._metrics.copy()

    async def cleanup(self):
        """清理适配器资源"""
        # 取消所有待处理的请求
        for request_id, future in self._pending_requests.items():
            if not future.done():
                future.cancel()
        
        self._pending_requests.clear()
        self.bots.clear()
        self.drivers.clear()
        
        logger.debug(f"Adapter {self.PROTOCOL} cleaned up")


class AdapterManager:
    """适配器管理器 - 加载和协调多个适配器"""

    def __init__(self, event_bus, config):
        self.adapters: Dict[str, BaseAdapter] = {}
        self.event_bus = event_bus
        self.config = config
        self.bots: Dict[str, Bot] = {}  # 全局机器人实例映射
        self._load_tasks: Set[asyncio.Task] = set()
        
        # 将AdapterManager引用添加到event_bus，以便适配器可以访问
        self.event_bus._adapter_manager = self

        # 订阅MessageRequest和ActionRequest
        self.event_bus.subscribe(MessageRequest, self.handle_message)
        self.event_bus.subscribe(ActionRequest, self.handle_action)
        logger.debug("AdapterManager subscribed to MessageRequest and ActionRequest")

    def register_adapter(self, adapter: BaseAdapter, adapter_protocol: str):
        """注册适配器"""
        if adapter_protocol in self.adapters:
            logger.warning(
                f"Adapter {adapter_protocol} already registered, overwriting"
            )
            # 清理旧的适配器
            old_adapter = self.adapters[adapter_protocol]
            asyncio.create_task(old_adapter.cleanup())

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

    async def handle_message(self, message: MessageRequest):
        """处理消息请求"""
        platform_name = message.platform.lower()
        logger.debug(f"AdapterManager handling message for platform: {platform_name}")
        
        if platform_name in self.adapters:
            adapter = self.adapters[platform_name]
            logger.debug(f"Found adapter for {platform_name}, handling message...")
            try:
                async with adapter.request_context(f"message_{message.event_id}"):
                    result = await adapter._execute_with_timeout(
                        adapter.handle_outgoing_message(message)
                    )
                    logger.debug(f"Message handled successfully, result: {result}")
                    return result
            except asyncio.TimeoutError:
                logger.error(f"Message request timeout for platform: {platform_name}")
                return None
            except Exception as e:
                logger.error(f"Failed to handle message for platform {platform_name}: {e}")
                return None
        else:
            logger.warning(f"No adapter found for platform: {platform_name}")
            logger.warning(f"Available adapters: {list(self.adapters.keys())}")
            return None

    async def handle_action(self, action: ActionRequest):
        """处理主动动作请求"""
        platform_name = action.platform.lower()
        logger.debug(f"AdapterManager handling action for platform: {platform_name}")
        
        if platform_name in self.adapters:
            adapter = self.adapters[platform_name]
            logger.debug(f"Found adapter for {platform_name}, handling action...")
            try:
                async with adapter.request_context(f"action_{action.action_id}"):
                    result = await adapter._execute_with_timeout(
                        adapter.handle_outgoing_action(action)
                    )
                    logger.debug(f"Action handled successfully, result: {result}")
                    return result
            except asyncio.TimeoutError:
                logger.error(f"Action request timeout for platform: {platform_name}")
                return None
            except Exception as e:
                logger.error(f"Failed to handle action for platform {platform_name}: {e}")
                return None
        else:
            logger.warning(f"No adapter found for platform: {platform_name}")
            logger.warning(f"Available adapters: {list(self.adapters.keys())}")
            return None

    async def load_adapters(self):
        """加载所有适配器"""
        adapter_path = "./libraries/adapters"
        if not os.path.exists(adapter_path):
            logger.warning(f"Adapter directory not found: {adapter_path}")
            return

        adapter_modules = [
            f.split(".")[0]
            for f in os.listdir(adapter_path)
            if f.endswith("_adapter.py")
        ]
        
        if not adapter_modules:
            logger.debug("No adapter modules found")
            return

        loaded_count = 0
        for module in adapter_modules:
            adapter_name = None
            try:
                adapter_name = module.split("_adapter")[0]
                logger.debug(f"Loading adapter: {adapter_name}")
                
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
                    continue
                
                adapter_config = self.config.get(adapter_name + "_adapter", {})
                adapter_protocol = getattr(adapter_class, "PROTOCOL", None)
                
                if not adapter_protocol:
                    logger.warning(
                        f"Adapter {adapter_name} did not specify a protocol, skipping..."
                    )
                    continue
                
                adapter_instance = adapter_class(adapter_config)
                adapter_instance.set_event_bus(self.event_bus)
                self.register_adapter(adapter_instance, str(adapter_protocol))
                loaded_count += 1
                
                logger.info(f"Successfully loaded adapter: {adapter_name} (protocol: {adapter_protocol})")
                
            except ImportError as e:
                logger.error(f"Failed to import adapter module {adapter_name}: {e}")
            except AttributeError as e:
                logger.error(f"Adapter class not found in module {adapter_name}: {e}")
            except Exception as e:
                logger.exception(f"Error loading adapter {adapter_name}: {e}")
        
        logger.info(f"Loaded {loaded_count}/{len(adapter_modules)} adapters.")
        
        # 报告加载统计
        if loaded_count < len(adapter_modules):
            logger.warning(f"Failed to load {len(adapter_modules) - loaded_count} adapters")

    async def unload_adapter(self, adapter_protocol: str) -> bool:
        """卸载指定适配器"""
        adapter = self.adapters.get(adapter_protocol)
        if not adapter:
            logger.warning(f"Adapter {adapter_protocol} not found")
            return False
        
        try:
            # 清理适配器资源
            await adapter.cleanup()
            
            # 从管理器中移除
            del self.adapters[adapter_protocol]
            
            # 清理相关的机器人实例
            bots_to_remove = []
            for bot_id, bot in self.bots.items():
                if bot.platform.lower() == adapter_protocol.lower():
                    bots_to_remove.append(bot_id)
            
            for bot_id in bots_to_remove:
                del self.bots[bot_id]
            
            logger.debug(f"Successfully unloaded adapter: {adapter_protocol}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to unload adapter {adapter_protocol}: {e}")
            return False

    def get_adapter_stats(self) -> Dict[str, Any]:
        """获取适配器统计信息"""
        stats = {
            "total_adapters": len(self.adapters),
            "adapter_names": list(self.adapters.keys()),
            "total_bots": len(self.bots),
            "bots_by_platform": {}
        }
        
        # 收集每个适配器的详细信息
        adapter_details = {}
        for name, adapter in self.adapters.items():
            adapter_details[name] = {
                "protocol": adapter.PROTOCOL,
                "bot_count": len(adapter.bots),
                "driver_count": len(adapter.drivers),
                "metrics": adapter.get_metrics()
            }
        
        stats["adapter_details"] = adapter_details
        
        # 按平台统计机器人
        for bot in self.bots.values():
            platform = bot.platform.lower()
            if platform not in stats["bots_by_platform"]:
                stats["bots_by_platform"][platform] = 0
            stats["bots_by_platform"][platform] += 1
        
        return stats

    async def cleanup_all(self):
        """清理所有适配器资源"""
        cleanup_tasks = []
        for adapter_protocol, adapter in self.adapters.items():
            try:
                cleanup_task = asyncio.create_task(adapter.cleanup(), name=f"cleanup_{adapter_protocol}")
                cleanup_tasks.append(cleanup_task)
            except Exception as e:
                logger.error(f"Failed to create cleanup task for adapter {adapter_protocol}: {e}")
        
        if cleanup_tasks:
            await asyncio.gather(*cleanup_tasks, return_exceptions=True)
        
        self.adapters.clear()
        self.bots.clear()
        self._load_tasks.clear()
        
        logger.info("All adapters cleaned up")