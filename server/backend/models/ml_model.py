from datetime import datetime
from backend.db import db

class MLModel(db.Model):
    """ML Model for storing model metadata"""
    __tablename__ = 'ml_models'
    __table_args__ = {'extend_existing': True}
    
    id = db.Column(db.String(36), primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    model_type = db.Column(db.String(50), nullable=False)  # anomaly_detection, classifier, llm
    description = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Model metadata
    version = db.Column(db.String(20), default='1.0.0')
    status = db.Column(db.String(20), default='created')  # created, training, trained, failed
    parameters = db.Column(db.JSON, nullable=True)
    performance_metrics = db.Column(db.JSON, nullable=True)
    features = db.Column(db.JSON, nullable=True)  # Feature importance or configuration
    
    # Storage paths
    model_path = db.Column(db.String(255), nullable=True)
    
    def __init__(self, name, model_type, description=None, parameters=None, 
                 performance_metrics=None, features=None, status='created'):
        import uuid
        self.id = str(uuid.uuid4())
        self.name = name
        self.model_type = model_type
        self.description = description
        self.parameters = parameters or {}
        self.performance_metrics = performance_metrics or {}
        self.features = features or []
        self.status = status
    
    def to_dict(self):
        """Convert ML model to dictionary"""
        return {
            'id': self.id,
            'name': self.name,
            'model_type': self.model_type,
            'description': self.description,
            'version': self.version,
            'status': self.status,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'parameters': self.parameters,
            'performance_metrics': self.performance_metrics,
            'features': self.features,
            'model_path': self.model_path
        }
    
    def save(self):
        """Save ML model to database"""
        db.session.add(self)
        db.session.commit()
        return self
    
    def update(self, **kwargs):
        """Update ML model attributes"""
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
        self.updated_at = datetime.utcnow()
        db.session.commit()
        return self
    
    def delete(self):
        """Delete ML model from database"""
        db.session.delete(self)
        db.session.commit()