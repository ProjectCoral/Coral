# PluginManager 插件管理器文档

## 概述

Coral PluginManager 是一个功能强大的插件管理系统，支持依赖感知的并发加载、完整的插件生命周期管理、权限集成和性能监控。本文档详细介绍 PluginManager 的功能和使用方法。

## 版本信息

```python
from Coral.plugin_manager import __version__, __meta__

print(f"PluginManager 版本: {__version__}")
print(f"PluginManager 元数据版本: {__meta__}")
```

当前版本：`260207_early_development`
兼容性版本：`250606`

## 核心功能

### 1. 依赖感知并发加载
- 自动解析插件依赖关系
- 拓扑排序确保依赖顺序
- 同一依赖层的插件并发加载
- 循环依赖检测

### 2. 完整的插件生命周期管理
- 加载/卸载插件
- 启用/禁用插件
- 重新加载插件
- 插件状态跟踪

### 3. 权限系统集成
- 插件管理命令权限控制
- 细粒度的权限分配
- 权限检查与验证

### 4. 性能监控与统计
- 插件加载时间统计
- 调用次数和错误统计
- 性能指标收集
- 实时状态监控

## 插件管理器初始化

### 基本初始化
```python
from Coral.plugin_manager import PluginManager
from Coral import register, config, perm_system

# 初始化插件管理器
plugin_manager = PluginManager(
    register=register,
    config=config,
    perm_system=perm_system,
    plugin_dir="./plugins"  # 插件目录，默认为 "./plugins"
)

# 加载所有插件
success, message = await plugin_manager.load_all_plugins()
print(f"加载结果: {success}, 消息: {message}")
```

### 配置选项
```python
# 通过配置设置插件目录
config.set("plugin_dir", "./custom_plugins")

# 设置最大并发加载数（默认为5）
config.set("plugin_manager.max_concurrent_loads", 10)

# 启用/禁用自动依赖安装
config.set("plugin_manager.auto_install_deps", True)
```

## 插件管理命令

PluginManager 提供了一套完整的插件管理命令，可以通过 `plugin` 命令使用：

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

### 命令详细说明

#### 1. 加载插件
```bash
# 加载单个插件
plugin load example_plugin

# 加载所有插件（框架启动时自动调用）
plugin reload all
```

#### 2. 卸载插件
```bash
# 卸载单个插件
plugin unload example_plugin

# 注意：如果其他插件依赖此插件，则无法卸载
```

#### 3. 启用/禁用插件
```bash
# 禁用插件（重命名为 plugin_name.disabled）
plugin disable example_plugin

# 启用插件（移除 .disabled 后缀）
plugin enable example_plugin
```

#### 4. 列出插件
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

#### 5. 查看统计信息
```bash
# 查看所有插件的总体统计
plugin stats

# 查看特定插件的统计
plugin stats example_plugin
```

#### 6. 查看插件信息
```bash
# 查看插件详细信息
plugin info example_plugin
```

#### 7. 重新加载插件
```bash
# 重新加载单个插件
plugin reload example_plugin

# 重新加载所有插件
plugin reload all
```

## 插件元数据规范

### 必需元数据
```python
__plugin_meta__ = {
    "name": "插件名称",          # 插件名称（建议与目录名一致）
    "version": "1.0.0",         # 插件版本
    "author": "开发者名称",      # 作者
    "description": "插件功能描述", # 描述
    "compatibility": "250606"   # 兼容的PluginManager版本
}
```

### 可选元数据
```python
__plugin_meta__ = {
    # ... 必需元数据 ...
    
    # 依赖声明
    "dependencies": ["other_plugin"],  # 依赖的其他插件
    "requirements": ["requests>=2.25.0"],  # Python包依赖
    
    # 权限声明
    "permissions": {
        "example.command": "示例命令权限",
        "example.admin": "管理员权限"
    },
    
    # 配置声明
    "config": {
        "enabled": True,
        "max_retries": 3
    }
}
```

