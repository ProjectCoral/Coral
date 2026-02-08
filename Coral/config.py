import os
import json
import logging

logger = logging.getLogger(__name__)

# 主配置模板
main_config_template = {
    "websocket_port": 21050,
    "self_id": 123456789,
}


class Config:
    """配置管理类"""
    
    main_config = "./config.json"

    def __init__(self, main_config):
        """
        初始化配置管理器
        
        Args:
            main_config: 主配置文件路径
        """
        self.main_config = main_config
        self.config = {}
        self.load_config(self.main_config)

    def load_config(self, config):
        """加载配置文件"""
        if not os.path.exists(config):
            logger.warning("[yellow]Config file not found, creating default config.[/]")
            self.config = main_config_template
        else:
            try:
                with open(config, "r", encoding="utf-8") as f:
                    self.config = json.load(f)
            except Exception as e:
                logger.exception(f"[red]Error loading config file: {e}[/]")
                logger.warning("[yellow]Backing up and creating default config.[/]")
                os.rename(config, config + ".bak")
                self.config = main_config_template

    def get(self, key, default=None):
        """
        获取配置值
        
        Args:
            key: 配置键名
            default: 默认值
            
        Returns:
            配置值，如果不存在则返回默认值
        """
        value = self.config.get(key, default)
        if value is None or value == default:
            self.set(key, default)
        return value

    def set(self, key, value):
        """
        设置配置值
        
        Args:
            key: 配置键名
            value: 配置值
        """
        self.config[key] = value
        self.save()

    def save(self, config=None):
        """
        保存配置到文件
        
        Args:
            config: 配置文件路径，如果为None则使用主配置文件
        """
        if not config:
            config = self.main_config
        with open(config, "w", encoding="utf-8") as f:
            json.dump(self.config, f, indent=4)
