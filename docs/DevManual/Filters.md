# 过滤器系统（Filters）指南

过滤器系统是 Coral 框架提供的强大消息过滤工具，可以简化插件开发，让开发者能够轻松定义复杂的消息处理条件。

## 基本使用

### 导入过滤器

```python
from Coral import filters
# 或者导入特定过滤器
from Coral.filters import contains, from_user, and_, or_
```

### 在插件中使用过滤器

```python
from Coral import on_message
from Coral.filters import contains

# 使用过滤器装饰器
@on_message(
    name="关键词回复",
    filters=contains("你好")
)
async def greet_handler(event):
    return "你好！有什么可以帮您？"
```

## 内容过滤器

### 1. 包含关键词（contains）

```python
# 单个关键词
filters.contains("你好")

# 多个关键词（满足任意一个即可）
filters.contains(["你好", "hello", "hi"])

# 区分大小写
filters.contains("Hello", case_sensitive=True)
```

### 2. 以指定前缀开头（starts_with）

```python
# 检查消息是否以指定前缀开头
filters.starts_with("命令")

# 区分大小写
filters.starts_with("Command", case_sensitive=True)
```

### 3. 以指定后缀结尾（ends_with）

```python
# 检查消息是否以指定后缀结尾
filters.ends_with("吗？")

# 区分大小写
filters.ends_with("?", case_sensitive=True)
```

### 4. 正则表达式匹配（regex）

```python
# 使用正则表达式匹配
filters.regex(r"^查询\s+(\w+)$")

# 带标志的正则表达式
import re
filters.regex(r"^test.*$", flags=re.IGNORECASE)
```

### 5. 完全相等（equal）

```python
# 消息完全匹配
filters.equal("ping")

# 不区分大小写
filters.equal("PING", case_sensitive=False)
```

## 用户和群组过滤器

### 1. 来自指定用户（from_user）

```python
# 单个用户
filters.from_user(123456789)

# 多个用户
filters.from_user([123456789, 987654321])

# 字符串用户ID
filters.from_user("admin_user")
```

### 2. 在指定群组中（in_group）

```python
# 单个群组
filters.in_group(1000001)

# 多个群组
filters.in_group([1000001, 1000002, 1000003])
```

### 3. 私聊消息（is_private）

```python
# 只处理私聊消息
filters.is_private()
```

### 4. 群聊消息（is_group）

```python
# 只处理群聊消息
filters.is_group()
```

## 权限过滤器

### 权限检查（has_permission）

```python
# 检查单个权限
filters.has_permission("chat.allow")

# 检查多个权限（满足任意一个即可）
filters.has_permission(["admin.access", "moderator.access"])

# 在插件中使用
@on_message(
    name="管理员功能",
    filters=filters.has_permission("admin.command")
)
async def admin_function(event):
    return "管理员功能已执行"
```

## 速率限制过滤器

### 速率限制（rate_limit）

```python
# 每分钟最多5次请求
filters.rate_limit(5, 60)

# 每10秒最多1次请求
filters.rate_limit(1, 10)

# 自定义限制键（默认按用户ID）
def custom_key(event):
    return f"{event.platform}_{event.user.user_id}"

filters.rate_limit(10, 60, key_func=custom_key)
```

## 消息类型过滤器

### 消息类型过滤（message_type）

```python
# 只处理图片消息
filters.message_type("image")

# 只处理@消息
filters.message_type("at")

# 只处理文件消息
filters.message_type("file")
```

## AT相关过滤器

### 1. 检查是否包含任何@（has_at）

```python
# 检查消息是否包含任何@
filters.has_at()

# 示例：只处理包含@的消息
@on_message(
    name="AT消息处理器",
    filters=filters.has_at()
)
async def at_handler(event):
    return "检测到@消息"
```

### 2. 检查是否@了机器人自己（to_me）

```python
# 检查消息是否@了机器人自己
filters.to_me()

# 示例：只处理@机器人的消息
@on_message(
    name="机器人AT处理器",
    filters=filters.to_me()
)
async def at_me_handler(event):
    return "你@了我！"
```

### 3. 检查是否@了指定用户（to_someone）

```python
# 检查是否@了指定用户
filters.to_someone(123456789)  # 单个用户
filters.to_someone([123456789, 987654321])  # 多个用户

# 示例：检查是否@了管理员
admin_users = [123456789, 987654321]
@on_message(
    name="管理员AT处理器",
    filters=filters.to_someone(admin_users)
)
async def admin_at_handler(event):
    return "检测到@管理员的消息"
```

### 4. AT过滤器的组合使用

