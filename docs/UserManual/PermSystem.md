# 权限系统 - 用户手册

Coral 内置了权限系统，通过它你可以控制用户对命令和功能的访问权限。

## 权限管理命令

使用 `perms` 命令管理权限：

### 查看已注册权限

```Console
perms show
```

### 查看权限分配情况

```Console
perms list
```

### 添加权限

为用户在指定群组添加权限：

```Console
perms add <权限名> <用户ID> [群组ID]
```

- **权限名**：格式为 `root.name`，如 `core.admin`、`myplugin.use`
- **用户ID**：用户的唯一标识符
- **群组ID**：可选，指定群组。默认为 `-1` 表示全局权限

示例：
```
perms add core.admin 123456789 1000001    # 为用户123456789在群组1000001添加admin权限
perms add core.admin 123456789            # 为用户123456789添加全局admin权限
```

### 移除权限

从用户移除权限：

```Console
perms remove <权限名> <用户ID> [群组ID]
```

示例：
```
perms remove core.admin 123456789 1000001
```

### 授予全局权限

跨越所有群组生效的权限：

```Console
perms grant <权限名> <用户ID>
```

示例：
```
perms grant core.admin 123456789
```

### 撤销全局权限

```Console
perms revoke <权限名> <用户ID>
```

## 权限名称格式

权限名称使用 `root.name` 格式：

| 示例 | 说明 |
|------|------|
| `core.admin` | core模块的管理员权限 |
| `core.read` | core模块的读取权限 |
| `myplugin.use` | myplugin插件的使用权限 |

## 根权限

拥有根权限（如 `core.`）可以匹配所有子权限（如 `core.read`、`core.write`）。

当你为用户授予 `core.` 根权限后，该用户自动拥有所有 `core.*` 的权限。

## 群组权限 vs 用户权限

### 用户权限

用户权限可以细分为：
- **全局权限**：用户在任何群组都有效的权限（群组ID为 `-1` 或使用 `grant` 命令）
- **群组权限**：仅在特定群组有效的权限

### 群组权限

群组权限对该群组内所有用户生效，无需单独为每个用户设置。

## 特殊用户

### Console 用户

`Console` 用户拥有所有权限，可用于测试或开发目的。

### user_id 和 group_id

- **user_id**：用户的唯一标识符，由适配器提供
- **group_id**：群组的标识符，可为任意字符串。私聊时 `group_id` 为 `-1` 或 `None`

## 权限检查优先级

1. Console 用户拥有所有权限
2. 用户全局权限（匹配根权限或完全相同）
3. 用户在特定群组的权限
4. 群组权限（匹配根权限或完全相同）
5. 全局群组权限（`-1`）

## 相关资源

- [权限系统开发指南](../DevManual/PermSystem.md) - 开发者接入权限系统
- [过滤器系统指南](../DevManual/Filters.md) - 在插件中使用权限过滤器