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
python Coral.py
```

至此，Coral 项目已经成功安装。

# 配置

配置文件生成在 `config.json` 中，可以自行修改。

# 插件、

Coral 项目支持插件机制，可以方便地扩展功能。

插件目录为 `plugins`。