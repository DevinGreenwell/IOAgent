"""Centralized configuration management for IOAgent application."""

import os
from typing import Dict, Any, Optional
from datetime import timedelta
import secrets
from pathlib import Path


class Config:
    """Base configuration class."""
    
    # Application
    APP_NAME = "IOAgent"
    VERSION = "1.0.0"
    
    # Paths
    BASE_DIR = Path(__file__).parent.parent.parent
    STATIC_FOLDER = BASE_DIR / "src" / "static"
    UPLOAD_FOLDER = BASE_DIR / "uploads"
    PROJECTS_FOLDER = BASE_DIR / "projects"
    
    # Flask
    SECRET_KEY = os.environ.get('SECRET_KEY') or secrets.token_hex(32)
    FLASK_ENV = os.environ.get('FLASK_ENV', 'development')
    DEBUG = False
    TESTING = False
    
    # Database
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_size': 10,
        'max_overflow': 20,
        'pool_pre_ping': True,
        'pool_recycle': 300,
        'pool_timeout': 30,
    }
    
    # JWT
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY') or secrets.token_hex(32)
    JWT_ALGORITHM = 'HS256'
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(minutes=15)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=7)
    JWT_TOKEN_LOCATION = ['headers', 'cookies']
    JWT_HEADER_NAME = 'Authorization'
    JWT_HEADER_TYPE = 'Bearer'
    JWT_COOKIE_SECURE = False
    JWT_COOKIE_CSRF_PROTECT = True
    JWT_CSRF_IN_COOKIES = True
    JWT_ACCESS_CSRF_HEADER_NAME = 'X-CSRF-TOKEN'
    JWT_REFRESH_CSRF_HEADER_NAME = 'X-CSRF-TOKEN'
    
    # Session
    SESSION_COOKIE_SECURE = False
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    
    # File Upload
    MAX_CONTENT_LENGTH = 100 * 1024 * 1024  # 100MB
    ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx', 'txt', 'jpg', 'jpeg', 'png'}
    
    # CORS
    CORS_ORIGINS = []
    CORS_SUPPORTS_CREDENTIALS = True
    
    # Rate Limiting
    RATE_LIMIT_STORAGE_URL = os.environ.get('REDIS_URL')
    AUTH_RATE_LIMIT = (5, 60)  # 5 requests per minute
    API_RATE_LIMIT = (100, 60)  # 100 requests per minute
    UPLOAD_RATE_LIMIT = (10, 300)  # 10 uploads per 5 minutes
    
    # AI Configuration
    ANTHROPIC_API_KEY = os.environ.get('ANTHROPIC_API_KEY')
    ANTHROPIC_MODEL = "claude-3-5-sonnet-20241022"
    AI_MAX_TOKENS = 4000
    AI_TEMPERATURE = 0.3
    
    # Celery Configuration
    CELERY_BROKER_URL = os.environ.get('CELERY_BROKER_URL', 'redis://localhost:6379/0')
    CELERY_RESULT_BACKEND = os.environ.get('CELERY_RESULT_BACKEND', 'redis://localhost:6379/0')
    
    # Email Configuration
    SMTP_HOST = os.environ.get('SMTP_HOST', 'localhost')
    SMTP_PORT = int(os.environ.get('SMTP_PORT', '587'))
    SMTP_USER = os.environ.get('SMTP_USER')
    SMTP_PASS = os.environ.get('SMTP_PASS')
    FROM_EMAIL = os.environ.get('FROM_EMAIL', 'noreply@ioagent.app')
    
    # Logging
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
    LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    LOG_FILE = 'ioagent.log'
    
    # Admin
    ADMIN_USERNAME = os.environ.get('ADMIN_USERNAME', 'admin')
    ADMIN_EMAIL = os.environ.get('ADMIN_EMAIL', 'admin@ioagent.local')
    ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD')
    
    @classmethod
    def init_app(cls, app):
        """Initialize application with configuration."""
        # Create required directories
        cls.UPLOAD_FOLDER.mkdir(parents=True, exist_ok=True)
        cls.PROJECTS_FOLDER.mkdir(parents=True, exist_ok=True)
        
        # Set up logging
        import logging
        logging.basicConfig(
            level=getattr(logging, cls.LOG_LEVEL),
            format=cls.LOG_FORMAT
        )


class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        f'sqlite:///{Config.BASE_DIR / "src" / "database" / "app.db"}'
    
    # Development CORS
    CORS_ORIGINS = [
        'http://localhost:3000',
        'http://127.0.0.1:5000',
        'http://localhost:5000',
        'http://localhost:5001'
    ]
    
    # Development security (less strict)
    JWT_COOKIE_SECURE = False
    SESSION_COOKIE_SECURE = False


class ProductionConfig(Config):
    """Production configuration."""
    DEBUG = False
    
    # Force secure settings
    JWT_COOKIE_SECURE = True
    SESSION_COOKIE_SECURE = True
    
    # Database
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')
    if SQLALCHEMY_DATABASE_URI and SQLALCHEMY_DATABASE_URI.startswith('postgres://'):
        # Fix for SQLAlchemy 1.4+
        SQLALCHEMY_DATABASE_URI = SQLALCHEMY_DATABASE_URI.replace('postgres://', 'postgresql://', 1)
    
    # Production CORS - should be specific domains
    CORS_ORIGINS = [
        'https://ioagent.onrender.com',
        'https://ioagent-*.onrender.com',  # For preview deployments
    ]
    
    @classmethod
    def init_app(cls, app):
        """Production-specific initialization."""
        super().init_app(app)
        
        # Ensure required environment variables
        required_vars = ['SECRET_KEY', 'JWT_SECRET_KEY', 'DATABASE_URL']
        missing = [var for var in required_vars if not os.environ.get(var)]
        if missing:
            raise ValueError(f"Missing required environment variables: {', '.join(missing)}")
        
        # Set up production logging
        import logging
        from logging.handlers import RotatingFileHandler
        
        if not app.debug:
            file_handler = RotatingFileHandler(
                cls.LOG_FILE,
                maxBytes=10 * 1024 * 1024,  # 10MB
                backupCount=10
            )
            file_handler.setFormatter(logging.Formatter(cls.LOG_FORMAT))
            file_handler.setLevel(logging.INFO)
            app.logger.addHandler(file_handler)
            app.logger.setLevel(logging.INFO)
            app.logger.info(f'{cls.APP_NAME} startup')


class TestingConfig(Config):
    """Testing configuration."""
    TESTING = True
    DEBUG = True
    
    # Use in-memory database for tests
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    
    # Disable CSRF for testing
    WTF_CSRF_ENABLED = False
    JWT_COOKIE_CSRF_PROTECT = False
    
    # Test-specific settings
    SECRET_KEY = 'test-secret-key'
    JWT_SECRET_KEY = 'test-jwt-secret'


# Configuration dictionary
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}


def get_config(config_name: Optional[str] = None) -> Config:
    """Get configuration object based on environment."""
    config_name = config_name or os.environ.get('FLASK_ENV', 'default')
    return config.get(config_name, config['default'])