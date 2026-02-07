from collections import defaultdict
import asyncio
import logging
import time
from typing import Union, Callable, Optional, Any
from dataclasses import dataclass
from .protocol import (
    MessageRequest,
    MessageEvent,
    NoticeEvent,
    CommandEvent,
    MessageChain,
    MessageSegment,
    Event
)

logger = logging.getLogger(__name__)


@dataclass
class EventBusMetrics:
    """事件总线性能指标"""
    total_events_processed: int = 0
    total_results_processed: int = 0
    avg_event_processing_time: float = 0.0
    avg_result_processing_time: float = 0.0
    max_queue_size: int = 0
    current_queue_size: int = 0
    total_errors: int = 0


class EventBus:
    def __init__(self):
        self._subscribers = defaultdict(list)
        self._middlewares = []
        self._result_queue: asyncio.Queue = asyncio.Queue()
        self._processing_task: Optional[asyncio.Task] = None
        self._running = False
        self._metrics = EventBusMetrics()
        self._batch_size = 10  # 批处理大小
        self._max_queue_size = 1000  # 最大队列大小

    async def initialize(self):
        """初始化事件总线"""
        self._running = True
        self._processing_task = asyncio.create_task(self._process_results())
        logger.info("Event bus initialized with async queue.")

    async def shutdown(self):
        """关闭事件总线"""
        self._running = False
        if self._processing_task:
            self._processing_task.cancel()
            try:
                # 等待任务完成，但忽略取消错误
                await asyncio.wait_for(self._processing_task, timeout=1.0)
            except (asyncio.CancelledError, asyncio.TimeoutError):
                pass
            except Exception as e:
                logger.debug(f"Error waiting for processing task: {e}")
        logger.info("Event bus shutdown.")

    def subscribe(self, event_type: type, handler: Callable, priority: int = 5):
        """订阅事件"""
        self._subscribers[event_type].append((handler, priority))
        self._subscribers[event_type].sort(key=lambda x: x[1], reverse=True)
        logger.debug(f"Subscribed {handler.__name__} to {event_type.__name__}")

    def unsubscribe(self, event_type: type, handler: Callable):
        """取消订阅事件"""
        if event_type in self._subscribers:
            self._subscribers[event_type] = [
                (h, p) for h, p in self._subscribers[event_type] if h != handler
            ]

    async def publish(self, event: Event) -> None:
        """发布事件（带中间件处理）"""
        start_time = time.time()
        self._metrics.total_events_processed += 1
        
        # 执行中间件链
        for middleware in self._middlewares:
            try:
                event = await middleware(event)
                if event is None:  # 中间件终止传播
                    return None
            except Exception as e:
                logger.error(f"Middleware error: {e}")
                self._metrics.total_errors += 1
                return None

        # 执行事件处理器
        results = []
        event_type = type(event)
        
        if event_type in self._subscribers:
            logger.debug(f"Found {len(self._subscribers[event_type])} subscribers for {event_type.__name__}")
            for handler, _ in self._subscribers[event_type]:
                try:
                    result = await handler(event)
                    if result is not None:  # 收集所有非None结果
                        logger.debug(
                            f"Event handler {handler.__name__} returns result: {type(result).__name__}"
                        )
                        results.append(result)
                        # 注意：这里不再break，让所有订阅者都能处理事件
                except Exception as e:
                    logger.exception(f"Event handler error: {e}")
                    self._metrics.total_errors += 1
        else:
            logger.debug(f"No subscribers for event type: {event_type.__name__}")

        # 处理所有结果
        if results:
            await self._enqueue_result(event, results)

        # 更新性能指标
        processing_time = time.time() - start_time
        self._metrics.avg_event_processing_time = (
            self._metrics.avg_event_processing_time * 
            (self._metrics.total_events_processed - 1) + 
            processing_time
        ) / self._metrics.total_events_processed

    async def _enqueue_result(self, event: Event, result: Any):
        """将结果加入队列"""
        logger.debug(f"Enqueuing result: {type(result).__name__}")
        
        if isinstance(result, list):
            for r in result:
                processed_result = self.convert_to_protocol(event, r) if isinstance(r, str) else r
                if processed_result is not None:
                    logger.debug(f"Adding to queue: {type(processed_result).__name__}")
                    await self._result_queue.put(processed_result)
        else:
            processed_result = (
                self.convert_to_protocol(event, result)
                if isinstance(result, str)
                else result
            )
            if processed_result is not None:
                logger.debug(f"Adding to queue: {type(processed_result).__name__}")
                await self._result_queue.put(processed_result)
        
        # 更新队列指标
        current_size = self._result_queue.qsize()
        self._metrics.current_queue_size = current_size
        if current_size > self._metrics.max_queue_size:
            self._metrics.max_queue_size = current_size

    def convert_to_protocol(
        self, event: Event, result: str
    ) -> Union[MessageRequest, None]:
        """将事件和结果转换为协议格式"""
        logger.warning(
            f"Result returned a string, which is deprecated and might be broken in a future version."
        )
        if not isinstance(event, Union[MessageEvent, NoticeEvent, CommandEvent]):
            logger.warning(f"Unsupported event type: {type(event)}")
            return None
        return MessageRequest(
            platform=event.platform,
            event_id=event.event_id,
            self_id=event.self_id,
            message=MessageChain([MessageSegment(type="text", data=result)]),
            user=event.user,
            group=event.group if hasattr(event, "group") else None,
        )

    def add_middleware(self, middleware: Callable):
        """添加中间件"""
        self._middlewares.append(middleware)

    async def _process_results(self):
        """异步处理缓冲区中的结果"""
        logger.debug("Start processing results in buffer.")
        
        while self._running:
            try:
                # 使用批处理提高性能
                batch = []
                for _ in range(self._batch_size):
                    try:
                        # 使用带超时的get，避免忙等待
                        result = await asyncio.wait_for(
                            self._result_queue.get(), 
                            timeout=0.1
                        )
                        if result is not None:
                            batch.append(result)
                            logger.debug(f"Got result from queue: {type(result).__name__}")
                    except asyncio.TimeoutError:
                        break  # 队列为空，处理当前批次
                
                if not batch:
                    # 队列为空，短暂休眠避免CPU占用
                    await asyncio.sleep(0.01)
                    continue
                
                # 批量处理结果
                start_time = time.time()
                for result in batch:
                    result_type = type(result)
                    logger.debug(f"Processing result from queue: {result_type.__name__}")
                    
                    if result_type in self._subscribers:
                        logger.debug(f"Found subscribers for {result_type.__name__}")
                        try:
                            await self.publish(result)
                        except Exception as e:
                            logger.error(f"Result handler error: {e}")
                            self._metrics.total_errors += 1
                    else:
                        logger.warning(f"No subscribers for result type: {result_type.__name__}")
                        logger.debug(f"Available subscriber types: {[k.__name__ for k in self._subscribers.keys()]}")
                    
                    self._result_queue.task_done()
                
                # 更新性能指标
                processing_time = time.time() - start_time
                self._metrics.total_results_processed += len(batch)
                self._metrics.avg_result_processing_time = (
                    self._metrics.avg_result_processing_time * 
                    (self._metrics.total_results_processed - len(batch)) + 
                    processing_time
                ) / self._metrics.total_results_processed
                
            except asyncio.CancelledError:
                logger.debug("Result processing cancelled")
                break
            except Exception as e:
                logger.error(f"Result processing error: {e}", exc_info=True)
                self._metrics.total_errors += 1
                await asyncio.sleep(0.1)  # 错误后短暂休眠
        
        logger.debug("Result processing stopped.")

    def get_metrics(self) -> EventBusMetrics:
        """获取性能指标"""
        return self._metrics

    def get_queue_size(self) -> int:
        """获取当前队列大小"""
        return self._result_queue.qsize()

    def is_queue_full(self) -> bool:
        """检查队列是否已满"""
        return self._result_queue.qsize() >= self._max_queue_size