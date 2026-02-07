# Coral API 接口

Coral 提供了丰富的 API 接口，用于与平台进行交互。API 接口主要通过适配器调用，支持 OneBot V11 协议兼容接口。

## API 状态

> **注意**：Coral 的 API 接口仍在积极开发中，部分功能可能尚未完全实现或存在限制。

## 核心 API

### 1. 消息发送 API

#### 发送私聊消息
```python
from Coral import get_bot

# 获取 Bot 实例
bot = get_bot("123456789")

# 发送私聊消息
await bot.send_message(
    message="Hello, World!",
    user_id="987654321"
)

# 发送复杂消息
from Coral.protocol import MessageChain, MessageSegment
message = MessageChain([
    MessageSegment.text("你好！"),
    MessageSegment.at("987654321"),
    MessageSegment.image("https://example.com/image.png")
])
await bot.send_message(message=message, user_id="987654321")
```

#### 发送群聊消息
```python
await bot.send_message(
    message="群公告：请注意群规",
    group_id="1000001",
    at_sender=True  # 是否@发送者
)
```

### 2. 消息操作 API

#### 撤回消息
```python
await bot.send_action(
    action_type="delete_message",
    message_id="msg_123456789"
)
```

#### 获取消息详情
```python
# 通过适配器获取消息详情
message_info = await adapter.get_message(message_id="msg_123456789")
```

### 3. 群组管理 API

#### 踢出群成员
```python
from Coral.protocol import UserInfo

user = UserInfo(platform="qq", user_id="987654321")
await bot.send_action(
    action_type="kick_member",
    target=user,
    group_id="1000001",
    reason="违反群规"
)
```

#### 禁言成员
```python
await bot.send_action(
    action_type="ban_member",
    target=user,
    group_id="1000001",
    duration=3600,  # 禁言时长（秒）
    reason="发送广告"
)
```

#### 设置群管理员
```python
await bot.send_action(
    action_type="set_group_admin",
    target=user,
    group_id="1000001",
    enable=True  # True: 设置为管理员，False: 取消管理员
)
```

### 4. 用户管理 API

#### 处理好友请求
```python
await bot.send_action(
    action_type="handle_friend_request",
    request_id="req_123456",
    approve=True,  # True: 同意，False: 拒绝
    remark="好友备注"  # 可选：设置好友备注
)
```

#### 删除好友
```python
await bot.send_action(
    action_type="delete_friend",
    target=user
)
```

## OneBot V11 兼容 API

Coral 支持 OneBot V11 标准 API，可以通过适配器直接调用：

### 标准 API 列表

