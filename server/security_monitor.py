import time
from datetime import datetime, timedelta
import json
import random
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from flask_socketio import SocketIO, emit
import logging
import sys
import threading
import requests
import os
import subprocess
import psutil
from collections import defaultdict
from collections import Counter
from process_monitor import setup_system_monitoring

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('security_monitor.log')
    ]
)

# Create logs directory if it doesn't exist
if not os.path.exists('logs'):
    os.makedirs('logs')

# Initialize security logs
LOGS_FILE = 'logs/security_logs.json'
def load_security_logs():
    if os.path.exists(LOGS_FILE):
        try:
            with open(LOGS_FILE, 'r') as f:
                return json.load(f)
        except json.JSONDecodeError:
            return {'events': [], 'statistics': {'total_events': 0, 'browser_kills': 0}}
    return {'events': [], 'statistics': {'total_events': 0, 'browser_kills': 0}}

def save_security_logs(logs):
    with open(LOGS_FILE, 'w') as f:
        json.dump(logs, f, indent=2)

security_logs = load_security_logs()

# Create Flask app with explicit template folder
template_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), 'templates'))
app = Flask(__name__, template_folder=template_dir)

# Configure CORS to allow all origins for testing
CORS(app, resources={
    r"/*": {
        "origins": "*",
        "methods": ["GET", "POST", "OPTIONS"],
        "allow_headers": ["Content-Type"]
    }
})

# Initialize Flask-SocketIO with CORS support
socketio = SocketIO(app, cors_allowed_origins="*")

logger = logging.getLogger(__name__)

# Global state
security_state = {
    'failed_attempts': defaultdict(lambda: {
        'count': 0,
        'first_attempt': None,
        'attempts': [],
        'username': None
    }),
    'threats': [],
    'risk_scores': {
        'overall': 0,
        'brute_force': 0,
        'suspicious_activity': 0,
        'system_health': 100
    },
    'alerts': []
}

# Constants
ATTEMPT_THRESHOLD = 5
TIME_WINDOW = 600  # 10 minutes
MAX_ALERTS = 100
RISK_LEVELS = {
    'low': (0, 30),
    'medium': (31, 70),
    'high': (71, 100)
}

def calculate_threat_score(threat_type, details):
    """Calculate a threat score based on type and details"""
    base_scores = {
        'brute_force': 70,
        'suspicious_activity': 50,
        'system_warning': 30,
        'authentication_failure': 40
    }
    
    score = base_scores.get(threat_type, 40)
    
    # Adjust score based on frequency
    if details.get('frequency', 0) > 5:
        score += 20
    
    # Cap score at 100
    return min(score, 100)

def get_risk_level(score):
    """Convert numeric score to risk level"""
    if score <= RISK_LEVELS['low'][1]:
        return 'low'
    elif score <= RISK_LEVELS['medium'][1]:
        return 'medium'
    else:
        return 'high'

def update_risk_scores():
    """Update overall risk scores based on current threats and alerts"""
    scores = security_state['risk_scores']
    
    # Calculate brute force risk
    recent_attempts = sum(1 for data in security_state['failed_attempts'].values()
                         if data['first_attempt'] and 
                         time.time() - data['first_attempt'] < TIME_WINDOW)
    scores['brute_force'] = min(100, recent_attempts * 20)
    
    # Calculate suspicious activity risk
    threat_scores = [threat['score'] for threat in security_state['threats']]
    scores['suspicious_activity'] = max(threat_scores) if threat_scores else 0
    
    # Calculate overall risk score
    scores['overall'] = max(scores['brute_force'], scores['suspicious_activity'])
    
    return scores

