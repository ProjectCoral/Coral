from collections import defaultdict
import asyncio
import logging
import threading
import queue
import time
from typing import Union
from .protocol import (
    MessageRequest,
    MessageEvent,
    NoticeEvent,
    CommandEvent,
    MessageChain,
    MessageSegment,
)

logger = logging.getLogger(__name__)


class EventBus:
    def __init__(self):
        self._subscribers = defaultdict(list)
        self._middlewares = []
        self._result_queue = None
        self._task = None

    async def initialize(self):
        self._result_queue = queue.Queue()
        threading.Thread(target=self._process_results, daemon=True).start()
        logger.info("Event bus buffer initialized.")

    def subscribe(self, event_type: type, handler: callable, priority: int = 5):
        """订阅事件"""
        self._subscribers[event_type].append((handler, priority))
        self._subscribers[event_type].sort(key=lambda x: x[1], reverse=True)

    def unsubscribe(self, event_type: type, handler: callable):
        """取消订阅事件"""
        if event_type in self._subscribers:
            self._subscribers[event_type] = [
                (h, p) for h, p in self._subscribers[event_type] if h != handler
            ]

    async def publish(self, event: object) -> None:
        """发布事件（带中间件处理）"""
        # 执行中间件链
        for middleware in self._middlewares:
            event = await middleware(event)
            if event is None:  # 中间件终止传播
                return None

        # 执行事件处理器
        result = None
        for handler, _ in self._subscribers[type(event)]:
            try:
                result = await handler(event)
                if result:  # 处理器可以返回结果中断传播
                    logger.debug(
                        f"Event handler {handler.__name__} returns result: {result}"
                    )
                    break
            except Exception as e:
                logger.error(f"Event handler error: {e}")
        if isinstance(result, list):
            for r in result:
                r = self.convert_to_protocol(event, r) if isinstance(r, str) else r
                self._result_queue.put(r) if r is not None else None
        else:
            result = (
                self.convert_to_protocol(event, result)
                if isinstance(result, str)
                else result
            )
            self._result_queue.put(result) if result is not None else None

    def convert_to_protocol(
        self, event: Union[MessageEvent, NoticeEvent, CommandEvent], result: str
    ) -> MessageRequest:
        """将事件和结果转换为协议格式"""
        logger.warning(
            f"Result returned a string, which is deprecated and might be broken in a future version."
        )
        return MessageRequest(
            platform=event.platform,
            event_id=event.event_id,
            self_id=event.self_id,
            message=MessageChain([MessageSegment(type="text", data=result)]),
            user=event.user,
            group=event.group if hasattr(event, "group") else None,
        )

    def add_middleware(self, middleware: callable):
        """添加中间件"""
        self._middlewares.append(middleware)

    def _process_results(self):
        """处理缓冲区中的结果"""
        logger.debug("Start processing results in buffer.")
        while True:
            try:
                if self._result_queue.empty():
                    time.sleep(0.1)
                    continue
                result = self._result_queue.get()
                if result is None:  # 跳过空结果
                    continue
                if type(result) in self._subscribers:
                    try:
                        asyncio.run(self.publish(result))
                    except Exception as e:
                        logger.error(f"Result handler error: {e}")
                else:
                    logger.warning(f"No subscribers for result type: {type(result)}")
            except Exception as e:
                logger.error(f"Result processing error: {e}")
