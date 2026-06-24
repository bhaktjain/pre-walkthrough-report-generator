import json
import os
from pathlib import Path

# Default Claude model used for transcript extraction. Override with the CLAUDE_MODEL env var.
DEFAULT_CLAUDE_MODEL = "claude-opus-4-8"


class Config:
    def __init__(self):
        # Environment variables take precedence (deployment / secret manager).
        self.anthropic_api_key = os.getenv('ANTHROPIC_API_KEY')
        self.rapidapi_key = os.getenv('RAPIDAPI_KEY')
        self.serpapi_key = os.getenv('SERPAPI_KEY')
        self.claude_model = os.getenv('CLAUDE_MODEL', DEFAULT_CLAUDE_MODEL)
        self.api_host = "us-real-estate-listings.p.rapidapi.com"

        # Zoho CRM credentials (used by the neighboring-projects feature).
        self.zoho_client_id = os.getenv('ZOHO_CLIENT_ID')
        self.zoho_client_secret = os.getenv('ZOHO_CLIENT_SECRET')
        self.zoho_refresh_token = os.getenv('ZOHO_REFRESH_TOKEN')

        # Legacy: still read an OpenAI key if present so old configs don't error,
        # but it is no longer used by the pipeline (migrated to Anthropic Claude).
        self.openai_api_key = os.getenv('OPENAI_API_KEY')

        # Fill any still-missing values from config.json. Both the package-level and
        # repo-root files are consulted and merged (each only fills values still unset),
        # so a key present in either location is found regardless of which file holds it.
        for config_path in [
            Path(__file__).parent.parent / 'config.json',  # pre_walkthrough_generator/config.json
            Path('config.json'),                            # repo-root / server-side config.json
        ]:
            try:
                if not config_path.exists():
                    continue
                with open(config_path) as f:
                    config_data = json.load(f)
            except (OSError, json.JSONDecodeError) as e:
                print(f"Warning: Could not load {config_path}: {e}")
                continue

            # Support both the nested {"api_keys": {...}} shape and a flat shape.
            api_keys = config_data.get('api_keys', config_data)

            self.anthropic_api_key = (
                self.anthropic_api_key
                or api_keys.get('anthropic')
                or api_keys.get('claude')
                or api_keys.get('anthropic_api_key')
            )
            self.rapidapi_key = self.rapidapi_key or api_keys.get('rapidapi') or api_keys.get('rapidapi_key')
            self.serpapi_key = self.serpapi_key or api_keys.get('serpapi') or api_keys.get('serpapi_key')
            self.openai_api_key = self.openai_api_key or api_keys.get('openai') or api_keys.get('openai_api_key')

            zoho = api_keys.get('zoho')
            if isinstance(zoho, dict):
                self.zoho_client_id = self.zoho_client_id or zoho.get('client_id')
                self.zoho_client_secret = self.zoho_client_secret or zoho.get('client_secret')
                self.zoho_refresh_token = self.zoho_refresh_token or zoho.get('refresh_token')

    @property
    def is_valid(self) -> bool:
        """The pipeline requires an Anthropic API key for transcript extraction."""
        return bool(self.anthropic_api_key)

    @property
    def has_zoho(self) -> bool:
        """Whether the full Zoho OAuth credential triple is available."""
        return bool(self.zoho_client_id and self.zoho_client_secret and self.zoho_refresh_token)


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
