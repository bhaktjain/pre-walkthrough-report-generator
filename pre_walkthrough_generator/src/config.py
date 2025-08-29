import json
from pathlib import Path

class Config:
    def __init__(self):
        config_path = Path(__file__).parent.parent / 'config.json'
        with open(config_path) as f:
            config = json.load(f)
            self.rapidapi_key = config.get('rapidapi_key')
            self.openai_api_key = config.get('openai_api_key')
            self.serpapi_key = config.get('serpapi_key')
            self.api_host = "us-real-estate-listings.p.rapidapi.com"

    @property
    def is_valid(self) -> bool:
        return bool(self.openai_api_key)

# Create a global instance
config = Config() 