import json
import os
from pathlib import Path

class Config:
    def __init__(self):
        # Try to load from environment variables first (for deployment)
        self.rapidapi_key = os.getenv('RAPIDAPI_KEY')
        self.openai_api_key = os.getenv('OPENAI_API_KEY')
        self.serpapi_key = os.getenv('SERPAPI_KEY')
        self.api_host = "us-real-estate-listings.p.rapidapi.com"
        
        # If environment variables are not set, try to load from config.json (for local development)
        if not self.rapidapi_key or not self.openai_api_key:
            try:
                config_path = Path(__file__).parent.parent / 'config.json'
                if config_path.exists():
                    with open(config_path) as f:
                        config_data = json.load(f)
                        self.rapidapi_key = self.rapidapi_key or config_data.get('rapidapi_key')
                        self.openai_api_key = self.openai_api_key or config_data.get('openai_api_key')
                        self.serpapi_key = self.serpapi_key or config_data.get('serpapi_key')
            except (FileNotFoundError, json.JSONDecodeError) as e:
                print(f"Warning: Could not load config.json: {e}")
                # Continue with environment variables only

    @property
    def is_valid(self) -> bool:
        return bool(self.openai_api_key)

# Global instance - will be created when first accessed
_config_instance = None

def get_config():
    """Get the global config instance, creating it if necessary"""
    global _config_instance
    if _config_instance is None:
        _config_instance = Config()
    return _config_instance

# For backward compatibility
config = get_config() 