| API 名称 | 描述 | 状态 |
|---------|------|------|
| `send_private_msg` | 发送私聊消息 | ✅ 已实现 |
| `send_group_msg` | 发送群消息 | ✅ 已实现 |
| `send_msg` | 发送消息 | ✅ 已实现 |
| `delete_msg` | 撤回消息 | ✅ 已实现 |
| `get_msg` | 获取消息 | ⚠️ 部分实现 |
| `get_forward_msg` | 获取合并转发消息 | ❌ 未实现 |
| `send_like` | 发送好友赞 | ❌ 未实现 |
| `set_group_kick` | 群组踢人 | ✅ 已实现 |
| `set_group_ban` | 群组禁言 | ✅ 已实现 |
| `set_group_anonymous_ban` | 设置匿名禁言 | ❌ 未实现 |
| `set_group_whole_ban` | 群组全员禁言 | ⚠️ 部分实现 |
| `set_group_admin` | 设置群管理员 | ✅ 已实现 |
| `set_group_anonymous` | 设置群匿名 | ❌ 未实现 |
| `set_group_card` | 设置群名片 | ⚠️ 部分实现 |
| `set_group_name` | 设置群名 | ⚠️ 部分实现 |
| `set_group_leave` | 退出群组 | ✅ 已实现 |
| `set_group_special_title` | 设置群组专属头衔 | ❌ 未实现 |
| `set_friend_add_request` | 处理加好友请求 | ✅ 已实现 |
| `set_group_add_request` | 处理加群请求 | ✅ 已实现 |
| `get_login_info` | 获取登录号信息 | ✅ 已实现 |
| `get_stranger_info` | 获取陌生人信息 | ⚠️ 部分实现 |
| `get_friend_list` | 获取好友列表 | ⚠️ 部分实现 |
| `get_group_info` | 获取群信息 | ✅ 已实现 |
| `get_group_list` | 获取群列表 | ✅ 已实现 |
| `get_group_member_info` | 获取群成员信息 | ✅ 已实现 |
| `get_group_member_list` | 获取群成员列表 | ✅ 已实现 |
| `get_group_honor_info` | 获取群荣誉信息 | ❌ 未实现 |
| `get_cookies` | 获取 Cookies | ❌ 未实现 |
| `get_csrf_token` | 获取 CSRF Token | ❌ 未实现 |
| `get_credentials` | 获取 Credentials | ❌ 未实现 |
| `get_record` | 获取语音 | ❌ 未实现 |
| `get_image` | 获取图片 | ⚠️ 部分实现 |
| `can_send_image` | 检查是否可以发送图片 | ✅ 已实现 |
| `can_send_record` | 检查是否可以发送语音 | ❌ 未实现 |
| `get_status` | 获取运行状态 | ✅ 已实现 |
| `get_version_info` | 获取版本信息 | ✅ 已实现 |
| `set_restart` | 重启 OneBot 实现 | ❌ 未实现 |
| `clean_cache` | 清理缓存 | ❌ 未实现 |

**状态说明**：
- ✅ 已实现：功能完整可用
- ⚠️ 部分实现：基本功能可用，但可能有限制
- ❌ 未实现：尚未实现

## 使用示例

### 通过适配器调用 API

```python
from Coral import adapter_manager

# 获取适配器
adapter = adapter_manager.get_adapter("onebotv11")

# 调用 API
result = await adapter.call_api(
    "send_private_msg",
    user_id="987654321",
    message="Hello from API!"
)

# 处理结果
if result.get("status") == "ok":
    print(f"消息发送成功，消息ID：{result.get('data', {}).get('message_id')}")
else:
    print(f"消息发送失败：{result.get('message')}")
```

### 批量消息发送

```python
import asyncio

async def broadcast_message(bot, message, group_ids):
    """向多个群组广播消息"""
    tasks = []
    for group_id in group_ids:
        task = bot.send_message(
            message=message,
            group_id=group_id
        )
        tasks.append(task)
    
    # 并发发送
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # 处理结果
    success_count = 0
    for i, result in enumerate(results):
        if isinstance(result, Exception):
            print(f"群组 {group_ids[i]} 发送失败：{result}")
        else:
            success_count += 1
    
    return success_count, len(group_ids)
```

### 错误处理

```python
async def safe_api_call(bot, api_name, **kwargs):
    """安全的 API 调用"""
    try:
        result = await bot.send_action(api_name, **kwargs)
        
        if result.get("success", False):
            return result.get("data")
        else:
            error_msg = result.get("message", "未知错误")
            print(f"API 调用失败：{error_msg}")
            return None
            
    except Exception as e:
        print(f"API 调用异常：{e}")
        return None

# 使用安全调用
user_info = await safe_api_call(
    bot,
    "get_group_member_info",
    group_id="1000001",
    user_id="987654321"
)
```

## API 响应格式

### 成功响应
```json
{
    "status": "ok",
    "retcode": 0,
    "data": {
        "message_id": 123456789
    },
    "message": ""
}
```

### 错误响应
```json
{
    "status": "failed",
    "retcode": 100,
    "data": null,
    "message": "参数错误：user_id 不能为空"
}
```

### 响应字段说明

