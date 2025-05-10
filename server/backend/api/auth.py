# Authentication API
from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from backend.models.user import User
from backend.db import db
from datetime import datetime, timedelta
import logging
import jwt
import bcrypt
from werkzeug.security import check_password_hash

logger = logging.getLogger(__name__)

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['POST'])
def register():
    """Register a new user"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['username', 'email', 'password']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        # Check if user already exists
        if User.query.filter_by(username=data['username']).first():
            return jsonify({'error': 'Username already exists'}), 400
            
        if User.query.filter_by(email=data['email']).first():
            return jsonify({'error': 'Email already exists'}), 400
            
        # Create new user
        user = User(
            username=data['username'],
            email=data['email'],
            password=data['password'],  # Password will be hashed in the User model
            role=data.get('role', 'user')
        )
        
        db.session.add(user)
        db.session.commit()
        
        return jsonify({
            'message': 'User registered successfully',
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'role': user.role
            }
        }), 201
        
    except Exception as e:
        logger.error(f"Error registering user: {str(e)}")
        db.session.rollback()
        return jsonify({'error': 'Error registering user'}), 500

@auth_bp.route('/login', methods=['POST'])
def login():
    """Login user and return JWT token"""
    try:
        data = request.get_json()
        
        # Validate input
        if not data or 'username' not in data or 'password' not in data:
            return jsonify({'error': 'Missing username or password'}), 400
            
        # Find user
        user = User.query.filter_by(username=data['username']).first()
        if not user:
            logger.warning(f"Login attempt with non-existent username: {data['username']}")
            return jsonify({'error': 'Invalid credentials'}), 401
            
        # Check password
        if not user.check_password(data['password']):
            logger.warning(f"Failed login attempt for user: {data['username']}")
            return jsonify({'error': 'Invalid credentials'}), 401
            
        # Create token
        try:
            access_token = create_access_token(identity=str(user.id))
        except Exception as e:
            logger.error(f"Error creating access token: {str(e)}")
            return jsonify({'error': 'Error creating access token'}), 500
            
        return jsonify({
            'access_token': access_token,
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'role': user.role
            }
        }), 200
            
    except Exception as e:
        logger.error(f"Login error: {str(e)}")
        return jsonify({'error': 'Error logging in'}), 500

@auth_bp.route('/me', methods=['GET'])
@jwt_required()
def get_current_user():
    """Get current user information"""
    try:
        user_id = int(get_jwt_identity())
        user = User.query.get(user_id)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
            
        return jsonify({
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'role': user.role
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting user info: {str(e)}")
        return jsonify({'error': 'Error getting user info'}), 500

@auth_bp.route('/auth/profile', methods=['GET'])
@jwt_required()
def get_profile():
    """Get user profile"""
    try:
        # Get current user
        user_id = int(get_jwt_identity())
        user = User.query.get(user_id)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
            
        return jsonify({
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'role': user.role,
            'created_at': user.created_at.isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error getting profile: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@auth_bp.route('/auth/profile', methods=['PUT'])
@jwt_required()
def update_profile():
    """Update user profile"""
    try:
        # Get current user
        user_id = int(get_jwt_identity())
        user = User.query.get(user_id)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
            
        data = request.get_json()
        
        # Update fields
        if 'email' in data:
            # Check if email already exists
            if User.query.filter(User.email == data['email'], User.id != user_id).first():
                return jsonify({'error': 'Email already exists'}), 409
            user.email = data['email']
            
        if 'password' in data:
            user.set_password(data['password'])
            
        db.session.commit()
        
        return jsonify({
            'message': 'Profile updated successfully',
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'role': user.role
            }
        })
        
    except Exception as e:
        logger.error(f"Error updating profile: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@auth_bp.route('/auth/verify', methods=['GET'])
def verify_token():
    """Verify JWT token validity"""
    try:
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({'error': 'Unauthorized'}), 401
            
        token = auth_header.split(' ')[1]
        
        try:
            payload = jwt.decode(
                token, 
                current_app.config['JWT_SECRET_KEY'], 
                algorithms=['HS256']
            )
            
            # Get user to ensure they still exist and are active
            user = User.query.get(payload['sub'])
            if not user or not user.is_active:
                return jsonify({'error': 'User not found or inactive'}), 401
                
            return jsonify({
                'valid': True,
                'user': {
                    'id': user.id,
                    'username': user.username,
                    'email': user.email,
                    'role': user.role
                }
            }), 200
                
        except jwt.ExpiredSignatureError:
            return jsonify({'error': 'Token expired'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'error': 'Invalid token'}), 401
            
    except Exception as e:
        logger.error(f"Token verification error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@auth_bp.route('/auth/change-password', methods=['POST'])
def change_password():
    """Change user password"""
    try:
        # Verify user is authenticated
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({'error': 'Unauthorized'}), 401
            
        token = auth_header.split(' ')[1]
        
        try:
            payload = jwt.decode(
                token, 
                current_app.config['JWT_SECRET_KEY'], 
                algorithms=['HS256']
            )
            
            user_id = payload['sub']
                
        except jwt.ExpiredSignatureError:
            return jsonify({'error': 'Token expired'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'error': 'Invalid token'}), 401
            
        # Process password change
        data = request.get_json()
        
        # Validate required fields
        if not all(k in data for k in ['current_password', 'new_password']):
            return jsonify({'error': 'Missing required fields'}), 400
            
        # Get user
        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404
            
        # Verify current password
        if not check_password_hash(user.password_hash, data['current_password']):
            return jsonify({'error': 'Current password is incorrect'}), 401
            
        # Update password
        user.password_hash = bcrypt.hashpw(
            data['new_password'].encode('utf-8'), 
            bcrypt.gensalt()
        )
        user.updated_at = datetime.utcnow()
        user.save()
        
        return jsonify({'message': 'Password changed successfully'}), 200
            
    except Exception as e:
        logger.error(f"Password change error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500