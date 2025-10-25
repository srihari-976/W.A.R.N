from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
import hashlib
import asyncio
from datetime import timedelta

from backend.services.brute_force_detector import BruteForceDetector
from backend.services.risk_action_system import RiskActionSystem, RiskLevel, ActionType
from backend.services.ip_blocker import IPBlocker
from backend.services.process_killer import ProcessKiller

auth_bp = Blueprint('auth', __name__)

# Initialize security services
brute_force_detector = BruteForceDetector()
ip_blocker = IPBlocker()
process_killer = ProcessKiller()
risk_action_system = RiskActionSystem(ip_blocker, process_killer)

@auth_bp.route('/login', methods=['POST'])
def login():
    """Simple login with JWT token"""
    try:
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')
        ip_address = data.get('ip_address', request.remote_addr)
        
        if not username or not password:
            return jsonify({'error': 'Username and password required'}), 400
        
        # Simple auth check (demo purposes)
        if password == 'demo123' or len(password) >= 6:
            # Create JWT token
            access_token = create_access_token(
                identity=username,
                expires_delta=timedelta(hours=24)
            )
            
            return jsonify({
                'success': True,
                'access_token': access_token,
                'refresh_token': access_token,  # Same for demo
                'token_type': 'bearer',
                'expires_in': 86400,
                'user_id': 'user_123',
                'username': username
            })
        else:
            # Handle failed login with brute force protection
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            risk_analysis = loop.run_until_complete(
                brute_force_detector.record_failed_login(username, ip_address, password)
            )
            
            # Execute security action if critical
            if risk_analysis['risk_level'] == 'critical':
                loop.run_until_complete(
                    risk_action_system.execute_action(
                        risk_level=RiskLevel.CRITICAL,
                        action=ActionType.TERMINATE_RESOURCES,
                        threat_data={
                            'ip': ip_address,
                            'username': username,
                            'process': 'chrome'
                        }
                    )
                )
            
            loop.close()
            
            return jsonify({
                'success': False,
                'message': risk_analysis['message'],
                'risk_level': risk_analysis['risk_level'],
                'action': risk_analysis['action'],
                'attempts_remaining': 3 - risk_analysis['user_attempts']
            }), 401
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@auth_bp.route('/register', methods=['POST'])
def register():
    """Simple registration"""
    try:
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')
        
        if not username or not password:
            return jsonify({'error': 'Username and password required'}), 400
        
        if len(username) < 3:
            return jsonify({'error': 'Username must be at least 3 characters'}), 400
            
        if len(password) < 6:
            return jsonify({'error': 'Password must be at least 6 characters'}), 400
        
        # Create JWT token
        access_token = create_access_token(
            identity=username,
            expires_delta=timedelta(hours=24)
        )
        
        return jsonify({
            'success': True,
            'access_token': access_token,
            'refresh_token': access_token,
            'token_type': 'bearer',
            'expires_in': 86400,
            'user_id': 'user_123',
            'username': username
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@auth_bp.route('/refresh', methods=['POST'])
def refresh():
    """Refresh token"""
    try:
        data = request.get_json()
        refresh_token = data.get('refresh_token')
        
        if not refresh_token:
            return jsonify({'error': 'Refresh token required'}), 400
        
        # For demo, just create a new token
        access_token = create_access_token(
            identity='demo_user',
            expires_delta=timedelta(hours=24)
        )
        
        return jsonify({
            'access_token': access_token,
            'refresh_token': refresh_token,
            'token_type': 'bearer',
            'expires_in': 86400
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@auth_bp.route('/me', methods=['GET'])
@jwt_required()
def get_current_user():
    """Get current user info"""
    try:
        current_user = get_jwt_identity()
        return jsonify({
            'id': 'user_123',
            'username': current_user,
            'email': f'{current_user}@example.com'
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@auth_bp.route('/logout', methods=['POST'])
@jwt_required()
def logout():
    """Logout user"""
    return jsonify({'message': 'Logged out successfully'})