# Coral - User Manual

这里是 Coral 用户手册。本文面向对开发并不熟悉，但希望使用 Coral 进行开发的用户。如果你要开发 Coral 插件，请参阅 [开发文档](DevManual.md)。

## 启动

想要部署并使用 Coral 机器人框架，只需要下载最新版的 Coral 代码。安装所需依赖并启动服务。详情请参阅 [快速部署](QuickStart.md)。

## 配置

在部署完成后第一次启动 Coral 机器人框架，会生成默认配置文件。

配置文件生成在 `config.json` 中，可以自行修改。

严格来说， `config.json` 的内容不固定，它存储的是调用 `config` 类生成的公共配置对象。 

## 插件

Coral 项目支持插件机制，可以方便地扩展功能。

插件目录为 `plugins`。

关于编写插件，请参考[插件开发文档](PluginDev.md)。
