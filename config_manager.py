import json
import os
from pathlib import Path
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)

class ConfigManager:
    """Manages dynamic configuration updates for the FastAPI server"""
    
    def __init__(self, config_file: str = "config.json"):
        self.config_file = config_file
        self.config = self.load_config()
        self.watchers = []
    
    def load_config(self) -> Dict[str, Any]:
        """Load configuration from file"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    return json.load(f)
            else:
                # Create default config
                default_config = {
                    "api_keys": {
                        "openai": "",
                        "rapidapi": "",
                        "serpapi": ""
                    },
                    "settings": {
                        "max_file_size": 10485760,  # 10MB
                        "timeout": 300,
                        "enable_logging": True,
                        "log_level": "INFO"
                    },
                    "templates": {
                        "default_template": "Pre-walkthrough_template.docx"
                    }
                }
                self.save_config(default_config)
                return default_config
        except Exception as e:
            logger.error(f"Error loading config: {e}")
            return {}
    
    def save_config(self, config: Dict[str, Any] = None):
        """Save configuration to file"""
        if config:
            self.config = config
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.config, f, indent=2)
            logger.info("Configuration saved successfully")
        except Exception as e:
            logger.error(f"Error saving config: {e}")
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value"""
        keys = key.split('.')
        value = self.config
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        return value
    
    def set(self, key: str, value: Any):
        """Set configuration value"""
        keys = key.split('.')
        config = self.config
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        config[keys[-1]] = value
        self.save_config()
    
    def update_api_keys(self, openai_key: str = None, rapidapi_key: str = None, serpapi_key: str = None):
        """Update API keys dynamically"""
        if openai_key:
            self.set("api_keys.openai", openai_key)
        if rapidapi_key:
            self.set("api_keys.rapidapi", rapidapi_key)
        if serpapi_key:
            self.set("api_keys.serpapi", serpapi_key)
        logger.info("API keys updated")
    
    def reload_config(self):
        """Reload configuration from file"""
        self.config = self.load_config()
        logger.info("Configuration reloaded")
        return self.config

# Global config manager instance
config_manager = ConfigManager() 