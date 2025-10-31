<div align="center">
    <div>
        <img src="./docs/coral.png" alt="logo" style="width: 20%; height: auto;">
    </div>
<h1>Project Coral</h1>

新一代（或许）跨平台、可扩展的 python 机器人框架

这个项目的灵感来源于<a href = "https://github.com/Moemu/Muice-Chatbot">沐雪(Muice-Chatbot)</a>

图标由画师<a href = "https://www.pixiv.net/users/20728711">WERI</a>绘制

![](https://shields.io/github/stars/ProjectCoral/Coral.svg)![](https://img.shields.io/github/forks/ProjectCoral/Coral.svg) ![](https://img.shields.io/github/tag/ProjectCoral/Coral.svg) ![](https://img.shields.io/github/release/ProjectCoral/Coral.svg) ![](https://img.shields.io/github/issues/ProjectCoral/Coral.svg)![](https://img.shields.io/badge/Python-3.10-blue)

</div>


## 声明

### 一切开发旨在学习，请勿用于非法用途。

### 许可证

本项目采用 `AGPL-3.0` 协议开源，详情请参阅 [LICENSE](https://github.com/ProjectCoral/Coral/blob/main/LICENSE) 文件。

    Copyright (C) 2024-2025 ProjectCoral and contributors.

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU Affero General Public License as
    published by the Free Software Foundation, either version 3 of the
    License, or (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU Affero General Public License for more details.

    You should have received a copy of the GNU Affero General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.

### 注意事项

- `AGPL-3.0` 协议属于传染性协议，因此建议直接/间接接触 Coral 项目的软件使用 `AGPL-3.0` 开源

- 本项目不建议用于商业用途。

### 衍生软件需声明引用

- 若引用 Coral 发布的软件包而不修改 Coral 源码，请在软件包的 `README` 中声明 Coral 项目的链接。

- 若修改 Coral 源代码再发布，**或参考 Coral 内部实现发布另一个项目**，则衍生项目必须在**文章首部**或 Coral 相关内容**首次出现**的位置**明确声明**来源于[本仓库](https://github.com/ProjectCoral/Coral)。不得扭曲或隐藏免费且开源的事实。

## 介绍

Coral 是一个跨平台、可扩展的 Python 机器人框架，Coral 基于事件驱动，使用异步 IO，能够为你的需求实现提供便捷灵活的支持。

Coral 与 Nonebot2 虽然都是 Python 机器人框架，但它们的实现方式不同，面向的使用对象也不同。

相较于 Nonebot2 , Coral 更接近于 mirai ,这就好比 Forge 与 Fabric , Coral 更加完整， Nonebot2 则更加轻量。

Coral 项目已经内置了不少有用的方法和插件，它可以帮助你快速开发出一个功能丰富、可扩展的机器人。

## 特性

- [x] 跨平台支持
- [x] 插件化架构
- [x] 事件驱动模型
- [x] 权限管理系统
- [x] 多平台适配器（OneBot V11、Console等）
- [x] 多Bot管理（一个平台可连接多个账号）
- [x] NoneBot2兼容层
- [x] 丰富的消息类型支持

## 快速使用

> [!important]
> 在2025/6/8的更新中，完全重构了 Coral 框架，并引入事件总线、适配器和驱动器。这将导致部分文档/插件失效，请见谅。

> 如果你希望快速部署一个 Coral 机器人，安装插件、并投入使用，请看这里：[快速部署](docs/QuickStart.md)

- **用户手册**: [UserManual](docs/UserManual.md)
- **插件开发**: [PluginDev](docs/PluginDev.md)

> 有关更多插件，请访问 [Coral 插件库](https://github.com/ProjectCoral/Coral_Plugins)。

## 开发相关

- 开发文档: [DevManual](docs/DevManual.md)
- 参与贡献: [Contributing](docs/CONTRIBUTING.md)
- 版本发布: [Release](https://github.com/ProjectCoral/Coral/releases)

- Coral 开发组和官方系列项目: [Official](https://github.com/ProjectCoral)

## 鸣谢

> 前身 [Muice-Chatbot](https://github.com/Moemu/Muice-Chatbot)

> Onebot11 协议 [OneBot](https://github.com/howmanybots/onebot)

> 文档参考 [mirai](https://github.com/mamoe/mirai)

> 实现参考 [nonebot2](https://github.com/nonebot/nonebot2)

### 总代码贡献

<a href="https://github.com/ProjectCoral/Coral/contributors">
    <img src="https://contrib.rocks/image?repo=ProjectCoral/Coral" />
</a>

### 感谢所有为 Coral 项目做出贡献的人！

Star History：

[![Star History Chart](https://api.star-history.com/svg?repos=ProjectCoral/Coral&type=Date)](https://star-history.com/#ProjectCoral/Coral&Date)
