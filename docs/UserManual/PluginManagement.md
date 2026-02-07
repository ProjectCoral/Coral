# 插件管理 - 用户手册

## 概述

Coral 提供了一个强大的插件管理系统，允许用户通过简单的命令管理插件的完整生命周期。本文档介绍如何使用插件管理命令。

## 插件管理命令

所有插件管理命令都以 `plugin` 开头，后面跟着子命令和参数。

### 命令概览

```
plugin load <plugin_name>      - 加载指定插件
plugin unload <plugin_name>    - 卸载指定插件
plugin enable <plugin_name>    - 启用已禁用的插件
plugin disable <plugin_name>   - 禁用插件（添加 .disabled 后缀）
plugin list [filter]           - 列出插件（all|loaded|enabled|disabled）
plugin stats [plugin_name]     - 显示插件统计信息
plugin info <plugin_name>      - 显示插件详细信息
plugin reload [plugin_name]    - 重新加载插件（单个或全部）
plugin help [command]          - 显示命令帮助
```

## 详细命令说明

### 1. 加载插件

加载指定的插件到系统中。

```bash
# 加载单个插件
plugin load example_plugin

# 示例输出：
# Plugin 'example_plugin' loaded successfully in 0.15s
```

**注意事项**：
- 插件必须存在于插件目录中
- 插件依赖必须满足
- 插件必须与当前版本兼容

### 2. 卸载插件

从系统中卸载指定的插件。

```bash
# 卸载单个插件
plugin unload example_plugin

# 示例输出：
# Plugin 'example_plugin' unloaded successfully
```

**注意事项**：
- 如果其他插件依赖此插件，则无法卸载
- 插件状态会被保存，可以重新加载

### 3. 启用插件

启用已被禁用的插件。

```bash
# 启用插件
plugin enable example_plugin

# 示例输出：
# Plugin 'example_plugin' enabled successfully
```

**工作原理**：
- 将插件目录从 `plugin_name.disabled` 重命名为 `plugin_name`
- 插件在下一次加载时可用

### 4. 禁用插件

禁用插件，使其无法加载。

```bash
# 禁用插件
plugin disable example_plugin

# 示例输出：
# Plugin 'example_plugin' disabled successfully
```

**工作原理**：
- 如果插件已加载，先卸载
- 将插件目录重命名为 `plugin_name.disabled`
- 插件在启用前无法加载

### 5. 列出插件

列出系统中的插件，支持多种过滤选项。

```bash
# 列出所有插件
plugin list all

# 列出已加载的插件
plugin list loaded

# 列出已启用的插件
plugin list enabled

# 列出已禁用的插件
plugin list disabled
```

**输出示例**：
```
All Plugins (8):
----------------------------------------
✓ example_plugin v1.0.0 - 示例插件
✓ weather_plugin v2.0.0 - 天气查询插件
✗ database_plugin v1.2.0 (disabled) - 数据库插件
✓ cache_plugin v1.1.0 - 缓存插件
----------------------------------------
Total: 8, Loaded: 5, Enabled: 7, Disabled: 1
```

**状态说明**：
- `✓` - 插件已加载
- `✗` - 插件未加载
- `(disabled)` - 插件被禁用

### 6. 查看统计信息

查看插件的性能统计信息。

```bash
# 查看所有插件的总体统计
plugin stats

# 查看特定插件的统计
plugin stats example_plugin
```

**总体统计输出示例**：
```
Overall Plugin Statistics
----------------------------------------
Plugin Manager Version: 260207_early_development
Plugin Directory: ./plugins

Plugin Counts:
  Total Plugins: 8
  Loaded: 5
  Enabled: 7
  Disabled: 1

Performance Metrics:
  Total Load Time: 1.25s
  Average Load Time: 0.25s
  Total Errors: 2
  Total Calls: 156
  Average Execution Time: 0.035s

Plugin Manager Status:
  Is Loading: No
  Compatibility Version: 250606
```

**插件统计输出示例**：
```
Statistics for plugin: example_plugin
----------------------------------------
Version: 1.0.0
Author: 开发者
State: LOADED
Load Status: SUCCESS

Performance Metrics:
  Load Time: 0.15s
  Load Count: 1
  Unload Count: 0
  Last Loaded: 2026-02-07 23:15:30
  Total Calls: 42
  Avg Execution Time: 0.023s
  Total Errors: 0
  Last Error: None

Dependencies:
  ✓ database_plugin
  ✗ cache_plugin

Description: 示例插件功能描述
```