### 完整示例
```python
__plugin_meta__ = {
    "name": "天气查询插件",
    "version": "2.0.0",
    "author": "Coral开发者",
    "description": "查询城市天气信息的插件",
    "compatibility": "250606",
    
    # 依赖声明
    "dependencies": ["network_utils"],  # 依赖网络工具插件
    "requirements": ["requests>=2.25.0", "beautifulsoup4>=4.9.0"],
    
    # 权限声明
    "permissions": {
        "weather.query": "查询天气权限",
        "weather.admin": "天气管理权限"
    },
    
    # 配置默认值
    "config": {
        "enabled": True,
        "api_key": "",
        "cache_duration": 300,
        "default_city": "北京"
    }
}
```

## 插件开发指南

### 1. 插件目录结构
```
weather_plugin/                    # 插件目录（名称即插件名）
├── __init__.py                   # 插件主文件（必需）
├── README.md                     # 插件说明文档（可选）
├── requirements.txt              # 依赖声明文件（可选）
├── config.json                   # 配置文件（可选）
└── data/                         # 数据目录（可选）
    └── cache/                    # 缓存数据
```

### 2. 插件主文件示例
```python
"""
天气查询插件
"""

__plugin_meta__ = {
    "name": "天气查询插件",
    "version": "2.0.0",
    "author": "Coral开发者",
    "description": "查询城市天气信息",
    "compatibility": "250606",
    "dependencies": [],
    "requirements": []
}

from Coral import on_command, on_message, contains
from Coral.protocol import MessageChain
import asyncio

# 插件初始化函数（可选）
async def plugin_load():
    """插件加载时调用"""
    print("天气插件加载完成")
    return True

async def plugin_unload():
    """插件卸载时调用"""
    print("天气插件卸载完成")
    return True

# 注册命令
@on_command("weather", "查询天气")
async def weather_command(event):
    if not event.args:
        return event.reply("请指定城市，例如：天气 北京")
    
    city = event.args[0]
    # 模拟天气查询
    weather_info = await get_weather(city)
    
    return event.reply(
        MessageChain()
            .add_text(f"{city}天气：")
            .add_text(f"\n{weather_info}")
    )

# 注册消息处理器
@on_message(filters=contains("天气怎么样"))
async def weather_message(event):
    # 从消息中提取城市
    message = event.message.to_plain_text()
    city = extract_city(message) or "北京"
    
    weather_info = await get_weather(city)
    return event.reply(f"{city}的天气：{weather_info}")

# 辅助函数
async def get_weather(city: str) -> str:
    """获取天气信息（模拟）"""
    await asyncio.sleep(0.1)  # 模拟网络请求
    weather_data = {
        "北京": "☀️ 晴天 25°C 湿度 45%",
        "上海": "🌧️ 小雨 22°C 湿度 85%",
        "广州": "⛅ 多云 28°C 湿度 70%"
    }
    return weather_data.get(city, "未知城市")

def extract_city(message: str) -> str:
    """从消息中提取城市名"""
    # 简单的提取逻辑
    for city in ["北京", "上海", "广州", "深圳"]:
        if city in message:
            return city
    return None
```

## 依赖管理

### 1. 依赖声明
```python
__plugin_meta__ = {
    # ... 其他元数据 ...
    "dependencies": ["database", "cache"],  # 插件依赖
    "requirements": [                        # Python包依赖
        "sqlalchemy>=1.4.0",
        "redis>=3.5.0"
    ]
}
```

### 2. 依赖解析
PluginManager 会自动：
1. 解析插件依赖关系
2. 检查循环依赖
3. 按依赖顺序加载插件
4. 验证依赖是否满足

### 3. 依赖安装
如果插件有 `requirements.txt` 文件或 `requirements` 元数据，PluginManager 会：
1. 检查依赖是否已安装
2. 自动安装缺失的依赖（如果配置允许）
3. 记录安装结果

## 权限系统集成

