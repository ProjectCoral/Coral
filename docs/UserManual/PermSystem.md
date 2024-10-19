# 权限系统 - 用户手册

Coral 内置了一套权限系统，通过它你可以控制用户运行 Coral 命令权限等功能。

## 命令

### add

`add` 命令用于添加用户到权限系统。

语法：

```Console
perms add <perm_name> <user_id> <group_id>
```

参数：
- `perm_name`：权限名称。
- `user_id`：用户 ID。
- `group_id`：用户所在组 ID。

### remove

`remove` 命令用于从权限系统中删除用户。

语法：

```Console
perms remove <perm_name> <user_id> <group_id>
```

参数：
- `perm_name`：权限名称。
- `user_id`：用户 ID。
- `group_id`：用户所在组 ID。

### show

`show` 命令用于显示所有已注册的权限。

语法：

```Console
perms show
```

### list

`list` 命令用于列出权限系统中的各用户拥有的权限。

语法：

```Console
perms list
```

## 参数

### user_id

一般来说，用户 ID 由适配器导入，是每个用户唯一的标识符。

也可设置为 `Console` 代表控制台用户。

### group_id

组 ID 用于标识用户所属的组，可以是任意字符串。

## 函数

### check_perm

`check_perm` 函数用于检查用户是否有权限运行指定的命令。

语法：

```python
permsystem.check_perm(perm_name : str or list, user_id : str, group_id : str) -> bool
```

参数：
- `perm_name`：权限名称，可以是字符串或列表。
- `user_id`：用户 ID。
- `group_id`：用户所在组 ID。

返回值：
- `True`：用户有权限运行指定的命令。
- `False`：用户没有权限运行指定的命令。