def add_threat(threat_type, details, source_ip=None):
    """Add a new threat to the monitoring system"""
    score = calculate_threat_score(threat_type, details)
    threat = {
        'id': len(security_state['threats']) + 1,
        'type': threat_type,
        'details': {
            'description': details.get('description', ''),
            'attack_vector': details.get('attack_vector', 'Unknown'),
            'affected_services': details.get('affected_services', []),
            'mitigation_steps': [],
            'frequency': details.get('frequency', 0),
            'source': details.get('source', source_ip),
            'target': details.get('target', 'system'),
        },
        'score': score,
        'risk_level': get_risk_level(score),
        'timestamp': datetime.now().isoformat(),
        'source_ip': source_ip,
        'status': 'active',
        'action_taken': 'quarantined' if threat_type == 'brute_force' else 'isolated'
    }

    # Add mitigation steps based on threat type
    if threat_type == 'brute_force':
        threat['details']['mitigation_steps'] = [
            'Browser process terminated',
            'IP address blocked',
            'Account access temporarily suspended',
            'Security team notified'
        ]
        threat['details']['attack_vector'] = 'Multiple failed login attempts'
        threat['details']['affected_services'] = ['Authentication System', 'User Accounts']
        threat['details']['description'] = f"Brute force attack detected from {source_ip} with {details.get('attempts', 0)} failed attempts"
    elif threat_type == 'suspicious_activity':
        threat['details']['mitigation_steps'] = [
            'Connection isolated from main network',
            'Enhanced monitoring enabled',
            'Traffic analysis initiated',
            'Behavioral analysis in progress'
        ]
    else:
        threat['details']['mitigation_steps'] = [
            'Activity logged',
            'Pattern analysis enabled',
            'Automated response ready'
        ]

    security_state['threats'].append(threat)
    
    # Log the threat addition
    logger.info(f"New threat added: {threat_type} from {source_ip}")
    logger.debug(f"Threat details: {json.dumps(threat, indent=2)}")
    
    # Broadcast the threat update with complete threat object
    broadcast_update('threat_detected', threat)
    
    # Create alert for high-risk threats
    if threat['risk_level'] in ['high', 'critical']:
        add_alert(
            title=f"High Risk {threat_type.replace('_', ' ').title()} Detected",
            description=f"Threat detected from {source_ip}. Action taken: {threat['action_taken'].title()}. {', '.join(threat['details']['mitigation_steps'])}",
            severity='high',
            threat_id=threat['id']
        )
    
    update_risk_scores()
    return threat

def add_alert(title, description, severity='medium', threat_id=None):
    """Add a new alert to the system"""
    alert = {
        'id': len(security_state['alerts']) + 1,
        'title': title,
        'description': description,
        'severity': severity,
        'timestamp': datetime.now().isoformat(),
        'threat_id': threat_id,
        'acknowledged': False
    }
    
    security_state['alerts'].append(alert)
    if len(security_state['alerts']) > MAX_ALERTS:
        security_state['alerts'].pop(0)
    
    # Broadcast the alert
    broadcast_update('process_termination' if 'terminated' in description.lower() else 'system_update', alert)
    
    return alert

@app.route('/')
def home():
    """API information endpoint"""
    return jsonify({
        'status': 'running',
        'service': 'Security Monitoring System',
        'endpoints': {
            'threats': '/api/threats',
            'alerts': '/api/alerts',
            'status': '/api/status',
            'risk': '/api/risk/scores'
        }
    })

