# 插件开发指南

目前， Coral 项目支持插件注册以下行为：

-  event 事件：当用户触发某些事件时，插件可以执行一些操作。
-  command 命令：当用户输入特定的命令时，插件可以执行一些操作。
-  fuction 函数：当代码调用特定的函数时，插件可以执行一些操作。

你也可以参考 [plugins](https://github.com/ProjectCoral/Coral/blob/main/plugins) 中的插件示例，了解插件开发的基本流程。

## 规范

1. 插件的目录结构：

    ```
    plugin-name
    ├── main.py  # 插件主文件
    ├── * README.md  # 插件说明文档(可选)
    ├── * requirements.txt  # 插件依赖(可选)
    └── ...  # 其他文件(可选)
    ```

    - 插件的主文件必须为 `main.py`，插件名称自动取自目录名称。

    - `requirements.txt` 用于声明插件依赖(可选)，若存在则会检查依赖是否满足并自动安装(我还是建议你搞个脚本，自动安装用的是 pip，网不好就抽风)。

2. 插件逻辑： 

    - 插件的主文件会在插件被注册时被调用，具体的注册方式请参考 [插件注册](DevManual/PluginReg.md)。

    - 返回的数据格式或是 API 请求数据请参考 [API 文档](DevManual/api.md)。

    - 当编写插件时你可以选择接入 Coral 内置的权限系统(详情请参考 [权限系统开发文档](DevManual/PermSystem.md))，也可以自己实现权限系统。

    - 我建议你将插件的 data 目录放在`./data/插件名`  目录下，这样可以方便管理插件数据。
  
    - 目前你可以引入以下模块：
        ```python
        from coral import register, config, perm_system
        ```

3. 插件配置：

    - 你可以选择使用 `config` 类注册全局配置，详情请参考 [调用全局配置](DevManual/UseConfig.md)。

    - 如果需要自行添加配置加载逻辑，请尽量把配置信息放在 `./config/插件名`  目录下，<s>不要到处乱拉</s>。