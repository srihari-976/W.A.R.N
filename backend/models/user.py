from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from backend.db import db, Column, Integer, String, DateTime, Boolean, relationship

class User(db.Model):
    """User model for authentication and authorization"""
    __tablename__ = 'users'
    __table_args__ = {'extend_existing': True}
    
    id = Column(Integer, primary_key=True)
    username = Column(String(80), unique=True, nullable=False)
    email = Column(String(120), unique=True, nullable=False)
    password_hash = Column(String(128))
    first_name = Column(String(50))
    last_name = Column(String(50))
    role = Column(String(20), nullable=False, default='user')
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships are handled by backrefs from other models
    
    def __init__(self, username, email, password, first_name=None, last_name=None, role='user'):
        self.username = username
        self.email = email
        self.set_password(password)
        self.first_name = first_name
        self.last_name = last_name
        self.role = role
        
    def set_password(self, password):
        """Set password hash"""
        self.password_hash = generate_password_hash(password)
        
    def check_password(self, password):
        """Check password hash"""
        return check_password_hash(self.password_hash, password)
        
    def to_dict(self):
        """Convert user to dictionary"""
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'role': self.role,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }
        
    def save(self):
        """Save user to database"""
        db.session.add(self)
        db.session.commit()
        
    def update(self, **kwargs):
        """Update user attributes"""
        for key, value in kwargs.items():
            if key == 'password':
                self.set_password(value)
            elif hasattr(self, key):
                setattr(self, key, value)
        self.updated_at = datetime.utcnow()
        db.session.commit()
        
    def delete(self):
        """Delete user from database"""
        db.session.delete(self)
        db.session.commit()
        
    @staticmethod
    def get_by_id(user_id):
        """Get user by ID"""
        return User.query.get(user_id)
        
    @staticmethod
    def get_by_username(username):
        """Get user by username"""
        return User.query.filter_by(username=username).first()
        
    @staticmethod
    def get_by_email(email):
        """Get user by email"""
        return User.query.filter_by(email=email).first()
        
    @staticmethod
    def get_all(filters=None, page=1, per_page=20):
        """
        Get all users with optional filtering
        
        Args:
            filters (dict): Dictionary of filters
            page (int): Page number
            per_page (int): Items per page
            
        Returns:
            tuple: (users, total)
        """
        query = User.query
        
        if filters:
            if 'role' in filters:
                query = query.filter_by(role=filters['role'])
            if 'is_active' in filters:
                query = query.filter_by(is_active=filters['is_active'])
                
        total = query.count()
        users = query.order_by(User.created_at.desc()).paginate(page=page, per_page=per_page)
        
        return users.items, total