@app.route('/api/threats')
def get_threats():
    """Get all recorded threats with enhanced details"""
    threats = security_state['threats']
    
    # Add additional context to each threat
    for threat in threats:
        if 'details' not in threat:
            threat['details'] = {
                'description': '',
                'attack_vector': 'Unknown',
                'affected_services': [],
                'mitigation_steps': []
            }
        
        # Ensure consistent structure
        threat['details'].setdefault('affected_services', [])
        threat['details'].setdefault('mitigation_steps', [])
        
        # Add default mitigation steps if none exist
        if not threat['details']['mitigation_steps']:
            if threat['type'] == 'brute_force':
                threat['details']['mitigation_steps'] = [
                    'Browser process terminated',
                    'IP address blocked',
                    'Account access temporarily suspended',
                    'Security team notified'
                ]
            elif threat['type'] == 'suspicious_activity':
                threat['details']['mitigation_steps'] = [
                    'Connection isolated from main network',
                    'Enhanced monitoring enabled',
                    'Traffic analysis initiated'
                ]
            else:
                threat['details']['mitigation_steps'] = [
                    'Activity logged',
                    'Pattern analysis enabled'
                ]

    return jsonify({
        'threats': threats,
        'total': len(threats),
        'statistics': {
            'by_type': dict(Counter(t['type'] for t in threats)),
            'by_risk_level': dict(Counter(t['risk_level'] for t in threats)),
            'by_action': dict(Counter(t['action_taken'] for t in threats))
        }
    })

@app.route('/api/alerts')
def get_alerts():
    """Get all alerts"""
    return jsonify({
        'alerts': security_state['alerts'],
        'total': len(security_state['alerts'])
    })

@app.route('/api/alerts', methods=['POST'])
def create_alert():
    """Create a new alert"""
    data = request.get_json()
    alert = add_alert(
        title=data['title'],
        description=data['description'],
        severity=data.get('severity', 'medium'),
        threat_id=data.get('threat_id')
    )
    return jsonify(alert)

@app.route('/api/risk/scores')
def get_risk_scores():
    """Get current risk scores"""
    return jsonify(update_risk_scores())

@app.route('/api/status')
def get_status():
    """Get current security status"""
    current_time = datetime.now()
    recent_window = current_time - timedelta(minutes=10)

    recent_threats = [t for t in security_state['threats'] 
                     if datetime.fromisoformat(t['timestamp']) > recent_window]
    recent_alerts = [a for a in security_state['alerts']
                    if datetime.fromisoformat(a['timestamp']) > recent_window]

    # Calculate statistics
    threat_types = {}
    risk_levels = {'low': 0, 'medium': 0, 'high': 0, 'critical': 0}
    actions_taken = {'quarantined': 0, 'isolated': 0, 'monitored': 0}

    for threat in recent_threats:
        threat_types[threat['type']] = threat_types.get(threat['type'], 0) + 1
        risk_levels[threat['risk_level']] = risk_levels.get(threat['risk_level'], 0) + 1
        actions_taken[threat['action_taken']] = actions_taken.get(threat['action_taken'], 0) + 1

    return jsonify({
        'active': True,
        'risk_scores': update_risk_scores(),
        'statistics': {
            'recent_threats_count': len(recent_threats),
            'recent_alerts_count': len(recent_alerts),
            'threat_types': threat_types,
            'risk_levels': risk_levels,
            'actions_taken': actions_taken
        },
        'tracking': {
            ip: {
                'count': data['count'],
                'first_attempt': datetime.fromtimestamp(data['first_attempt']).isoformat() if data['first_attempt'] else None,
                'attempts': [datetime.fromtimestamp(t).isoformat() for t in data['attempts']],
                'username': data['username']
            }
            for ip, data in security_state['failed_attempts'].items()
        }
    })

@app.route('/api/notifications')
def get_notifications():
    """Get all notifications with enhanced details"""
    notifications = []
    
    # Convert alerts to notifications
    for alert in security_state['alerts']:
        notification = {
            'id': alert['id'],
            'title': alert['title'],
            'message': alert['description'],
            'severity': alert['severity'],
            'timestamp': alert['timestamp'],
            'read': alert['acknowledged'],
            'threat_id': alert.get('threat_id'),
            'details': {
                'action_taken': 'Quarantined' if 'brute force' in alert['title'].lower() else 'Isolated',
                'affected_system': 'Authentication System' if 'brute force' in alert['title'].lower() else 'General System',
            }
        }
        notifications.append(notification)
    
    return jsonify({
        'notifications': notifications,
        'total': len(notifications),
        'unread': len([n for n in notifications if not n['read']])
    })

