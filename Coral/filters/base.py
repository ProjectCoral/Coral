"""
过滤器基类模块
包含 EventFilter、MessageFilter、CompositeFilter 等基类
"""
import logging
from typing import Any, List, Type
from abc import ABC, abstractmethod

from ..protocol import MessageEvent

logger = logging.getLogger(__name__)


class EventFilter(ABC):
    """事件过滤器基类"""
    
    def __init__(self):
        self._cached_supported_types = None
        self._warning_logged = False
    
    @property
    def supported_event_types(self) -> List[Type]:
        """延迟计算并缓存支持的事件类型"""
        if self._cached_supported_types is None:
            self._cached_supported_types = self._get_supported_event_types()
        return self._cached_supported_types
    
    def _get_supported_event_types(self) -> List[Type]:
        """子类可以重写此方法返回支持的事件类型"""
        return []
    
    def is_supported(self, event_type: Type) -> bool:
        """检查是否支持指定事件类型"""
        supported = self.supported_event_types
        if not supported:
            return True
        
        # 检查事件类型是否是支持类型的子类
        for supported_type in supported:
            if issubclass(event_type, supported_type):
                return True
        return False
    
    async def check_with_warning(self, event: Any) -> bool:
        """检查事件，如果不支持则发出警告并返回True"""
        event_type = type(event)
        
        # 快速路径：如果过滤器支持所有类型，直接检查
        if not self.supported_event_types:
            return await self.check(event)
        
        # 检查是否支持
        if not self.is_supported(event_type):
            # 只记录一次警告，避免重复日志
            if not self._warning_logged:
                logger.warning(
                    f"过滤器 {self.__class__.__name__} 不支持事件类型 {event_type.__name__}，"
                    f"将默认返回True。过滤器设计用于：{[t.__name__ for t in self.supported_event_types]}"
                )
                self._warning_logged = True
            return True
        
        return await self.check(event)
    
    @abstractmethod
    async def check(self, event: Any) -> bool:
        """检查事件是否满足过滤条件"""
        pass
    
    def __and__(self, other: 'EventFilter') -> 'EventFilter':
        """逻辑与操作"""
        from .message_filters import AndFilter
        return AndFilter(self, other)
    
    def __or__(self, other: 'EventFilter') -> 'EventFilter':
        """逻辑或操作"""
        from .message_filters import OrFilter
        return OrFilter(self, other)
    
    def __invert__(self) -> 'EventFilter':
        """逻辑非操作"""
        from .message_filters import NotFilter
        return NotFilter(self)


class MessageFilter(EventFilter):
    """消息过滤基类（兼容旧版本）"""
    
    def _get_supported_event_types(self) -> List[Type]:
        return [MessageEvent]
    
    @abstractmethod
    async def check(self, event: MessageEvent) -> bool:
        """检查事件是否满足过滤条件"""
        pass


class CompositeFilter(EventFilter):
    """复合过滤器基类"""
    
    def __init__(self, *filters: EventFilter):
        super().__init__()
        self.filters = filters
    
    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({', '.join(map(repr, self.filters))})"
    
    def _get_supported_event_types(self) -> List[Type]:
        """复合过滤器支持所有子过滤器都支持的事件类型"""
        if not self.filters:
            return []
        
        # 获取所有子过滤器支持的事件类型
        supported_sets = []
        for filter_obj in self.filters:
            supported = filter_obj.supported_event_types
            if not supported:  # 如果某个过滤器支持所有类型，则复合过滤器也支持所有类型
                return []
            supported_sets.append(set(supported))
        
        # 求交集
        common_types = set.intersection(*supported_sets)
        return list(common_types)
