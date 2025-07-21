"""Settings management for IOAgent application."""

import os
import json
from typing import Dict, Any, Optional
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class Settings:
    """Application settings manager."""
    
    def __init__(self, settings_file: Optional[Path] = None):
        """Initialize settings manager."""
        self.settings_file = settings_file or Path.home() / '.ioagent' / 'settings.json'
        self.settings_file.parent.mkdir(parents=True, exist_ok=True)
        self._settings = self._load_settings()
    
    def _load_settings(self) -> Dict[str, Any]:
        """Load settings from file."""
        if self.settings_file.exists():
            try:
                with open(self.settings_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error loading settings: {e}")
                return self._default_settings()
        return self._default_settings()
    
    def _default_settings(self) -> Dict[str, Any]:
        """Get default settings."""
        return {
            'theme': 'light',
            'language': 'en',
            'notifications': {
                'email': True,
                'in_app': True
            },
            'ui': {
                'items_per_page': 20,
                'show_tooltips': True,
                'compact_mode': False
            },
            'api': {
                'timeout': 30,
                'retry_count': 3
            },
            'export': {
                'format': 'docx',
                'include_metadata': True
            }
        }
    
    def save(self) -> None:
        """Save settings to file."""
        try:
            with open(self.settings_file, 'w') as f:
                json.dump(self._settings, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving settings: {e}")
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get setting value."""
        keys = key.split('.')
        value = self._settings
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    def set(self, key: str, value: Any) -> None:
        """Set setting value."""
        keys = key.split('.')
        settings = self._settings
        
        # Navigate to the parent dictionary
        for k in keys[:-1]:
            if k not in settings:
                settings[k] = {}
            settings = settings[k]
        
        # Set the value
        settings[keys[-1]] = value
        
        # Save changes
        self.save()
    
    def update(self, updates: Dict[str, Any]) -> None:
        """Update multiple settings."""
        def deep_update(target: Dict, source: Dict) -> None:
            for key, value in source.items():
                if isinstance(value, dict) and key in target and isinstance(target[key], dict):
                    deep_update(target[key], value)
                else:
                    target[key] = value
        
        deep_update(self._settings, updates)
        self.save()
    
    def reset(self) -> None:
        """Reset settings to defaults."""
        self._settings = self._default_settings()
        self.save()
    
    def export_settings(self) -> Dict[str, Any]:
        """Export settings for backup."""
        return self._settings.copy()
    
    def import_settings(self, settings: Dict[str, Any]) -> None:
        """Import settings from backup."""
        self._settings = settings
        self.save()


class EnvironmentManager:
    """Manage environment-specific configurations."""
    
    @staticmethod
    def load_env_file(env_file: Path = Path('.env')) -> None:
        """Load environment variables from file."""
        if env_file.exists():
            from dotenv import load_dotenv
            load_dotenv(env_file)
    
    @staticmethod
    def get_required_vars() -> Dict[str, str]:
        """Get required environment variables for each environment."""
        return {
            'development': [
                'FLASK_ENV',
                'SECRET_KEY',
                'JWT_SECRET_KEY'
            ],
            'production': [
                'FLASK_ENV',
                'SECRET_KEY',
                'JWT_SECRET_KEY',
                'DATABASE_URL',
                'ANTHROPIC_API_KEY'
            ],
            'testing': [
                'FLASK_ENV'
            ]
        }
    
    @staticmethod
    def validate_environment() -> Dict[str, Any]:
        """Validate environment configuration."""
        env = os.environ.get('FLASK_ENV', 'development')
        required_vars = EnvironmentManager.get_required_vars().get(env, [])
        
        missing = []
        for var in required_vars:
            if not os.environ.get(var):
                missing.append(var)
        
        return {
            'environment': env,
            'valid': len(missing) == 0,
            'missing_vars': missing
        }
    
    @staticmethod
    def get_config_summary() -> Dict[str, Any]:
        """Get configuration summary for debugging."""
        return {
            'environment': os.environ.get('FLASK_ENV', 'development'),
            'debug': os.environ.get('FLASK_DEBUG', 'False').lower() == 'true',
            'database': 'PostgreSQL' if 'postgresql' in os.environ.get('DATABASE_URL', '') else 'SQLite',
            'api_configured': bool(os.environ.get('ANTHROPIC_API_KEY')),
            'secure_cookies': os.environ.get('FLASK_ENV') == 'production',
            'port': int(os.environ.get('PORT', 5001))
        }


# Global settings instance
settings = Settings()

# Load environment on import
EnvironmentManager.load_env_file()