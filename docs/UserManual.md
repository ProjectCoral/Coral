# Coral - User Manual

这里是 Coral 用户手册。本文面向对开发并不熟悉，但希望使用 Coral 进行开发的用户。如果你要开发 Coral 插件，请参阅 [开发文档](DevManual.md)。

如果有问题，请在 [GitHub issues](https://github.com/ProjectCoral/Coral/issues) 中反馈。

## 目录结构

    ```
    Coral
    ├── config.json
    ├── plugins
    │   ├── plugin1
    │   │   ├── plugin.py
    │   │   └── ...
    │   ├── plugin2
    │   │   ├── plugin.py
    │   │   └── ...
    │   └──...
    ├── logs
    ├── data
    ├── config
    ├──...
    └── main.py
    ```

- `config.json`：配置文件，包含框架的全局配置信息。
- `plugins`：插件目录，包含所有需加载的插件。
- `data`：数据目录，包含插件运行数据。
- `config`：配置目录，包含插件运行配置。
- `main.py`：启动文件。

## 启动

想要部署并使用 Coral 机器人框架，只需要下载最新版的 Coral 代码。安装所需依赖并启动服务。详情请参阅 [快速部署](QuickStart.md)。

## 配置

在部署完成后第一次启动 Coral 机器人框架，会生成默认配置文件。

配置文件生成在 `config.json` 中，可以自行修改。

严格来说， `config.json` 的内容不固定，它存储的是调用 `config` 类生成的公共配置对象。 

## 控制台

启动完成后， Coral 将会启动控制台，你可以通过控制台执行各类命令。

目前 Coral 内置的控制台命令有：
- `help`：查看帮助信息
- `status`：查看机器人状态
- `plugins`：查看已加载的插件
- `perms`：权限管理(详情请参阅 [权限系统用户文档](https://github.com/ProjectCoral/Coral/blob/main/docs/UserManual/PermSystem.md))


## 插件

功能不够完善？想添加更多功能？可以试试插件。

Coral 项目支持插件机制，可以方便地扩展功能。

插件目录为 `./plugins`，插件名称会自动取自插件目录名。

> Coral 官方为 [Muice-Chatbot](https://github.com/Moemu/Muice-Chatbot) 重构的插件：[Muice-Chatbot-Plugin](https://github.com/ProjectCoral/Muice_Chatbot_Plugin)。

有关更多插件，请访问 [Coral 插件库](https://github.com/ProjectCoral/Coral_Plugins)。

关于编写插件，请参考[插件开发文档](PluginDev.md)。
