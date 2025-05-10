import os
from datetime import timedelta

class Config:
    """Base configuration"""
    # Basic Flask config
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key')
    DEBUG = True
    
    # Database configuration
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'sqlite:///dev.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # JWT configuration
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY', 'dev-jwt-secret-key')
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=1)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=30)
    
    # ElasticSearch configuration
    ELASTICSEARCH_HOST = os.environ.get('ELASTICSEARCH_HOST', 'http://localhost:9200')
    ELASTICSEARCH_USER = os.environ.get('ELASTICSEARCH_USER', 'elastic')
    ELASTICSEARCH_PASSWORD = os.environ.get('ELASTICSEARCH_PASSWORD', 'changeme')
    ELASTICSEARCH_INDEX = os.environ.get('ELASTICSEARCH_INDEX', 'security_events')
    
    # ML model configuration
    MODEL_DIR = os.environ.get('MODEL_DIR') or 'models'
    ANOMALY_DETECTOR_PATH = os.path.join(MODEL_DIR, 'anomaly_detector.joblib')
    THREAT_CLASSIFIER_PATH = os.path.join(MODEL_DIR, 'threat_classifier.joblib')
    
    # Logging configuration
    LOG_LEVEL = 'INFO'
    LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    LOG_FILE = os.environ.get('LOG_FILE') or 'app.log'
    
    # Security configuration
    ENABLE_AUTOMATED_RESPONSE = False
    MIN_PASSWORD_LENGTH = 12
    PASSWORD_COMPLEXITY = True
    
    # Rate limiting
    RATELIMIT_DEFAULT = "100/hour"
    RATELIMIT_STORAGE_URL = "memory://"
    
    # CORS configuration
    CORS_ORIGINS = ['http://localhost:3000']
    CORS_METHODS = ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS']
    CORS_HEADERS = ['Content-Type', 'Authorization']
    
    # API configuration
    API_PREFIX = '/api'
    API_VERSION = 'v1'
    API_TITLE = 'Security Operations Center API'
    API_DESCRIPTION = 'API for Security Operations Center'
    
    # Response configuration
    RESPONSE_TIMEOUT = 30
    RESPONSE_MAX_RETRIES = 3
    
    # Asset configuration
    ASSET_TYPES = ['server', 'workstation', 'network_device', 'database', 'application', 'cloud_service']
    ASSET_STATUSES = ['active', 'inactive', 'maintenance', 'isolated', 'decommissioned']
    
    # Alert configuration
    ALERT_SEVERITIES = ['critical', 'high', 'medium', 'low']
    ALERT_STATUSES = ['new', 'in_progress', 'resolved', 'false_positive', 'ignored']
    
    # Event configuration
    EVENT_TYPES = ['authentication', 'authorization', 'network', 'system', 'application', 'database', 'security']
    EVENT_SOURCES = ['firewall', 'ids', 'ips', 'antivirus', 'siem', 'endpoint', 'cloud']
    
    # Session configuration
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    PERMANENT_SESSION_LIFETIME = timedelta(days=1)
    
    # Alert settings
    MAX_ALERTS_PER_PAGE = 100
    ALERT_RETENTION_DAYS = 90
    
    # Asset settings
    ASSET_SCAN_INTERVAL = 24  # hours
    
    # Event settings
    EVENT_RETENTION_DAYS = 90
    MAX_EVENTS_PER_ALERT = 1000

class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///dev.db'
    CORS_ORIGINS = ['*']

class TestingConfig(Config):
    """Testing configuration"""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///test.db'
    WTF_CSRF_ENABLED = False

class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    TESTING = False
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')
    SECRET_KEY = os.environ.get('SECRET_KEY')
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY')
    ENABLE_AUTOMATED_RESPONSE = True
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    CORS_ORIGINS = [os.environ.get('FRONTEND_URL', 'https://example.com')]

# Configuration dictionary
config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}

def get_config():
    """Get configuration based on environment"""
    env = os.environ.get('FLASK_ENV', 'default')
    return config.get(env, config['default'])