```python
# 组合使用：@了机器人自己或指定用户
combined_at_filter = filters.or_(
    filters.to_me(),
    filters.to_someone([123456789, 987654321])
)

# 组合使用：包含@并且是群聊消息
group_at_filter = filters.and_(
    filters.has_at(),
    filters.is_group()
)

# 组合使用：@了机器人自己并且包含特定关键词
smart_at_filter = filters.and_(
    filters.to_me(),
    filters.contains("帮助")
)

@on_message(
    name="智能AT处理器",
    filters=smart_at_filter
)
async def smart_at_handler(event):
    return "你@了我并请求帮助！"
```

### 5. AT过滤器的实际应用

```python
# 实际应用：权限检查+AT过滤
def create_admin_at_filter(admin_users):
    """创建管理员AT过滤器"""
    return filters.and_(
        filters.has_at(),  # 必须包含@
        filters.or_(
            filters.to_me(),  # @机器人自己
            filters.to_someone(admin_users)  # 或@管理员
        ),
        filters.has_permission("admin.notify")  # 需要通知权限
    )

# 使用示例
admin_users = [123456789, 987654321]
admin_at_filter = create_admin_at_filter(admin_users)

@on_message(
    name="管理员通知",
    filters=admin_at_filter
)
async def admin_notify_handler(event):
    # 查找被@的用户
    for segment in event.message.segments:
        if segment.type == "at":
            user_id = segment.data.get("user_id")
            return f"检测到@用户 {user_id} 的通知"
    return "AT通知处理完成"
```

## 自定义过滤器

### 自定义过滤函数（custom）

```python
# 自定义过滤逻辑
def custom_filter(event):
    # 检查消息长度
    if len(event.message.to_plain_text()) > 100:
        return True
    # 检查发送时间
    import datetime
    hour = datetime.datetime.now().hour
    return 9 <= hour <= 18  # 只在工作时间处理

filters.custom(custom_filter)

# 使用lambda表达式
filters.custom(lambda event: "重要" in event.message.to_plain_text())
```

## 组合过滤器

### 逻辑与组合（and_）

```python
# 多个条件必须同时满足
filters.and_(
    filters.contains("报告"),
    filters.in_group([1000001]),
    filters.has_permission("report.submit")
)

# 使用操作符
filter1 = filters.contains("天气")
filter2 = filters.in_group([1000001])
combined = filter1 & filter2
```

### 逻辑或组合（or_）

```python
# 满足任意一个条件即可
filters.or_(
    filters.contains("帮助"),
    filters.contains("help"),
    filters.contains("使用方法")
)

# 使用操作符
filter1 = filters.contains("早上好")
filter2 = filters.contains("早安")
combined = filter1 | filter2
```

### 逻辑非组合（not_）

```python
# 排除特定条件
filters.not_(filters.from_user([123456789]))

# 使用操作符
admin_filter = filters.from_user([123456789])
non_admin_filter = ~admin_filter
```

## 高级用法

### 复杂条件组合

```python
# 复杂条件：在指定群组中，来自管理员或包含"紧急"关键词
complex_filter = filters.and_(
    filters.in_group([1000001, 1000002]),
    filters.or_(
        filters.from_user([123456789, 987654321]),  # 管理员
        filters.contains("紧急")  # 紧急消息
    ),
    filters.has_permission("group.access")  # 需要群组访问权限
)

@on_message(
    name="复杂条件处理器",
    filters=complex_filter
)
async def complex_handler(event):
    return "复杂条件匹配成功"
```

### 过滤器复用

```python
# 定义可复用的过滤器
admin_users = [123456789, 987654321]
important_groups = [1000001, 1000002]

# 管理员过滤器
admin_filter = filters.from_user(admin_users)

# 重要群组过滤器
group_filter = filters.in_group(important_groups)

# 紧急消息过滤器
urgent_filter = filters.contains("紧急")

# 组合使用
@on_message(
    name="管理员紧急消息",
    filters=admin_filter & group_filter & urgent_filter
)
async def admin_urgent_handler(event):
    return "处理管理员紧急消息"
```

### 动态过滤器

```python
# 根据配置动态创建过滤器
def create_dynamic_filter(config):
    filters_list = []
    
    if config.get("require_auth", False):
        filters_list.append(filters.has_permission("chat.allow"))
    
    if config.get("allowed_groups"):
        filters_list.append(filters.in_group(config["allowed_groups"]))
    
    if config.get("keywords"):
        filters_list.append(filters.contains(config["keywords"]))
    
    # 组合所有条件
    return filters.and_(*filters_list)

# 使用动态过滤器
config = {
    "require_auth": True,
    "allowed_groups": [1000001, 1000002],
    "keywords": ["报告", "提交"]
}

dynamic_filter = create_dynamic_filter(config)

@on_message(
    name="动态过滤示例",
    filters=dynamic_filter
)
async def dynamic_handler(event):
    return "动态过滤器匹配成功"
```