def log_security_event(event_type, details, severity='info'):
    """Log a security event to the JSON file"""
    event = {
        'id': len(security_logs['events']) + 1,
        'type': event_type,
        'details': details,
        'severity': severity,
        'timestamp': datetime.now().isoformat(),
        'source_ip': details.get('source_ip', 'unknown'),
        'action_taken': details.get('action_taken', 'none')
    }
    
    security_logs['events'].insert(0, event)  # Add to beginning of list
    security_logs['statistics']['total_events'] += 1
    
    if event_type == 'browser_kill':
        security_logs['statistics']['browser_kills'] += 1
    
    # Keep only last 1000 events
    if len(security_logs['events']) > 1000:
        security_logs['events'] = security_logs['events'][:1000]
    
    save_security_logs(security_logs)
    return event

@app.route('/api/security/log-attempt', methods=['POST'])
def log_attempt():
    """Log a login attempt and check for brute force attacks"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400

        ip = data.get('ip', request.remote_addr)
        username = data.get('username', 'unknown')
        success = data.get('success', False)
        
        logger.debug(f"Received login attempt - IP: {ip}, Username: {username}, Success: {success}")
        
        if not success:
            current_time = time.time()
            attempts = security_state['failed_attempts'][ip]
            
            # Initialize if first attempt
            if not attempts['first_attempt']:
                attempts['first_attempt'] = current_time
                attempts['username'] = username
            
            attempts['count'] += 1
            attempts['attempts'].append(current_time)
            
            # Log the failed attempt
            log_security_event('failed_login', {
                'source_ip': ip,
                'username': username,
                'attempt_count': attempts['count'],
                'details': data.get('details', {})
            }, severity='warning')
            
            # Clean old attempts
            attempts['attempts'] = [t for t in attempts['attempts'] 
                                  if current_time - t < TIME_WINDOW]
            attempts['count'] = len(attempts['attempts'])
            
            if attempts['count'] >= ATTEMPT_THRESHOLD:
                # Add threat and alert
                threat = add_threat(
                    'brute_force',
                    {
                        'ip': ip,
                        'username': username,
                        'attempts': attempts['count'],
                        'window': f"{TIME_WINDOW/60} minutes",
                        'frequency': attempts['count'] / (TIME_WINDOW/60)
                    },
                    source_ip=ip
                )
                
                # Log the brute force detection
                log_security_event('brute_force_detected', {
                    'source_ip': ip,
                    'username': username,
                    'attempts': attempts['count'],
                    'action_taken': 'browser_kill'
                }, severity='critical')
                
                # Reset counter
                attempts['count'] = 0
                attempts['attempts'] = []
                
                return jsonify({
                    'status': 'alert_triggered',
                    'message': 'Brute force attack detected',
                    'threat': threat
                }), 403
            
            logger.info(f"Failed attempt recorded - IP: {ip}, Count: {attempts['count']}")
            
        return jsonify({
            'status': 'recorded',
            'attempts': security_state['failed_attempts'][ip]['count']
        })
    
    except Exception as e:
        logger.error(f"Error processing login attempt: {str(e)}", exc_info=True)
        return jsonify({'error': 'Internal server error'}), 500

def simulate_threats():
    """Simulate various security threats for testing"""
    threat_types = [
        'suspicious_activity',
        'system_warning',
        'authentication_failure'
    ]
    
    while True:
        try:
            # Randomly generate a threat
            threat_type = random.choice(threat_types)
            details = {
                'frequency': random.randint(1, 10),
                'source': f"192.168.1.{random.randint(2, 254)}",
                'target': random.choice(['auth_service', 'file_system', 'network']),
                'description': f"Simulated {threat_type} for testing"
            }
            
            add_threat(threat_type, details, source_ip=details['source'])
            
            # Sleep for random interval (30-90 seconds)
            time.sleep(random.randint(30, 90))
            
        except Exception as e:
            logger.error(f"Error in threat simulation: {str(e)}")
            time.sleep(60)

@app.route('/instagram')
def instagram_login():
    try:
        logger.info("Attempting to render Instagram login page")
        return render_template('instagram_login.html')
    except Exception as e:
        logger.error(f"Error rendering template: {str(e)}")
        return str(e), 500

def kill_chrome_process():
    """Kill all Chrome processes"""
    try:
        if sys.platform == 'win32':
            subprocess.run(['taskkill', '/F', '/IM', 'chrome.exe'], check=True)
        else:
            subprocess.run(['pkill', '-9', 'chrome'], check=True)
        return True
    except subprocess.CalledProcessError:
        logger.error("Failed to kill Chrome process")
        return False

@app.route('/api/security/kill-browser', methods=['POST'])
def terminate_browser():
    """Endpoint to terminate the browser process"""
    try:
        kill_chrome_process()
        event_details = {
            'action': 'browser_termination',
            'timestamp': datetime.now().isoformat(),
            'status': 'success'
        }
        security_logs['statistics']['browser_kills'] += 1
        security_logs['events'].append(event_details)
        save_security_logs(security_logs)
        
        # Broadcast the process termination
        broadcast_update('process_termination', {
            'type': 'process_termination',
            'details': {
                'process': 'browser',
                'reason': 'security_measure',
                'timestamp': event_details['timestamp']
            }
        })
        
        return jsonify({'status': 'success', 'message': 'Browser process terminated'})
    except Exception as e:
        logger.error(f"Error terminating browser: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/security/logs')
def get_security_logs():
    """Get security logs with optional filtering"""
    try:
        severity = request.args.get('severity')
        event_type = request.args.get('type')
        limit = int(request.args.get('limit', 100))
        
        filtered_logs = security_logs['events']
        
        if severity:
            filtered_logs = [log for log in filtered_logs if log['severity'] == severity]
        if event_type:
            filtered_logs = [log for log in filtered_logs if log['type'] == event_type]
            
        return jsonify({
            'logs': filtered_logs[:limit],
            'statistics': security_logs['statistics'],
            'total': len(filtered_logs)
        })
    except Exception as e:
        logger.error(f"Error retrieving logs: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

# WebSocket event handlers
@socketio.on('connect')
def handle_connect():
    logger.info('Client connected')
    emit('connection_status', {'status': 'connected'})

@socketio.on('disconnect')
def handle_disconnect():
    logger.info('Client disconnected')

def broadcast_update(event_type, data):
    """Broadcast updates to all connected clients"""
    try:
        logger.info(f"Broadcasting {event_type} event")
        logger.debug(f"Event data: {json.dumps(data, indent=2)}")
        socketio.emit(event_type, data)
        logger.info(f"Successfully broadcasted {event_type} event")
    except Exception as e:
        logger.error(f'Error broadcasting {event_type} event: {e}', exc_info=True)

if __name__ == "__main__":
    logger.info("Starting Security Monitoring System...")
    
    # Start threat simulation in background
    simulator = threading.Thread(target=simulate_threats, daemon=True)
    simulator.start()
    
    try:
        # Setup process and system monitoring
        process_monitor, observer = setup_system_monitoring(socketio)
        
        # Start the process monitor in a background thread
        process_thread = threading.Thread(target=process_monitor.monitor_processes, daemon=True)
        process_thread.start()
        
        # Start the file system observer
        observer.start()
        
        # Run the Flask app with SocketIO on port 5001
        socketio.run(app, host='0.0.0.0', port=5001, debug=True, allow_unsafe_werkzeug=True)
    except Exception as e:
        logger.error(f"Failed to start server: {str(e)}", exc_info=True)
        sys.exit(1)
    finally:
        if 'observer' in locals():
            observer.stop()
            observer.join() 