| 字段名 | 类型 | 说明 |
|--------|------|------|
| `status` | string | 状态，"ok" 或 "failed" |
| `retcode` | int | 返回码，0 表示成功 |
| `data` | any | 返回数据，具体内容因 API 而异 |
| `message` | string | 错误信息，成功时为空字符串 |

## 返回码说明

| 返回码 | 说明 |
|--------|------|
| 0 | 成功 |
| 1 | 异步处理已开始 |
| 100 | 参数错误 |
| 102 | 权限不足 |
| 103 | 操作失败 |
| 104 | 消息发送失败 |
| 201 | 工作线程池已满 |
| 202 | 操作超时 |

## 最佳实践

### 1. 错误处理
```python
async def robust_api_call(api_func, *args, **kwargs):
    """健壮的 API 调用"""
    max_retries = 3
    for attempt in range(max_retries):
        try:
            return await api_func(*args, **kwargs)
        except Exception as e:
            if attempt == max_retries - 1:
                raise
            await asyncio.sleep(1)  # 等待后重试
```

### 2. 速率限制
```python
import asyncio
from datetime import datetime

class RateLimitedAPI:
    """带速率限制的 API 调用器"""
    def __init__(self, calls_per_second=5):
        self.calls_per_second = calls_per_second
        self.last_call_time = 0
        self.lock = asyncio.Lock()
    
    async def call(self, api_func, *args, **kwargs):
        async with self.lock:
            now = time.time()
            elapsed = now - self.last_call_time
            min_interval = 1.0 / self.calls_per_second
            
            if elapsed < min_interval:
                await asyncio.sleep(min_interval - elapsed)
            
            self.last_call_time = time.time()
            return await api_func(*args, **kwargs)
```

### 3. 批量操作优化
```python
async def batch_operation(items, operation_func, batch_size=10):
    """批量操作优化"""
    results = []
    for i in range(0, len(items), batch_size):
        batch = items[i:i + batch_size]
        
        # 并发执行批次操作
        batch_tasks = [
            operation_func(item) for item in batch
        ]
        batch_results = await asyncio.gather(
            *batch_tasks, 
            return_exceptions=True
        )
        
        results.extend(batch_results)
        
        # 批次间延迟，避免触发速率限制
        if i + batch_size < len(items):
            await asyncio.sleep(0.5)
    
    return results
```

## 平台差异说明

不同平台的 API 支持程度可能有所不同：

### QQ 平台（OneBot V11）
- ✅ 支持最完整的 API 集合
- ✅ 消息发送和群管理功能完善
- ⚠️ 部分高级功能可能受限

### Console 平台
- ✅ 基础消息发送
- ❌ 无群组管理功能
- ❌ 无用户管理功能

### 其他平台
- ⚠️ 支持程度因平台而异
- 🔧 可能需要自定义适配器实现

## 调试技巧

### 1. API 调用日志
```python
import logging

# 启用 API 调试日志
logging.basicConfig(level=logging.DEBUG)

# 在适配器中添加日志
class LoggingAdapter:
    async def call_api(self, api_name, **kwargs):
        logging.debug(f"调用 API: {api_name}, 参数: {kwargs}")
        result = await self._real_call_api(api_name, **kwargs)
        logging.debug(f"API 响应: {result}")
        return result
```

### 2. 性能监控
```python
import time

async def timed_api_call(api_func, *args, **kwargs):
    """带计时器的 API 调用"""
    start_time = time.time()
    result = await api_func(*args, **kwargs)
    elapsed = time.time() - start_time
    
    if elapsed > 1.0:  # 超过1秒警告
        logging.warning(f"API 调用耗时过长: {elapsed:.2f}秒")
    
    return result
```

## 相关资源

- [OneBot V11 标准](https://github.com/botuniverse/onebot-11) - OneBot V11 协议规范
- [适配器开发指南](AdapterDev.md) - 开发自定义适配器
- [协议文档](Protocol.md) - Coral 协议规范

---

**最后更新：2026-01-31**  
**文档版本：v1.1.0**  
**API 状态：开发中**