## 在事件总线中使用过滤器

过滤器也可以直接在事件总线中使用：

```python
from Coral import event_bus
from Coral.protocol import MessageEvent

# 使用过滤器包装事件处理器
@event_bus.subscribe(MessageEvent)
async def filtered_handler(event: MessageEvent):
    # 手动应用过滤器
    filter_condition = filters.and_(
        filters.contains("查询"),
        filters.has_permission("query.allow")
    )
    
    if await filter_condition.check(event):
        return "执行查询操作"
    
    return None  # 不匹配，不处理
```

## 性能优化

### 1. 过滤器缓存

```python
from functools import lru_cache

# 缓存常用过滤器
@lru_cache(maxsize=10)
def get_cached_filter(keyword: str):
    return filters.contains(keyword)

# 使用缓存的过滤器
@on_message(
    name="缓存过滤器示例",
    filters=get_cached_filter("帮助")
)
async def cached_handler(event):
    return "使用缓存的过滤器"
```

### 2. 避免复杂过滤器的重复计算

```python
# 预计算复杂过滤器
complex_filter = filters.and_(
    filters.contains("天气"),
    filters.or_(
        filters.in_group([1000001]),
        filters.from_user([123456789])
    )
)

# 在多个处理器中复用
@on_message(
    name="天气查询1",
    filters=complex_filter
)
async def weather_handler1(event):
    return "天气查询结果1"

@on_message(
    name="天气查询2", 
    filters=complex_filter
)
async def weather_handler2(event):
    return "天气查询结果2"
```

### 3. 使用最有效的过滤器顺序

```python
# 将最可能失败的过滤器放在前面
efficient_filter = filters.and_(
    filters.has_permission("chat.allow"),  # 权限检查通常很快
    filters.in_group([1000001]),           # 群组检查
    filters.contains("复杂关键词")          # 内容匹配可能较慢
)
```

## 其他示例

### 1. 过滤器调试

```python
# 打印过滤器结构
filter_condition = filters.and_(
    filters.contains("测试"),
    filters.in_group([1000001])
)
print(f"过滤器结构：{filter_condition}")

# 测试过滤器
test_event = MessageEvent(...)
result = await filter_condition.check(test_event)
print(f"过滤结果：{result}")
```

### 2. 性能监控

```python
import time

async def benchmark_filter(filter_condition, event):
    start_time = time.time()
    result = await filter_condition.check(event)
    elapsed = time.time() - start_time
    
    print(f"过滤器检查耗时：{elapsed:.4f}秒")
    print(f"检查结果：{result}")
    
    return result
```

### 3. 过滤器日志

```python
import logging

# 创建带日志的过滤器
class LoggingFilter(filters.MessageFilter):
    def __init__(self, base_filter, name="未命名过滤器"):
        self.base_filter = base_filter
        self.name = name
        self.logger = logging.getLogger(__name__)
    
    async def check(self, event):
        self.logger.debug(f"检查过滤器：{self.name}")
        result = await self.base_filter.check(event)
        self.logger.debug(f"过滤器 {self.name} 结果：{result}")
        return result

# 包装现有过滤器
logged_filter = LoggingFilter(
    filters.contains("重要"),
    name="重要消息过滤器"
)
```

## 过滤器兼容性说明

Coral 的过滤器系统支持类型检查。当过滤器被用于不支持的事件类型时，<s>你为什么要这么做</s>系统会发出警告但默认返回 `True`。

```python
from Coral.protocol import CommandEvent

# 在CommandEvent上使用MessageFilter（会发出警告）
@on_command(
    name="测试命令",
    description="测试命令",
    filters=filters.contains("测试")  # 会发出警告，但会正常工作
)
async def test_command(event: CommandEvent):
    return "命令执行成功"
```

### 3. 过滤器类型支持

| 过滤器类型 | 支持的事件类型 | 说明 |
|-----------|--------------|------|
| MessageFilter | MessageEvent | 专为消息事件设计 |
| EventFilter | 所有事件类型 | 通用过滤器基类 |
| CompositeFilter | 取决于子过滤器 | 复合过滤器支持子过滤器的交集 |

## 相关资源

- [事件总线指南](EventBus.md) - 了解事件处理机制
- [插件开发指南](../PluginDev.md) - 学习插件开发
- [权限系统指南](PermSystem.md) - 了解权限管理

---

**最后更新：2026-02-02**  
**文档版本：v1.1.0**  
