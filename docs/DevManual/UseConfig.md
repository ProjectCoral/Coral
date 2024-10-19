# 调用全局配置

Coral 全局配置是通过 `config` 类提供的。
它的调用格式和 json 格式类似，可以通过 `config.get('section.key')` 的方式获取配置项的值。

这里以插件注册函数为例，展示如何调用全局配置。

## 示例

1. 引入 `config` 类

    在编写好注册函数后，我们得到了示例类：
    ```python
    def register_function(register, config, perm_system):
        register.register_function("get_bot_id", TestFunction(register, config).get_bot_id)

    class TestFunction:
        register = None
        config = None

        def __init__(self, register, config):
            self.register = register
            self.config = config

        async def get_bot_id(self, *args):
            # 获取 bot_id 配置项的值
    ```

    在定义类时，我们引入了 `register` 和 `config` 两个参数，分别代表插件注册函数和全局配置。

2. 调用配置项

    你可以通过 `config.get('section.key', default=None)` 的方式获取配置项的值。

    ```python
    async def get_bot_id(self, *args):
        bot_id = self.config.get('bot_id', '123456789')
        return bot_id
    ```

    这里，我们通过 `config.get('bot_id', '123456789')` 的方式获取 `bot_id` 配置项的值，如果没有配置项，则设置并返回默认值 `'123456789'`。

    同样地，你可以使用 `config.set('section.key', value)` 的方式设置配置项的值。

    ```python
    async def set_bot_id(self, bot_id, *args):
        self.config.set('bot_id', bot_id)
        return None
    ```

    这里，我们通过 `config.set('bot_id', bot_id)` 的方式设置 `bot_id` 配置项的值。

    > 调用 `config` 类**变动**配置时，`config.config` 会**自动更新并保存**到文件中，不需要手动保存。