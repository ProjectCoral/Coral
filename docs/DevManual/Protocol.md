# Coral 协议文档

## 协议变更日志

| 版本   | 日期       | 变更说明                  |
|--------|------------|-------------------------|
| v1 | 2025-06-08 | 初始协议版本              |
| v2 | 2025-06-09 | 添加事件基类<br>统一事件字段<br>新增BotResponse响应<br>添加实用方法 |
| v3 | 2026-02-02 | 新增事件便捷回复方法<br>Bot链式调用设计<br>MessageRequest构建器模式<br>MessageChain链式构建 |

你可以从 Coral 中导入 `PROTOCOL_VERSION` 查看当前协议版本

```python
from Coral import PROTOCOL_VERSION
print(PROTOCOL_VERSION)  # 3
```

## 核心协议类

### 1. 消息结构

```python
# 消息段（文本）
MessageSegment.text("你好")

# 消息段（图片）
MessageSegment.image("https://example.com/image.png", width=200, height=200)

# 消息段（@用户）
MessageSegment.at("123456789")

# 消息链（组合多个消息段）
chain = MessageChain([
    MessageSegment.at("123456789"),
    MessageSegment.text(" 你好！"),
    MessageSegment.image("https://example.com/welcome.png")
])

# 转换为纯文本
plain_text = chain.to_plain_text()  # 返回：" 你好！"
```

### 2. 用户信息

```python
UserInfo(
    platform="qq",
    user_id="123456789",
    nickname="珊瑚用户",
    cardname="群名片",  # 新增字段
    avatar="https://q.qlogo.cn/headimg_dl?dst_uin=123456789",
    roles=["VIP", "管理员"]  # 角色列表
)
```

### 3. 群组信息

```python
GroupInfo(
    platform="qq",
    group_id="987654321",
    name="珊瑚交流群",
    owner_id="123456789",
    member_count=100
)
```

## 事件类型

### 0. 事件基类 (Event)

```python
class Event:
    platform: str    # 平台名称
    self_id: str     # 机器人ID
    time: float      # 事件时间戳
```

### 1. 消息事件 (MessageEvent)

```python
MessageEvent(
    event_id="msg_123456",  # 事件唯一ID
    platform="qq",
    self_id="1000000",
    time=1717939200.123,    # 时间戳
    message=MessageChain([...]),
    user=UserInfo(...),
    group=GroupInfo(...),  # 群聊时存在
    
    # 实用方法
    is_private(),  # 是否私聊
    is_group(),    # 是否群聊
    to_me()  # 是否被@
)
```

### 2. 通知事件 (NoticeEvent)

```python
# 新成员入群
NoticeEvent(
    event_id="notice_123",  # 事件唯一ID
    platform="qq",
    type="group_increase",   # 通知类型（新增）
    self_id="1000000",
    time=1717939200.123,     # 时间戳
    user=UserInfo(...),      # 新成员
    group=GroupInfo(...),
    operator=UserInfo(...)   # 操作者
    
    # 实用方法
    to_me(),  # 目标是否为自身
    is_operator()      # 操作者是否为自身
)

# 好友添加
NoticeEvent(
    event_id="notice_456",
    platform="qq",
    type="friend_add",      # 通知类型（新增）
    self_id="1000000",
    time=1717939200.123,
    user=UserInfo(...)      # 新好友
)
```

### 3. 命令事件 (CommandEvent)

```python
CommandEvent(
    event_id="cmd_789",      # 事件唯一ID
    platform="qq",
    self_id="1000000",
    time=1717939200.123,     # 时间戳
    command="weather",       # 命令名称
    raw_message=MessageChain([...]),  # 原始消息（新增）
    user=UserInfo(...),
    args=["北京"]             # 命令参数
)
```

## 响应结构

### 1. 机器人响应 (BotResponse)

```python
BotResponse(
    success=True,            # 操作状态
    message="操作成功",       # 响应消息
    data={"result": "ok"},   # 响应数据
    event_id="msg_123456"    # 关联事件ID
)
```

### 2. 消息响应 (MessageRequest)

```python
MessageRequest(
    platform="qq",
    event_id="msg_123456",    # 回复的事件ID
    self_id="1000000",
    message=MessageChain([...]),
    at_sender=True,           # 是否@发送者
    recall_duration=60        # 60秒后撤回
)
```

### 3. 动作请求 (ActionRequest)

```python
# 踢出群成员
ActionRequest(
    platform="qq",
    self_id="1000000",
    type="kick_member",
    target=UserInfo(...),
    data={"reason": "违反群规"}
)

# 发送私聊消息
ActionRequest(
    platform="qq",
    self_id="1000000",
    type="send_private_msg",
    target=UserInfo(...),
    data={"message": MessageChain([...])}
)
```

## 协议使用示例

### 1. 处理消息事件

