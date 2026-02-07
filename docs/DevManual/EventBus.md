# 事件总线（Event Bus）指南

事件总线是 Coral 框架的核心组件，负责处理事件的发布、订阅和分发。它采用异步设计，支持中间件和批处理，为插件提供了灵活的事件处理机制。

## 基本使用

### 导入事件总线

```python
from Coral import event_bus
```

### 订阅事件

```python
from Coral.protocol import MessageEvent

# 订阅消息事件
@event_bus.subscribe(MessageEvent)
async def handle_message(event: MessageEvent):
    """处理消息事件"""
    if "你好" in event.message.to_plain_text():
        return "你好！我是Coral机器人"
```

### 发布事件

```python
from Coral.protocol import MessageEvent, UserInfo, MessageChain, MessageSegment

# 创建事件
event = MessageEvent(
    event_id="msg_123",
    platform="qq",
    self_id="1000000",
    message=MessageChain([MessageSegment.text("你好")]),
    user=UserInfo(platform="qq", user_id="123456789")
)

# 发布事件
await event_bus.publish(event)
```

## 事件类型

Coral 支持多种事件类型：

### 1. 消息事件（MessageEvent）
```python
from Coral.protocol import MessageEvent

@event_bus.subscribe(MessageEvent)
async def handle_message(event: MessageEvent):
    # 检查是否为私聊
    if event.is_private():
        return "这是私聊消息"
    
    # 检查是否被@
    if event.to_me():
        return "您提到了我"
    
    # 获取消息文本
    text = event.message.to_plain_text()
    return f"收到消息：{text}"
```

### 2. 通知事件（NoticeEvent）
```python
from Coral.protocol import NoticeEvent

@event_bus.subscribe(NoticeEvent)
async def handle_notice(event: NoticeEvent):
    if event.type == "group_increase":
        return f"欢迎新成员 {event.user.nickname} 加入群聊！"
    elif event.type == "friend_add":
        return f"已添加新好友：{event.user.nickname}"
```

### 3. 命令事件（CommandEvent）
```python
from Coral.protocol import CommandEvent

@event_bus.subscribe(CommandEvent)
async def handle_command(event: CommandEvent):
    if event.command == "weather":
        city = event.args[0] if event.args else "北京"
        return f"正在查询{city}的天气..."
```

### 4. 自定义事件
```python
from Coral.protocol import GenericEvent
from dataclasses import dataclass

# 定义自定义事件
@dataclass
class CustomEvent:
    platform: str
    name: str
    data: dict

# 订阅自定义事件
@event_bus.subscribe(CustomEvent)
async def handle_custom(event: CustomEvent):
    return f"处理自定义事件：{event.name}，数据：{event.data}"
```

## 中间件系统

事件总线支持中间件，可以在事件处理前后执行自定义逻辑：

### 创建中间件

```python
async def logging_middleware(event):
    """日志记录中间件"""
    import logging
    logger = logging.getLogger(__name__)
    
    logger.info(f"处理事件：{type(event).__name__}")
    
    # 修改事件（可选）
    if hasattr(event, 'platform'):
        event.platform = event.platform.upper()
    
    # 返回事件继续处理，返回None则终止
    return event

async def auth_middleware(event):
    """权限检查中间件"""
    from Coral import perm_system
    
    # 检查用户权限
    if hasattr(event, 'user'):
        has_perm = perm_system.check_perm(
            ["chat.allow"], 
            event.user.user_id,
            event.group.group_id if hasattr(event, 'group') and event.group else None
        )
        
        if not has_perm:
            logger.warning(f"用户 {event.user.user_id} 无权限")
            return None  # 终止事件处理
    
    return event
```

### 注册中间件

```python
# 添加中间件到事件总线
event_bus.add_middleware(logging_middleware)
event_bus.add_middleware(auth_middleware)

# 中间件按添加顺序执行
```

## 优先级系统

事件订阅支持优先级控制，数字越大优先级越高：

```python
# 高优先级处理器（先执行）
@event_bus.subscribe(MessageEvent, priority=10)
async def high_priority_handler(event: MessageEvent):
    if "紧急" in event.message.to_plain_text():
        return "紧急消息已处理"
    return None  # 返回None让其他处理器继续处理

# 低优先级处理器（后执行）
@event_bus.subscribe(MessageEvent, priority=1)
async def low_priority_handler(event: MessageEvent):
    return "这是默认回复"
```

## 结果处理

### 返回类型支持

事件处理器可以返回多种类型的结果：

```python
@event_bus.subscribe(MessageEvent)
async def handle_event(event: MessageEvent):
    # 1. 返回字符串（自动转换为MessageRequest）
    return "Hello, World!"
    
    # 2. 返回MessageRequest对象
    from Coral.protocol import MessageRequest, MessageChain, MessageSegment
    return MessageRequest(
        platform=event.platform,
        event_id=event.event_id,
        self_id=event.self_id,
        message=MessageChain([MessageSegment.text("Hello!")]),
        user=event.user
    )
    
    # 3. 返回列表（多个结果）
    return [
        "第一条消息",
        MessageRequest(...),  # 第二条消息
    ]
    
    # 4. 返回None（不发送回复）
    if event.user.user_id == "admin":
        return None  # 管理员消息不回复
```

### 结果队列

事件总线使用异步队列处理结果，避免阻塞：

```python
# 获取队列状态
queue_size = event_bus.get_queue_size()
is_full = event_bus.is_queue_full()

print(f"当前队列大小：{queue_size}")
print(f"队列是否已满：{is_full}")
```