### 7. 查看插件信息

查看插件的详细信息，包括元数据和依赖关系。

```bash
# 查看插件详细信息
plugin info example_plugin
```

**输出示例**：
```
Plugin Information: example_plugin
----------------------------------------
Name: example_plugin
Version: 1.0.0
Author: 开发者
Compatibility: 250606
State: LOADED
Disabled: No
Loaded: Yes
Can Load: Yes
Dependencies Met: Yes

Description:
  示例插件功能描述

Dependencies:
  ✓ database_plugin (exists: ✓)
  ✗ cache_plugin (exists: ✗)

Requirements:
  requests>=2.25.0
  beautifulsoup4>=4.9.0

Path: ./plugins/example_plugin
```

### 8. 重新加载插件

重新加载插件，适用于插件更新后的热重载。

```bash
# 重新加载单个插件
plugin reload example_plugin

# 重新加载所有插件
plugin reload all
```

**工作原理**：
1. 卸载插件（如果已加载）
2. 重新加载插件
3. 保持插件状态和配置

### 9. 获取帮助

获取插件管理命令的帮助信息。

```bash
# 获取所有命令的帮助
plugin help

# 获取特定命令的帮助
plugin help load
plugin help list
```

## 权限要求

插件管理命令需要相应的权限：

| 命令 | 所需权限 | 说明 |
|------|----------|------|
| `plugin load` | `plugin.load` | 加载插件权限 |
| `plugin unload` | `plugin.unload` | 卸载插件权限 |
| `plugin enable` | `plugin.enable` | 启用插件权限 |
| `plugin disable` | `plugin.disable` | 禁用插件权限 |
| `plugin list` | `plugin.list` | 列出插件权限 |
| `plugin stats` | `plugin.stats` | 查看统计权限 |
| `plugin info` | `plugin.info` | 查看信息权限 |
| `plugin reload` | `plugin.reload` | 重新加载权限 |

**基础权限**：所有插件管理命令都需要 `plugin` 基础权限。

## 使用示例

### 示例1：安装和管理天气插件

```bash
# 1. 列出所有可用插件
plugin list all

# 2. 加载天气插件
plugin load weather_plugin

# 3. 查看插件信息
plugin info weather_plugin

# 4. 测试插件功能
weather 北京

# 5. 查看插件性能
plugin stats weather_plugin

# 6. 更新插件后重新加载
plugin reload weather_plugin
```

### 示例2：故障排除

```bash
# 1. 插件加载失败，查看错误信息
plugin info problem_plugin

# 2. 检查依赖是否满足
plugin stats problem_plugin

# 3. 如果依赖缺失，加载依赖插件
plugin load missing_dependency

# 4. 重新加载问题插件
plugin reload problem_plugin

# 5. 如果问题依旧，禁用插件
plugin disable problem_plugin
```

### 示例3：批量操作

```bash
# 1. 禁用所有插件（维护模式）
plugin list loaded
# 逐个禁用已加载的插件
plugin disable plugin1
plugin disable plugin2
# ...

# 2. 启用所有插件
plugin list disabled
# 逐个启用被禁用的插件
plugin enable plugin1
plugin enable plugin2
# ...

# 3. 重新加载所有插件（系统更新后）
plugin reload all
```

## 常见问题

### Q: 插件加载失败怎么办？
**可能原因**：
1. 依赖不满足
2. 插件版本不兼容
3. 插件代码错误
4. 权限不足

**解决方法**：
```bash
# 查看详细错误信息
plugin info <plugin_name>

# 检查依赖
plugin stats <plugin_name>

# 检查权限
# 联系管理员分配 plugin.load 权限
```

## 相关命令

### 权限管理
```bash
# 查看权限系统帮助
perms help

# 为用户分配插件管理权限
perms add plugin <user_id> <group_id>
perms add plugin.load <user_id> <group_id>
```

### 系统状态
```bash
# 查看系统状态
system status

# 查看日志
logs show
```

## 获取帮助

如果遇到问题，可以通过以下方式获取帮助：

1. **命令帮助**：`plugin help` 或 `plugin help <command>`
2. **查看文档**：参考插件开发文档
3. **社区支持**：访问 Coral 社区论坛
4. **联系开发者**：通过 GitHub Issues 报告问题

> **提示**：更多插件相关信息，请参考 [插件开发指南](../PluginDev.md) 和 [PluginManager 文档](../DevManual/PluginManager.md)。