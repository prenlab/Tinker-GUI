import argparse
import yaml
import sys
from typing import Any, Dict
import os
import logging


class ConfigManager:
    def __init__(self, template_path='templateConfig.yaml', user_path='userConfig.yaml'):
        self.template_path = template_path
        self.user_path = user_path
        self.config: Dict[str, Any] = {}
        self.logger = self._setup_logger()

# Create logger (should be straightforward; writing comments -> Copilot -> yay!)
    def _setup_logger(self):
        logger = logging.getLogger(__name__)
        if not logger.hasHandlers():
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(filename)s - %(message)s')
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        logger.setLevel(logging.INFO)
        return logger

    def load_yaml(self, path: str) -> Dict[str, Any]:
        try:
            with open(path, 'r') as f:
                self.logger.info(f"Loading YAML file: {path}")
                return yaml.safe_load(f) or {}
        except Exception as e:
            self.logger.error(f"Error loading YAML file: {e}")
            return {}

    def save_yaml(self, path: str, data: Dict[str, Any]):
        try:
            with open(path, 'w') as f:
                yaml.safe_dump(data, f)
            self.logger.info(f"Saved YAML file: {path}")
        except Exception as e:
            self.logger.error(f"Error saving YAML file: {e}")

    def load_config(self):
        # Load template config as defaults
        self.config = self.load_yaml(self.template_path)
        # Override with userConfig.yaml if exists
        if os.path.exists(self.user_path):
            user_config = self.load_yaml(self.user_path)
            if user_config:
                self.config.update(user_config)
        # Parse CLI arguments, using current config as defaults
        parser = argparse.ArgumentParser()
        for key, value in self.config.items():
            parser.add_argument(f'--{key}', type=str, help=f'Setting for {key}', default=value)
        args, unknown = parser.parse_known_args()
        # Override config with CLI arguments (highest priority)
        for key in self.config.keys():
            cli_value = getattr(args, key)
            if cli_value is not None:
                self.config[key] = cli_value
        # Save updated config to userConfig.yaml
        self.save_yaml(self.user_path, self.config)

    def get(self, key: str, default: Any = None) -> Any:
        return self.config.get(key, default)

    def all(self) -> Dict[str, Any]:
        return self.config

def main():
    manager = ConfigManager()
    manager.logger.info("Program started.")
    manager.load_config()
    manager.logger.info("Finished parsing user config.")
    manager.logger.info("Actual configuration:")
    manager.logger.info(manager.all())
    manager.logger.info("YAML dump of configuration:")
    manager.logger.info('\n' + yaml.dump(manager.all(), default_flow_style=False))

if __name__ == "__main__":
    main()
