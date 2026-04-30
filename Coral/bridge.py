"""
MessageBridge - 抽象接口，解耦 Driver 和 Adapter
"""

from abc import ABC, abstractmethod
from typing import Any, Callable, Dict


class MessageBridge(ABC):
    """
    Driver 和 Adapter 之间的通信桥梁

    职责：
    - Driver 通过 bridge 接收来自平台的数据
    - Adapter 通过 bridge 向平台发送数据
    - 负责 Bot 的生命周期管理
    """

    @abstractmethod
    async def send_to_platform(self, data: bytes) -> None:
        """发送数据到平台（由 Driver 调用）"""
        raise NotImplementedError

    @abstractmethod
    async def receive_from_platform(self, raw_data: Any) -> None:
        """接收来自平台的原始数据（由 Driver 调用）"""
        raise NotImplementedError

    @abstractmethod
    def register_driver_sender(self, driver_id: str, sender: Callable) -> None:
        """注册 Driver 的发送回调（由 Driver 调用）"""
        raise NotImplementedError

    @abstractmethod
    def register_bot_factory(self, factory: Callable) -> None:
        """注册 Bot 工厂函数（由 Driver 调用）"""
        raise NotImplementedError

    @abstractmethod
    def create_bot(self, self_id: str, config: Dict[str, Any]) -> Any:
        """创建 Bot 实例（由 Driver 在 on_connect 时调用）"""
        raise NotImplementedError

    @abstractmethod
    def remove_bot(self, self_id: str) -> None:
        """移除 Bot 实例（由 Driver 在 on_disconnect 时调用）"""
        raise NotImplementedError
