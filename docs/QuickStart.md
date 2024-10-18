# 快速使用

# 安装

### 1. 自动安装

项目内置了自动安装脚本`install_env.bat`，只需运行即可完成安装

或是运行以下命令：

```powershell
.\install_env.bat
```

### 2. 手动安装

项目依赖于以下环境：

- Python 3.6+
- git 2.xx+

在安装 Python 3.6+ 后，拉取项目代码到本地：

```powershell
git clone https://github.com/ProjectCoral/Coral.git
```

进入项目根目录，安装依赖：

```powershell
pip install -r requirements.txt
```

启动项目：

```powershell
python main.py
```

至此，Coral 项目已经成功安装，接下来需要接入平台。

# 接入

Coral 项目支持多种接入方式，只需注册函数并调用即可做到在任意平台使用。

对于 企鹅 平台， Coral 项目目前原生支持反向websocket `Reverse_websocket` 接入。你需要下载可用的 Onebot11 适配器（如[LLOnebot](https://github.com/LLOneBot/LLOneBot)、[Lagrange.Core](https://github.com/LagrangeDev/Lagrange.Core)），配置 `config.json` 文件中的 `websocket_port` 即可。

# 配置

配置文件生成在 `config.json` 中，可以自行修改。

# 插件、

Coral 项目支持插件机制，可以方便地扩展功能。

插件目录为 `plugins`。

关于编写插件，请参考[插件开发文档](https://github.com/ProjectCoral/Coral/blob/master/docs/PluginDev.md)。