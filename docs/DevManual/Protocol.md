# Coral 协议文档

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
```

### 2. 用户信息

```python
UserInfo(
    platform="qq",
    user_id="123456789",
    nickname="珊瑚用户",
    avatar="https://q.qlogo.cn/headimg_dl?dst_uin=123456789",
    roles=["VIP", "管理员"]
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

### 1. 消息事件 (MessageEvent)

```python
MessageEvent(
    event_id="msg_123456",
    platform="qq",
    self_id="1000000",
    message=MessageChain([...]),
    user=UserInfo(...),
    group=GroupInfo(...)  # 群聊时存在
)
```

### 2. 通知事件 (NoticeEvent)

```python
# 新成员入群
NoticeEvent(
    event_id="notice_123",
    platform="qq",
    type="group_increase",
    self_id="1000000",
    user=UserInfo(...),  # 新成员
    group=GroupInfo(...),
    operator=UserInfo(...)  # 操作者
)

# 好友添加
NoticeEvent(
    event_id="notice_456",
    platform="qq",
    type="friend_add",
    self_id="1000000",
    user=UserInfo(...)  # 新好友
)
```

### 3. 命令事件 (CommandEvent)

```python
CommandEvent(
    event_id="cmd_789",
    platform="qq",
    self_id="1000000",
    command="weather",
    raw_message=MessageChain([...]),
    user=UserInfo(...),
    args=["北京"]  # 命令参数
)
```

## 响应结构

### 1. 消息响应 (MessageRequest)

```python
MessageRequest(
    platform="qq",
    event_id="msg_123456",
    self_id="1000000",
    message=MessageChain([...]),
    at_sender=True,  # 是否@发送者
    recall_duration=60  # 60秒后撤回
)
```

### 2. 动作请求 (ActionRequest)

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
            ]),
            user=event.user,
            group=event.group if event.group else None
        )
```

### 2. 创建命令响应

```python
@on_command("ban", "封禁用户")
async def ban_user(event: CommandEvent):
    if not event.args:
        return "请指定要封禁的用户"
    
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
def create_welcome_message(user):
    return MessageRequest(
            platform=event.platform,
            event_id=event.event_id,
            self_id=event.self_id,
            message=MessageChain([
                MessageSegment.at(user.user_id),
                MessageSegment.text(" 欢迎加入群聊！\n"),
                MessageSegment.image("https://example.com/welcome.png"),
                MessageSegment.text("\n请查看群公告~")
            ]),
            user=event.user,
            group=event.group if event.group else None
        )
```

## 协议变更日志

| 版本   | 日期       | 变更说明                  |
|--------|------------|-------------------------|
| v1.0.0 | 2025-06-08 | 初始协议版本              |


> 提示：使用 `GenericEvent` 可以创建自定义事件类型实现高级功能