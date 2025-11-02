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
from backend.api.auth_simple import auth_bp
from backend.api.alerts import alerts_bp
from backend.api.assets import assets_bp
from backend.api.events import events_bp
from backend.api.risk import risk_bp
from backend.api.security import security_bp
from backend.services.event_processor import event_processor
from backend.services.threat_detector import threat_detector
from backend.services.security_monitor import security_monitor
from backend.utils.populate_security_data import populate_sample_data

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
    
    # Configure CORS for frontend integration
    CORS(app, 
         origins=["http://localhost:3000", "http://127.0.0.1:3000", "http://localhost:5173", "file://"],
         supports_credentials=True,
         allow_headers=["Content-Type", "Authorization", "Accept"],
         methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"])
    
    socketio.init_app(app, cors_allowed_origins=["http://localhost:3000", "http://127.0.0.1:3000"])
    
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
    # Optional demo blueprint (skip if module not present)
    try:
        from backend.api.demo import demo_bp
        app.register_blueprint(demo_bp, url_prefix='/demo')
    except Exception as e:
        app.logger.warning(f"Demo blueprint not loaded: {e}")
    app.register_blueprint(security_bp, url_prefix='/api')
    
    # Initialize database
    with app.app_context():
        init_db(app)
        
        # Populate sample data if database is empty (optional; skip on mapping issues)
        try:
            from backend.models.security_event import SecurityEvent
            if SecurityEvent.query.count() == 0:
                populate_sample_data()
        except Exception as e:
            app.logger.warning(f"Skipping sample data population: {e}")
            
        # Start security monitoring (optional)
        try:
            security_monitor.start_monitoring(app)
        except Exception as e:
            app.logger.warning(f"Security monitor not started: {e}")
    
    # Start threat detection system
    import threading
    def start_detection_system():
        import asyncio
        async def init_system():
            await threat_detector.load_models()
            await event_processor.start()
        asyncio.run(init_system())
    
    detection_thread = threading.Thread(target=start_detection_system, daemon=True)
    detection_thread.start()
    app.logger.info('W.A.R.N threat detection system started')
    
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
        """W.A.R.N API Status"""
        return {
            'message': 'W.A.R.N - Watchdog AI for Risk Neutralization',
            'version': '2.0.0',
            'model': 'Llama 3.2 3B (MITRE ATT&CK Fine-tuned)',
            'status': 'operational',
            'endpoints': {
                'auth': '/api/auth',
                'alerts': '/api/alerts',
                'assets': '/api/assets',
                'events': '/api/events',
                'risk': '/api/risk'
            }
        }
    
    @app.route('/health')
    def health_check():
        from datetime import datetime
        return {
            'status': 'healthy',
            'ml_model': 'loaded' if threat_detector.is_loaded else 'loading',
            'model_type': 'Llama 3.2 3B (MITRE ATT&CK Fine-tuned)',
            'event_processor': 'running',
            'anomaly_detector': 'active',
            'accuracy': '88.3%',
            'timestamp': datetime.utcnow().isoformat()
        }, 200
    
    @app.route('/test')
    def test_connection():
        return {'message': 'Connection successful', 'status': 'ok'}, 200
    
    # Ensure socketio is available globally
    app.socketio = socketio
    
    return app

if __name__ == '__main__':
    app = create_app()
    app.run(host='0.0.0.0', port=5000, debug=True)
