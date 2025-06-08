import os
import json
import logging

logger = logging.getLogger(__name__)

main_config_template = {
    "websocket_port": 21050,
    "self_id": 123456789,
}


class Config:
    main_config = "./config.json"

    def __init__(self, main_config):
        self.main_config = main_config
        self.config = {}
        self.load_config(self.main_config)

    def load_config(self, config):
        if not os.path.exists(config):
            logger.warning("[yellow]Config file not found, creating a default one.[/]")
            self.config = main_config_template
        else:
            try:
                with open(config, "r") as f:
                    self.config = json.load(f)
            except Exception as e:
                logger.exception(f"[red]Error loading config file: {e}[/]")
                logger.warning("[yellow]Backing up and creating a default one.[/]")
                os.rename(config, config + ".bak")
                self.config = main_config_template

    def get(self, key, default=None):
        value = self.config.get(key, default)
        if value is None or value == default:
            self.set(key, default)
        return value

    def set(self, key, value):
        self.config[key] = value
        self.save()

    def save(self, config=None):
        if not config:
            config = self.main_config
        with open(config, "w") as f:
            json.dump(self.config, f, indent=4)