```python
@on_message()
async def handle_message(event: MessageEvent):
    if "天气" in event.message.to_plain_text():
        return MessageRequest(
            platform=event.platform,
            event_id=event.event_id,
            self_id=event.self_id,
            message=MessageChain([
                MessageSegment.text("请问你想查询哪个城市的天气？")
            ])
        )
```

### 2. 创建命令响应

```python
@on_command("ban", "封禁用户")
async def ban_user(event: CommandEvent):
    if not event.args:
        return BotResponse(
            success=False,
            message="请指定要封禁的用户",
            event_id=event.event_id
        )
    
    return ActionRequest(
        platform=event.platform,
        self_id=event.self_id,
        type="ban_user",
        target=UserInfo(user_id=event.args[0]),
        data={"duration": 3600, "reason": "违反规则"}
    )
```

### 3. 发送复合消息

```python
def create_welcome_message(event, user):
    return MessageRequest(
        platform=event.platform,
        event_id=event.event_id,
        self_id=event.self_id,
        message=MessageChain([
            MessageSegment.at(user.user_id),
            MessageSegment.text(" 欢迎加入群聊！\n"),
            MessageSegment.image("https://example.com/welcome.png"),
            MessageSegment.text("\n请查看群公告~")
        ])
    )
```
### 4. 自定义事件类型

使用 `GenericEvent` 可以创建自定义事件类型实现全局广播

```python
GenericEvent(
    platform="qq",
    name="custom_event",  # 自定义事件名称
    self_id="1000000",
    time=time.time()
)
```

## 实用方法说明

1. **消息转换**：
   ```python
   message.to_plain_text()  # 提取纯文本内容
   ```

2. **事件检测**：
   ```python
   event.is_private()     # 是否私聊
   event.is_group()       # 是否群聊
   event.to_me() # 是否提及机器人
   ```

3. **对象转换**：
   ```python
   obj.to_dict()         # 转换为字典
   Class.from_dict(data) # 从字典创建对象
   ```

## 快速消息构建

Coral Protocol v3 引入了多项新功能，使插件开发更加简洁高效：

### 1. 事件便捷回复

所有事件类（MessageEvent、NoticeEvent、CommandEvent）都新增了`reply()`方法，简化回复操作：

```python
@on_message()
async def handle_message(event: MessageEvent):
    # 简单回复
    return event.reply("你好！")
    
    # 带选项的回复
    return event.reply("你好！", at_sender=True, recall_duration=60)
    
    # 回复MessageChain
    message = MessageChain().add_text("Hello ").add_at(event.user.user_id)
    return event.reply(message)
```

### 2. MessageChain链式构建

MessageChain新增链式构建方法，使消息构建更加流畅：

```python
# 使用类方法创建
chain1 = MessageChain.text("Hello")
chain2 = MessageChain.image("http://example.com/image.jpg")

# 链式调用构建复杂消息
chain3 = MessageChain() \
    .add_text("欢迎 ") \
    .add_at("123456") \
    .add_text(" 加入群聊！") \
    .add_image("http://example.com/welcome.jpg") \
    .add_face("123")
```

### 3. MessageRequest构建器模式

MessageRequest新增构建器模式，支持链式调用：

```python
# 从事件创建构建器
builder = MessageRequest.builder(event)

# 链式构建消息请求
request = builder \
    .text("Hello") \
    .at("123456") \
    .image("http://example.com/img.jpg") \
    .set_at_sender() \
    .recall_after(30) \
    .build()

# 直接使用构建器发送复杂消息
@on_message()
async def handle_message(event: MessageEvent):
    return MessageRequest.builder(event) \
        .text("收到你的消息：") \
        .text(event.message.to_plain_text()) \
        .set_at_sender() \
        .build()
```

### 4. Bot链式调用设计

Bot类新增链式调用接口，使主动发送消息更加直观：

```python
# 获取Bot实例
bot = get_bot("qq", "bot_123")

# 传统方式
await bot.send_message("Hello", user=user_info)

# 链式调用发送消息
await bot.to_group("10001").send("Hello, group!")
await bot.to_user("123456").at_sender().send("Hello, user!")
await bot.to_group("10001").recall_after(60).send("这条消息60秒后撤回")
```

### 5. 插件示例

```python
from Coral import on_message, contains
from Coral.protocol import MessageChain

@on_message(filters=contains("天气"))
async def weather_handler(event):
    # 使用便捷回复方法
    return event.reply(
        MessageChain()
            .add_text("当前天气：")
            .add_text("☀️ 晴天 25°C")
            .add_text("\n建议：适合外出")
    )

@on_message(filters=contains("帮助"))
async def help_handler(event):
    # 使用MessageRequest构建器
    return MessageRequest.builder(event) \
        .text("可用命令：") \
        .text("\n1. 天气 - 查询天气") \
        .text("\n2. 帮助 - 显示帮助") \
        .set_at_sender() \
        .build()
```