### 1. 权限声明
```python
# 在插件元数据中声明权限
__plugin_meta__ = {
    # ... 其他元数据 ...
    "permissions": {
        "weather.query": "查询天气权限",
        "weather.admin": "天气管理权限",
        "weather.config": "配置天气插件权限"
    }
}
```

### 2. 权限检查
```python
from Coral.filters import has_permission

@on_command(
    "weather_admin",
    "天气管理命令",
    filters=has_permission("weather.admin")
)
async def weather_admin_command(event):
    return "管理员操作成功"
```

### 3. 插件管理命令权限
PluginManager 自动注册以下权限：
- `plugin` - 基础插件管理权限
- `plugin.load` - 加载插件权限
- `plugin.unload` - 卸载插件权限
- `plugin.enable` - 启用插件权限
- `plugin.disable` - 禁用插件权限
- `plugin.list` - 列出插件权限
- `plugin.stats` - 查看统计权限
- `plugin.info` - 查看信息权限
- `plugin.reload` - 重新加载权限

## 性能监控

### 1. 插件统计信息
```bash
# 查看插件统计
plugin stats example_plugin

# 输出示例：
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
```

### 2. 总体统计
```bash
# 查看总体统计
plugin stats

# 输出示例：
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

## 高级功能

### 1. 并发加载控制
```python
# 在初始化时设置最大并发数
plugin_manager = PluginManager(
    register=register,
    config=config,
    perm_system=perm_system,
    plugin_dir="./plugins"
)

# 或者通过配置设置
config.set("plugin_manager.max_concurrent_loads", 10)
```

### 2. 依赖图可视化
```python
# 获取插件依赖图（开发调试用）
from Coral.plugin_manager.metadata import PluginMetadata

metadata = PluginMetadata()
plugins_meta = {}  # 从 registry 获取插件元数据
dependency_graph = metadata.build_dependency_graph(plugins_meta)

# 检查循环依赖
if dependency_graph.has_cycle():
    print("警告：检测到循环依赖")

# 获取加载顺序
load_order = dependency_graph.topological_sort()
print(f"加载顺序: {load_order}")
```

### 3. 自定义加载策略
```python
# 继承 PluginManager 实现自定义逻辑
class CustomPluginManager(PluginManager):
    async def load_all_plugins(self) -> Tuple[bool, str]:
        # 自定义加载逻辑
        print("使用自定义加载策略")
        return await super().load_all_plugins()
    
    async def load_plugin(self, plugin_name: str) -> Tuple[bool, str]:
        # 自定义单个插件加载逻辑
        print(f"加载插件: {plugin_name}")
        return await super().load_plugin(plugin_name)
```

## 故障排除

### 常见问题

#### Q: 插件加载失败
**可能原因**：
1. 依赖不满足
2. 插件元数据错误
3. 兼容性版本不匹配
4. 插件代码错误

**解决方法**：
```bash
# 查看详细错误信息
plugin info <plugin_name>

# 检查依赖
plugin stats <plugin_name>
```

#### Q: 循环依赖错误
**解决方法**：
1. 检查插件依赖声明
2. 重构插件消除循环依赖
3. 使用延迟加载或接口解耦

#### Q: 权限不足
**解决方法**：
1. 检查用户权限
2. 联系管理员分配权限
3. 使用 `plugin list` 查看可用插件

#### Q: 插件无法卸载
**可能原因**：
1. 其他插件依赖此插件
2. 插件正在使用中
3. 权限不足

**解决方法**：
```bash
# 查看依赖关系
plugin info <plugin_name>

# 先卸载依赖此插件的其他插件
plugin unload <dependent_plugin>
plugin unload <plugin_name>
```

## 相关链接
- [插件开发指南](./PluginDev.md) - 插件开发详细指南
- [插件注册文档](./PluginReg.md) - 插件注册机制
- [协议文档](./Protocol.md) - Coral通信协议
- [权限系统](./PermSystem.md) - 权限系统使用指南
- [API文档](./api.md) - 完整API参考