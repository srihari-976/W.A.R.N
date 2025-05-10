# db.py - Database connection
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import MetaData
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Table, Boolean, Text, JSON, func
from sqlalchemy.orm import relationship, backref
from flask_migrate import Migrate

# Create naming convention for constraints
convention = {
    "ix": 'ix_%(column_0_label)s',
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s"
}

metadata = MetaData(naming_convention=convention)
db = SQLAlchemy(metadata=metadata)

# Initialize Flask-Migrate
migrate = Migrate()

def init_db(app):
    """Initialize the database with the app context"""
    with app.app_context():
        # Import models here to ensure they are registered with SQLAlchemy
        from backend.models import User, Asset, Alert, SecurityEvent as Event, Response, alert_events, MLModel, RiskScore
        
        # Create all tables
        db.create_all()
