# 适配器开发指南

适配器负责平台协议与核心协议的转换，需实现以下核心功能：

## 1. 继承基类

```python
from core.adapter import BaseAdapter

PROTOCOL = "my_platform"  # 必须定义的协议标识

class MyPlatformAdapter(BaseAdapter):
    
```

## 2. 实现抽象方法

```python
async def handle_incoming(self, raw_data: Dict[str, Any]):
    """处理来自平台的原始数据"""
    # 1. 解析原始数据
    event = self._parse_raw(raw_data)
    
    # 2. 转换为协议事件
    protocol_event = self.convert_to_protocol(event)
    
    # 3. 发布到事件总线
    await self.publish_event(protocol_event)

def convert_to_protocol(self, platform_event) -> MessageEvent:
    """平台原生事件转协议事件"""
    return MessageEvent(
        event_id=platform_event["id"],
        platform=self.PROTOCOL,
        self_id=self.config["bot_id"],
        message=self._build_message_chain(platform_event),
        user=UserInfo(...),
        group=GroupInfo(...) if platform_event.get("group") else None
    )

async def handle_outgoing_action(self, action: ActionRequest):
    """处理主动动作（如禁言、踢人）"""
    # 1. 转换为平台特定格式
    platform_action = {
        "type": action.type,
        "target": action.target.user_id,
        "data": action.data
    }
    
    # 2. 发送到驱动器
    await self.send_to_driver(platform_action)

async def handle_outgoing_message(self, message: MessageRequest):
    """处理消息回复"""
    # 1. 转换为平台消息格式
    platform_msg = self._convert_message(message)
    
    # 2. 发送到驱动器
    await self.send_to_driver({
        "type": "message",
        "content": platform_msg
    })
```

## 3. 事件处理建议

- 使用 `register_event_handler()` 注册特定事件处理函数
- 在 `handle_incoming` 中处理多种事件类型：

  ```python
  if raw_data["type"] == "message":
      event = self.convert_message_event(raw_data)
  elif raw_data["type"] == "notice":
      event = self.convert_notice_event(raw_data)
  ```

完整开发模板见框架的 `libraries/adapters` 目录，包含适配器的完整实现示例。
