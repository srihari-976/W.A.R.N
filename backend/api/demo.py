from flask import Blueprint, request, jsonify
from backend.services.brute_force_protection import brute_force_protection
from backend.models.alert import Alert
from backend.db import db
import logging
import subprocess
import platform
from datetime import datetime

logger = logging.getLogger(__name__)
demo_bp = Blueprint('demo', __name__)

# Demo threat tracking
demo_threats = {}
threat_logs = []

@demo_bp.route('/instagram-login', methods=['POST'])
def instagram_login():
    try:
        data = request.get_json()
        username = data.get('username', '')
        password = data.get('password', '')
        ip = data.get('ip', '192.168.1.100')
        
        # Check if IP or username is blocked
        ip_blocked = brute_force_protection.is_ip_blocked(ip)
        user_blocked = brute_force_protection.is_user_blocked(username)
        
        if ip_blocked and user_blocked:
            return jsonify({
                'message': f'Both IP {ip} and account {username} are blocked',
                'blocked': True,
                'current_attempts': 3,
                'block_reason': 'BOTH_BLOCKED'
            }), 429
        elif ip_blocked:
            return jsonify({
                'message': f'IP {ip} is blocked. Account {username} quarantined.',
                'blocked': True,
                'current_attempts': 3,
                'block_reason': 'IP_BLOCKED'
            }), 429
        elif user_blocked:
            return jsonify({
                'message': f'Account {username} is blocked',
                'blocked': True,
                'current_attempts': 3,
                'block_reason': 'USER_BLOCKED'
            }), 429
        
        # Simulate failed login (always fail for demo)
        blocked = brute_force_protection.record_failed_login(ip, username, 'instagram_app')
        
        # Get attempt counts - use username-specific attempts for this user
        user_attempts = len(brute_force_protection.user_attempts.get(username, []))
        current_attempts = user_attempts
        
        # Add to threat logs with detailed actions
        action_taken = 'failed_login'
        security_actions = []
        
        if current_attempts == 1:
            action_taken = 'system_isolated'
            security_actions.append('System isolation initiated')
        elif current_attempts == 2:
            action_taken = 'password_reset_required'
            security_actions.append('Password reset enforced')
        elif blocked:
            action_taken = 'critical_block'
            security_actions.extend([
                'IP address blocked',
                'Browser processes terminated',
                'System quarantined'
            ])
            
            # Simulate browser process termination (demo only)
            try:
                if platform.system() == 'Windows':
                    # Kill browser processes on Windows
                    subprocess.run(['taskkill', '/f', '/im', 'chrome.exe'], 
                                 capture_output=True, check=False)
                    subprocess.run(['taskkill', '/f', '/im', 'firefox.exe'], 
                                 capture_output=True, check=False)
                    subprocess.run(['taskkill', '/f', '/im', 'msedge.exe'], 
                                 capture_output=True, check=False)
                logger.info(f"Browser processes terminated for IP: {ip}")
            except Exception as e:
                logger.warning(f"Could not terminate browser processes: {e}")
        
        threat_logs.append({
            'timestamp': datetime.utcnow().isoformat(),
            'ip': ip,
            'username': username,
            'action': action_taken,
            'attempts': current_attempts,
            'security_actions': security_actions,
            'severity': 'critical' if blocked else 'medium'
        })
        
        # Create alert in database
        try:
            alert = Alert(
                alert_type='brute_force_attempt',
                severity='critical' if blocked else 'medium',
                status='active',
                source='instagram_demo',
                description=f'Brute force attempt from {ip} - Attempt {current_attempts}/3',
                risk_score=current_attempts * 30,
                threat_level='critical' if blocked else 'medium',
                analysis=f'User: {username}, Actions: {", ".join(security_actions)}'
            )
            db.session.add(alert)
            db.session.commit()
        except Exception as e:
            logger.error(f"Error creating alert: {e}")
        
        if blocked:
            return jsonify({
                'message': 'CRITICAL: Account locked. Browser terminated and IP blocked.',
                'blocked': True,
                'current_attempts': current_attempts,
                'security_actions': security_actions,
                'browser_terminated': True
            }), 429
        else:
            return jsonify({
                'message': f'Invalid credentials. {3 - current_attempts} attempts remaining.',
                'blocked': False,
                'current_attempts': current_attempts,
                'security_actions': security_actions
            }), 401
            
    except Exception as e:
        logger.error(f"Demo login error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@demo_bp.route('/threats', methods=['GET'])
def get_threats():
    try:
        # Get current threats from both blocked IPs and users
        blocked_ips = brute_force_protection.get_blocked_ips()
        blocked_users = brute_force_protection.blocked_users
        
        threats = []
        
        # Add IP-based threats
        for ip, info in blocked_ips.items():
            threats.append({
                'id': f"threat_{ip}",
                'ip': ip,
                'username': info.get('username', 'unknown'),
                'status': 'ip_blocked',
                'severity': 'high',
                'remaining_time': info.get('remaining_seconds', 0),
                'processes_killed': 3,
                'quarantined': False
            })
        
        # Add user-based threats (quarantined users)
        for username, info in blocked_users.items():
            # Check if not already in IP threats
            existing = next((t for t in threats if t['username'] == username), None)
            if not existing:
                threats.append({
                    'id': f"user_{username}",
                    'ip': info.get('ip', 'unknown'),
                    'username': username,
                    'status': 'quarantined',
                    'severity': 'medium',
                    'remaining_time': 3600,
                    'processes_killed': 0,
                    'quarantined': True
                })
            else:
                # Update existing threat to show quarantine status
                existing['quarantined'] = True
        
        return jsonify({
            'threats': threats,
            'logs': threat_logs[-20:],  # Last 20 logs
            'total_count': len(threats)
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting threats: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@demo_bp.route('/threats/<threat_id>/action', methods=['POST'])
def threat_action(threat_id):
    try:
        data = request.get_json()
        action = data.get('action')
        
        # Extract IP from threat_id
        ip = threat_id.replace('threat_', '')
        
        if action == 'quarantine':
            # Add quarantine logic
            threat_logs.append({
                'timestamp': brute_force_protection.login_attempts[ip][-1]['timestamp'].isoformat(),
                'ip': ip,
                'action': 'quarantined',
                'message': 'Threat quarantined by admin'
            })
            
        elif action == 'unblock':
            # Remove from blocked IPs and quarantine associated users
            if ip in brute_force_protection.blocked_ips:
                blocked_info = brute_force_protection.blocked_ips[ip]
                username = blocked_info.get('username', 'unknown')
                
                # Quarantine the user when IP is unblocked
                if username != 'unknown':
                    brute_force_protection.blocked_users[username] = {
                        'blocked_at': datetime.utcnow(),
                        'ip': ip,
                        'app_name': 'instagram_app',
                        'reason': 'Auto-quarantined after IP unblock'
                    }
                
                del brute_force_protection.blocked_ips[ip]
                
                threat_logs.append({
                    'timestamp': datetime.utcnow().isoformat(),
                    'ip': ip,
                    'action': 'unblocked',
                    'message': f'IP unblocked by admin. User {username} auto-quarantined.'
                })
            
        elif action == 'terminate':
            # Simulate process termination
            threat_logs.append({
                'timestamp': brute_force_protection.login_attempts[ip][-1]['timestamp'].isoformat(),
                'ip': ip,
                'action': 'terminated',
                'message': 'Additional processes terminated'
            })
        
        return jsonify({'message': f'Action {action} completed'}), 200
        
    except Exception as e:
        logger.error(f"Error performing threat action: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@demo_bp.route('/stats', methods=['GET'])
def get_demo_stats():
    try:
        blocked_count = len(brute_force_protection.get_blocked_ips())
        total_attempts = sum(len(attempts) for attempts in brute_force_protection.login_attempts.values())
        
        # Generate hourly data for graph
        hourly_data = []
        for i in range(24):
            hourly_data.append({
                'hour': f"{i:02d}:00",
                'threats': max(0, blocked_count - (24 - i) + (i % 3))
            })
        
        return jsonify({
            'current_threats': blocked_count,
            'total_attempts': total_attempts,
            'processes_killed': blocked_count * 3,
            'hourly_threats': hourly_data
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting demo stats: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@demo_bp.route('/security-events', methods=['GET'])
def get_security_events():
    """Get real-time security events for threat control center"""
    try:
        # Get recent alerts from database
        recent_alerts = Alert.query.filter_by(source='instagram_demo').order_by(Alert.timestamp.desc()).limit(10).all()
        
        events = []
        for alert in recent_alerts:
            events.append({
                'id': alert.id,
                'timestamp': alert.timestamp.isoformat(),
                'type': alert.alert_type,
                'severity': alert.severity,
                'description': alert.description,
                'analysis': alert.analysis,
                'risk_score': alert.risk_score,
                'status': alert.status
            })
        
        # Add threat logs
        combined_events = events + threat_logs[-10:]
        
        return jsonify({
            'events': combined_events,
            'blocked_ips': list(brute_force_protection.get_blocked_ips().keys()),
            'active_threats': len(brute_force_protection.get_blocked_ips())
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting security events: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@demo_bp.route('/manual-action', methods=['POST'])
def manual_security_action():
    """Allow manual security actions from threat control center"""
    try:
        data = request.get_json()
        action_type = data.get('action')
        target_ip = data.get('ip')
        
        if action_type == 'unblock_ip':
            if target_ip in brute_force_protection.blocked_ips:
                blocked_info = brute_force_protection.blocked_ips[target_ip]
                username = blocked_info.get('username', 'unknown')
                
                # Auto-quarantine user when IP is unblocked
                if username != 'unknown':
                    brute_force_protection.blocked_users[username] = {
                        'blocked_at': datetime.utcnow(),
                        'ip': target_ip,
                        'app_name': 'instagram_app',
                        'reason': 'Auto-quarantined after manual IP unblock'
                    }
                
                del brute_force_protection.blocked_ips[target_ip]
                threat_logs.append({
                    'timestamp': datetime.utcnow().isoformat(),
                    'ip': target_ip,
                    'action': 'manual_unblock',
                    'message': f'IP manually unblocked. User {username} auto-quarantined.',
                    'severity': 'info'
                })
                return jsonify({'message': f'IP {target_ip} unblocked. User {username} quarantined.'}), 200
            else:
                return jsonify({'error': 'IP not found in blocked list'}), 404
                
        elif action_type == 'quarantine_system':
            # Quarantine all users from this IP
            for username, user_info in brute_force_protection.user_attempts.items():
                if any(attempt['ip'] == target_ip for attempt in user_info):
                    brute_force_protection.blocked_users[username] = {
                        'blocked_at': datetime.utcnow(),
                        'ip': target_ip,
                        'app_name': 'instagram_app',
                        'reason': 'Manual system quarantine'
                    }
            
            threat_logs.append({
                'timestamp': datetime.utcnow().isoformat(),
                'ip': target_ip,
                'action': 'manual_quarantine',
                'message': 'System and all associated users quarantined by administrator',
                'severity': 'high'
            })
            return jsonify({'message': f'System {target_ip} and users quarantined'}), 200
            
        elif action_type == 'unblock_user':
            username = data.get('username')
            if username and username in brute_force_protection.blocked_users:
                del brute_force_protection.blocked_users[username]
                threat_logs.append({
                    'timestamp': datetime.utcnow().isoformat(),
                    'ip': 'N/A',
                    'action': 'manual_user_unblock',
                    'message': f'User {username} manually unblocked by administrator',
                    'severity': 'info'
                })
                return jsonify({'message': f'User {username} unblocked successfully'}), 200
            else:
                return jsonify({'error': 'User not found in blocked list'}), 404
            
        else:
            return jsonify({'error': 'Unknown action type'}), 400
            
    except Exception as e:
        logger.error(f"Error performing manual action: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500