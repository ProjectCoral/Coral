# 过滤器系统（Filters）指南

过滤器系统是 Coral 框架提供的消息过滤工具，可以简化插件开发，让开发者能够轻松定义复杂的消息处理条件。

## 基本使用

### 导入

```python
from Coral import filters
from Coral.filters import contains, from_user, and_, or_, has_permission
```

### 在插件中使用

```python
from Coral import on_message
from Coral.filters import contains

@on_message(
    name="关键词回复",
    filters=contains("你好")
)
async def greet_handler(event):
    return "你好！有什么可以帮您？"
```

## 内容过滤器

### contains - 包含关键词

```python
# 单个关键词
filters.contains("你好")

# 多个关键词（满足任意一个即可）
filters.contains(["你好", "hello", "hi"])

# 区分大小写
filters.contains("Hello", case_sensitive=True)
```

### starts_with - 以指定前缀开头

```python
filters.starts_with("命令")
filters.starts_with("Command", case_sensitive=True)
```

### ends_with - 以指定后缀结尾

```python
filters.ends_with("吗？")
filters.ends_with("?", case_sensitive=True)
```

### regex - 正则表达式匹配

```python
import re
filters.regex(r"^查询\s+(\w+)$")
filters.regex(r"^test.*$", flags=re.IGNORECASE)
```

### equal - 完全相等

```python
filters.equal("ping")
filters.equal("PING", case_sensitive=False)
```

## 用户和群组过滤器

### from_user - 来自指定用户

```python
filters.from_user(123456789)              # 单个用户
filters.from_user([123456789, 987654321])  # 多个用户
filters.from_user("admin_user")           # 字符串ID
```

### in_group - 在指定群组中

```python
filters.in_group(1000001)                        # 单个群组
filters.in_group([1000001, 1000002, 1000003])   # 多个群组
```

### is_private - 私聊消息

```python
filters.is_private()
```

### is_group - 群聊消息

```python
filters.is_group()
```

## 权限过滤器

### has_permission - 权限检查

```python
from Coral.permission import Permission

# 检查单个权限
MY_USE = Permission("myplugin", "use")
filters.has_permission(MY_USE)

# 检查多个权限（满足任意一个即可）
filters.has_permission([Permission("admin", "access"), Permission("moderator", "access")])

# 在插件中使用
@on_message(
    name="管理员功能",
    filters=filters.has_permission(Permission("admin", "command"))
)
async def admin_function(event):
    return "管理员功能已执行"
```

## 速率限制过滤器

### rate_limit - 速率限制

```python
# 每分钟最多5次请求（按用户ID限制）
filters.rate_limit(5, 60)

# 每10秒最多1次请求
filters.rate_limit(1, 10)

# 自定义限制键
def custom_key(event):
    return f"{event.group.group_id}_{event.user.user_id}"

filters.rate_limit(10, 60, key_func=custom_key)
```

## 消息类型过滤器

### message_type - 指定消息类型

```python
filters.message_type("image")  # 图片
filters.message_type("at")     # @消息
filters.message_type("file")   # 文件
```

## AT相关过滤器

### has_at - 包含任何@

```python
filters.has_at()
```

### to_me - @了机器人自己

```python
filters.to_me()
```

### to_someone - @了指定用户

```python
filters.to_someone(123456789)              # 单个用户
filters.to_someone([123456789, 987654321])  # 多个用户
```

## 自定义过滤器

### custom - 自定义过滤函数

```python
def custom_filter(event):
    return len(event.message.to_plain_text()) > 100

filters.custom(custom_filter)
filters.custom(lambda event: "重要" in event.message.to_plain_text())
```

## 组合过滤器

### and_ - 逻辑与

```python
filters.and_(
    filters.contains("报告"),
    filters.in_group([1000001]),
    filters.has_permission(Permission("report", "submit"))
)

# 使用操作符
combined = filters.contains("天气") & filters.in_group([1000001])
```

### or_ - 逻辑或

```python
filters.or_(
    filters.contains("帮助"),
    filters.contains("help"),
    filters.contains("使用方法")
)

# 使用操作符
combined = filter1 | filter2
```

### not_ - 逻辑非

```python
filters.not_(filters.from_user([123456789]))

# 使用操作符
non_admin = ~filters.from_user([123456789])
```

## 工厂函数表

| 函数 | 说明 |
|------|------|
| `contains(keywords, case_sensitive)` | 包含关键词 |
| `starts_with(prefix, case_sensitive)` | 以指定前缀开头 |
| `ends_with(suffix, case_sensitive)` | 以指定后缀结尾 |
| `regex(pattern, flags)` | 正则表达式匹配 |
| `equal(text, case_sensitive)` | 完全相等 |
| `from_user(user_ids)` | 来自指定用户 |
| `in_group(group_ids)` | 在指定群组中 |
| `is_private()` | 私聊消息 |
| `is_group()` | 群聊消息 |
| `has_permission(permission)` | 权限检查 |
| `rate_limit(requests, period, key_func)` | 速率限制 |
| `message_type(msg_type)` | 消息类型 |
| `custom(func)` | 自定义函数 |
| `and_(*filters)` | 逻辑与 |
| `or_(*filters)` | 逻辑或 |
| `not_(filter)` | 逻辑非 |
| `to_someone(user_ids)` | @了指定用户 |
| `to_me()` | @了机器人自己 |
| `has_at()` | 包含任何@ |

## 高级用法

### 复杂条件组合

```python
complex_filter = filters.and_(
    filters.in_group([1000001, 1000002]),
    filters.or_(
        filters.from_user([123456789, 987654321]),
        filters.contains("紧急")
    ),
    filters.has_permission(Permission("group", "access"))
)

@on_message(name="复杂条件处理器", filters=complex_filter)
async def complex_handler(event):
    return "复杂条件匹配成功"
```

### 动态过滤器

```python
def create_filter(config):
    filter_list = []

    if config.get("require_auth"):
        filter_list.append(filters.has_permission(Permission("chat", "allow")))

    if config.get("allowed_groups"):
        filter_list.append(filters.in_group(config["allowed_groups"]))

    if config.get("keywords"):
        filter_list.append(filters.contains(config["keywords"]))

    return filters.and_(*filter_list) if filter_list else None
```

### 过滤器复用

```python
admin_users = [123456789, 987654321]
important_groups = [1000001, 1000002]

admin_filter = filters.from_user(admin_users)
group_filter = filters.in_group(important_groups)
urgent_filter = filters.contains("紧急")

@on_message(name="管理员紧急消息", filters=admin_filter & group_filter & urgent_filter)
async def admin_urgent_handler(event):
    return "处理管理员紧急消息"
```

## 过滤器类型说明

Coral 的过滤器支持类型检查。当过滤器被用于不支持的事件类型时，系统会发出警告但默认返回 `True`。

| 过滤器类型 | 支持的事件类型 |
|-----------|--------------|
| `MessageFilter` | MessageEvent |
| `EventFilter` | 所有事件类型 |
| `CompositeFilter` | 取决于子过滤器 |

## 相关资源

- [权限系统指南](PermSystem.md) - 了解权限管理
- [插件开发指南](../PluginDev.md) - 学习插件开发
- [事件总线指南](EventBus.md) - 了解事件处理机制