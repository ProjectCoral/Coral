# 接入权限系统

Coral 内置了权限系统，支持基于 `Permission` 对象的权限控制。

关于权限系统的使用，请参阅 [权限系统用户文档](../UserManual/PermSystem.md)。

## 核心概念

### Permission 对象

权限由 `Permission(root, name, description)` 创建，格式为 `root.name`：

```python
from Coral.permission import Permission

# 创建权限
ADMIN = Permission("core", "admin")
READ = Permission("core", "read")

# 组合权限
can_manage = ADMIN | READ  # OR
can_read = ADMIN & ~READ   # AND NOT
```

### 权限检查

```python
from Coral import perm_system

# 检查权限（单个或列表）
perm_system.check_perm(Permission("core", "admin"), user_id, group_id)
perm_system.check_perm([perm1, perm2], user_id, group_id)  # OR逻辑
```

## 接入 Command

1. **注册权限**

```python
from Coral import perm_system
from Coral.permission import Permission

# 注册权限
perm_system.register_perm(Permission("myplugin", "use", "使用插件"))
perm_system.register_perm(Permission("myplugin", "admin", "管理插件"))
```

2. **绑定权限**

通过 `permission` 参数绑定：

```python
from Coral import on_command
from Coral.permission import Permission

MY_USE = Permission("myplugin", "use")

@on_command(
    name="mycmd",
    description="我的命令",
    permission=MY_USE,
)
async def mycmd_handler(event):
    return "命令执行成功"
```

通过过滤器绑定：

```python
from Coral import on_command
from Coral.filters import has_permission
from Coral.permission import Permission

MY_USE = Permission("myplugin", "use")

@on_command(
    name="mycmd",
    description="我的命令",
    filters=has_permission(MY_USE),
)
async def mycmd_handler(event):
    return "命令执行成功"
```

3. **权限列表（OR逻辑）**

```python
from Coral import on_command
from Coral.permission import Permission

@on_command(
    name="mycmd",
    description="我的命令",
    permission=[Permission("myplugin", "use"), Permission("myplugin", "admin")],
)
async def mycmd_handler(event):
    return "命令执行成功"
```

上述配置表示：拥有 `myplugin.use` 或 `myplugin.admin` 任一权限即可执行。

## 手动权限检查

在插件中进行权限检查：

```python
from Coral import perm_system
from Coral.permission import Permission

class MyPlugin:
    def __init__(self, register, perm_system):
        self.register = register
        self.perm = perm_system

    async def handle_event(self, event):
        user_id = event.user.user_id
        group_id = event.group.group_id if event.group else -1

        if not self.perm.check_perm(Permission("myplugin", "use"), user_id, group_id):
            return None  # 无权限

        # 处理逻辑
        return "处理成功"
```

## 根权限匹配

权限系统支持根权限匹配：拥有根权限（如 `myplugin.`）可以匹配所有子权限（如 `myplugin.read`、`myplugin.write`）。

```python
from Coral.permission import Permission
from Coral import perm_system

# 注册根权限
perm_system.register_perm(Permission("myplugin", "", "插件根权限"))
perm_system.register_perm(Permission("myplugin", "read", "读取"))
perm_system.register_perm(Permission("myplugin", "write", "写入"))

# 拥有根权限的用户可以匹配所有子权限
perm_system.grant_global_perm(Permission("myplugin", ""), user_id)
```

## 权限管理命令

用户可以使用内置命令管理权限：

```
perms show                          # 显示所有已注册权限
perms list                          # 列出用户和群组权限
perms add <权限名> <用户ID> [群组ID]  # 添加权限
perms remove <权限名> <用户ID> [群组ID] # 移除权限
perms grant <权限名> <用户ID>         # 授予全局权限
perms revoke <权限名> <用户ID>         # 撤销全局权限
```

权限名格式：`root.name`，如 `core.admin`、`myplugin.use`。

## Console 用户

`Console` 用户拥有所有权限，可用于代码中直接调用命令：

```python
from Coral import register
from Coral.protocol import CommandEvent, MessageChain, UserInfo, MessageSegment

register.execute_command(CommandEvent(
    event_id=f"console-{time.time()}",
    platform="console",
    self_id="Console",
    command="mycmd",
    raw_message=MessageChain([MessageSegment.text("mycmd")]),
    user=UserInfo(platform="system", user_id="Console"),
    args=[]
))
```

## 相关资源

- [权限系统用户文档](../UserManual/PermSystem.md) - 用户权限管理
- [过滤器系统指南](Filters.md) - 消息过滤
- [插件开发指南](../PluginDev.md) - 插件开发