# app.py
from flask import Flask, redirect, url_for
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
import os
import logging
from logging.handlers import RotatingFileHandler
from flask_socketio import SocketIO

from backend.config import get_config, Config
from backend.services.elasticsearch.client import ESClient
from backend.db import db, init_db
from backend.api.auth import auth_bp
from backend.api.alerts import alerts_bp
from backend.api.assets import assets_bp
from backend.api.events import events_bp
from backend.api.risk import risk_bp

logger = logging.getLogger(__name__)

migrate = Migrate()
jwt = JWTManager()
socketio = SocketIO()

def create_app(config_name='development'):
    """Create and configure the Flask application"""
    app = Flask(__name__)
    
    # Load configuration
    app.config.from_object(get_config())
    
    # Ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass
        
    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    CORS(app)
    socketio.init_app(app, cors_allowed_origins="*")
    
    # Configure logging
    if not os.path.exists('logs'):
        os.mkdir('logs')
    file_handler = RotatingFileHandler('logs/app.log', maxBytes=10240, backupCount=10)
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
    ))
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.setLevel(logging.INFO)
    app.logger.info('Application startup')
    
    # Initialize Elasticsearch (optional)
    try:
        es_client = ESClient()
        app.config['ELASTICSEARCH_CLIENT'] = es_client
        if es_client.es:
            logger.info("Elasticsearch connection established")
        else:
            logger.warning("Elasticsearch is not available - continuing without it")
    except Exception as e:
        logger.warning(f"Could not initialize Elasticsearch: {str(e)}")
        app.config['ELASTICSEARCH_CLIENT'] = None
    
    # Register blueprints
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(alerts_bp, url_prefix='/api/alerts')
    app.register_blueprint(assets_bp, url_prefix='/api/assets')
    app.register_blueprint(events_bp, url_prefix='/api/events')
    app.register_blueprint(risk_bp, url_prefix='/api/risk')
    
    # Initialize database
    with app.app_context():
        init_db(app)
    
    # WebSocket event handlers
    @socketio.on('connect')
    def handle_connect():
        logging.info('Client connected')
    
    @socketio.on('disconnect')
    def handle_disconnect():
        logging.info('Client disconnected')
    
    @socketio.on('subscribe_events')
    def handle_event_subscription(data):
        logging.info(f'Client subscribed to events: {data}')
    
    @app.route('/')
    def index():
        """Redirect to API documentation"""
        return {
            'message': 'Welcome to the Cybersecurity API',
            'endpoints': {
                'auth': '/api/auth',
                'alerts': '/api/alerts',
                'assets': '/api/assets',
                'events': '/api/events'
            }
        }
    
    @app.route('/health')
    def health_check():
        return {'status': 'healthy'}, 200
    
    # Ensure socketio is available globally
    app.socketio = socketio
    
    return app

if __name__ == '__main__':
    app = create_app()
    app.run(host='0.0.0.0', port=5000, debug=True)
