# common/config/config_loader.py

import os
import yaml
from pathlib import Path
from typing import Dict, Any


class ConfigLoader:


    _instance = None
    _config = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance


    def __init__(self):
        self._config = self._load_config()

    def _load_config(self) -> Dict[str, Any]:
        config_dir = Path(__file__).parent
        config_file = config_dir / 'config.yml'

        with open(config_file, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)

        env = os.getenv('TEST_ENV', 'dev')
        env_config = config.get(env, {})

        default_config = config.get("default", {})
        result = self._merge_config(default_config, env_config)

        result = self._override_with_env(result)

        return result

    def _merge_config(self, default: Dict, override: Dict) -> Dict:
        result = default.copy()
        for key, value in override.items():
            if isinstance(value, dict) and key in result:
                result[key] = self._merge_config(result.get(key, {}), value)
            else:
                result[key] = value
        return result

    def _override_with_env(self, config: Dict) -> Dict:
        env_mappings = {
            "ADMIN_URL": ('admin', 'base_url'),
            "MEMBER_URL": ('member', 'base_url'),

            "DB_HOST": ('database', 'host'),
            "DB_PORT": ('database', 'port'),
            "DB_USER": ('database', 'user'),
            "DB_PASSWORD": ('database', 'password'),
            "DB_NAME": ('database', 'database'),

            "REDIS_HOST": ('redis', 'host'),
            "REDIS_PORT": ('redis', 'port'),
            "REDIS_DB": ('redis', 'db'),
        }

        for env_key, path in env_mappings.items():
            value = os.getenv(env_key)
            if value is not None:
                if path[-1] in ['port', 'db']:
                    value = int(value)
                self._set_nested_value(config, path, value)

        return config

    def _set_nested_value(self, config: Dict, path: tuple, value):
        current = config
        for key in path[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]
        current[path[-1]] = value

    def get(self, key: str = None, default: Any = None) -> Any:
        if key is None:
            return self._config

        keys = key.split('.')
        value = self._config
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
            else:
                return default
            if value is None:
                return default
        return value

    def reload(self):
        self._config = self._load_config()

config = ConfigLoader()