## 性能监控

事件总线提供性能指标：

```python
# 获取性能指标
metrics = event_bus.get_metrics()

print(f"已处理事件数：{metrics.total_events_processed}")
print(f"已处理结果数：{metrics.total_results_processed}")
print(f"平均事件处理时间：{metrics.avg_event_processing_time:.4f}s")
print(f"平均结果处理时间：{metrics.avg_result_processing_time:.4f}s")
print(f"最大队列大小：{metrics.max_queue_size}")
print(f"当前队列大小：{metrics.current_queue_size}")
print(f"错误总数：{metrics.total_errors}")
```

## 高级用法

### 批量事件处理

```python
import asyncio
from Coral.protocol import MessageEvent

async def batch_process_events(events: list[MessageEvent]):
    """批量处理事件"""
    tasks = []
    for event in events:
        task = event_bus.publish(event)
        tasks.append(task)
    
    # 并发处理所有事件
    results = await asyncio.gather(*tasks, return_exceptions=True)
    return results
```

### 事件过滤

```python
from Coral import filters

# 使用过滤器组合
@event_bus.subscribe(MessageEvent)
async def filtered_handler(event: MessageEvent):
    # 检查消息是否包含关键词
    if not filters.contains("重要")(event):
        return None
    
    # 检查是否来自管理员
    if not filters.from_user(["admin1", "admin2"])(event):
        return None
    
    return "处理重要管理员消息"
```

### 错误处理

```python
@event_bus.subscribe(MessageEvent)
async def safe_handler(event: MessageEvent):
    try:
        # 可能出错的代码
        result = some_risky_operation(event)
        return result
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"事件处理错误：{e}", exc_info=True)
        
        # 返回错误信息或None
        return f"处理出错：{str(e)}"
```

## 最佳实践

### 1. 合理使用优先级
```python
# 安全检查和权限验证使用高优先级
@event_bus.subscribe(MessageEvent, priority=10)
async def security_check(event: MessageEvent):
    if not is_safe_message(event):
        return None  # 不安全消息，终止处理

# 业务逻辑使用中等优先级
@event_bus.subscribe(MessageEvent, priority=5)
async def business_logic(event: MessageEvent):
    return process_business(event)

# 日志记录使用低优先级
@event_bus.subscribe(MessageEvent, priority=1)
async def logging_handler(event: MessageEvent):
    log_message(event)
    return None  # 不返回结果，只记录日志
```

### 2. 避免阻塞操作
```python
# 错误示例：同步阻塞操作
@event_bus.subscribe(MessageEvent)
async def bad_handler(event: MessageEvent):
    import time
    time.sleep(5)  # ❌ 同步阻塞，会阻塞整个事件总线
    return "处理完成"

# 正确示例：异步非阻塞操作
@event_bus.subscribe(MessageEvent)
async def good_handler(event: MessageEvent):
    await asyncio.sleep(5)  # ✅ 异步等待，不会阻塞
    return "处理完成"
```

### 3. 合理处理返回值
```python
@event_bus.subscribe(MessageEvent)
async def smart_handler(event: MessageEvent):
    # 根据情况决定是否返回结果
    if should_reply(event):
        return "这是回复"
    else:
        return None  # 不回复，让其他处理器处理
    
    # 或者返回多个结果
    if needs_multiple_replies(event):
        return [
            "第一条消息",
            "第二条消息",
            MessageRequest(...)  # 复杂消息
        ]
```

### 4. 使用中间件复用逻辑
```python
# 创建可复用的中间件
async def rate_limit_middleware(event):
    """速率限制中间件"""
    user_id = event.user.user_id
    current_time = time.time()
    
    # 检查用户请求频率
    if is_rate_limited(user_id, current_time):
        logger.warning(f"用户 {user_id} 触发速率限制")
        return None  # 终止处理
    
    return event

# 注册到事件总线
event_bus.add_middleware(rate_limit_middleware)
```

## 故障排除

### 常见问题

1. **事件未触发**
   ```python
   # 检查事件类型是否正确
   print(f"订阅的事件类型：{MessageEvent}")
   print(f"发布的事件类型：{type(event)}")
   
   # 检查事件总线是否已初始化
   # 在插件初始化时调用
   await event_bus.initialize()
   ```

2. **结果未发送**
   ```python
   # 检查返回值类型
   # 字符串会自动转换，其他类型需要符合协议
   
   # 检查队列状态
   print(f"队列大小：{event_bus.get_queue_size()}")
   print(f"性能指标：{event_bus.get_metrics()}")
   ```

3. **性能问题**
   ```python
   # 监控性能指标
   metrics = event_bus.get_metrics()
   if metrics.avg_event_processing_time > 1.0:
       logger.warning("事件处理时间过长")
   
   if metrics.current_queue_size > 100:
       logger.warning("队列积压严重")
   ```

### 调试技巧

```python
import logging

# 启用调试日志
logging.basicConfig(level=logging.DEBUG)

# 添加调试中间件
async def debug_middleware(event):
    print(f"[DEBUG] 处理事件：{type(event).__name__}")
    print(f"[DEBUG] 事件数据：{event}")
    return event

event_bus.add_middleware(debug_middleware)
```

## 相关资源

- [协议文档](Protocol.md) - 了解事件和消息格式
- [插件开发指南](../PluginDev.md) - 学习如何开发插件
- [过滤器系统](Filters.md) - 使用过滤器简化事件处理

---

**最后更新：2026-01-31**  
**文档版本：v1.0.0**