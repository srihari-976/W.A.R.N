import time
from datetime import datetime
import json
import requests
from flask import Flask, request, jsonify
from flask_cors import CORS
import logging
import sys

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('bruteforce_monitor.log')
    ]
)

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes
logger = logging.getLogger(__name__)

# Global dictionary to track login attempts
failed_attempts = {}
ATTEMPT_THRESHOLD = 5  # Number of failed attempts before alert
TIME_WINDOW = 600  # 10 minutes in seconds

@app.route('/')
def home():
    return jsonify({
        'status': 'running',
        'service': 'Brute Force Detection Agent',
        'endpoints': [
            '/api/security/test',
            '/api/security/status',
            '/api/security/log-attempt'
        ]
    })

@app.route('/api/security/test')
def test():
    """Test endpoint to verify the service is running"""
    logger.debug("Test endpoint called")
    return jsonify({
        'status': 'ok',
        'timestamp': datetime.now().isoformat(),
        'message': 'Brute force detection service is running'
    })

def clean_old_attempts():
    """Remove attempts older than TIME_WINDOW"""
    current_time = time.time()
    old_count = len(failed_attempts)
    cleaned = {
        ip: data for ip, data in failed_attempts.items()
        if current_time - data['first_attempt'] < TIME_WINDOW
    }
    if old_count != len(cleaned):
        logger.info(f"Cleaned {old_count - len(cleaned)} old entries")
    return cleaned

def send_alert(ip, username, attempt_count):
    try:
        url = 'http://localhost:3000/api/alerts/'
        alert_data = {
            'title': 'Potential Brute Force Attack Detected',
            'description': f"Multiple failed login attempts detected!\nIP: {ip}\nUsername: {username}\nAttempts: {attempt_count} in last {TIME_WINDOW/60} minutes",
            'severity': 'high',
            'timestamp': datetime.now().isoformat(),
            'type': 'security_alert',
            'metadata': {
                'ip_address': ip,
                'username': username,
                'attempt_count': attempt_count
            }
        }
        logger.debug(f"Sending alert to {url}: {json.dumps(alert_data, indent=2)}")
        response = requests.post(url, json=alert_data)
        response.raise_for_status()
        logger.info(f"Alert sent successfully for IP {ip}")
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to send alert to notification service: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error sending alert: {str(e)}")

@app.route('/api/security/log-attempt', methods=['POST'])
def log_attempt():
    try:
        data = request.get_json()
        if not data:
            logger.warning("Received request with no JSON data")
            return jsonify({'error': 'No data provided'}), 400

        ip = data.get('ip', request.remote_addr)
        username = data.get('username', 'unknown')
        success = data.get('success', False)
        
        logger.debug(f"Received login attempt - IP: {ip}, Username: {username}, Success: {success}")
        
        if not success:
            current_time = time.time()
            
            # Clean up old attempts
            global failed_attempts
            failed_attempts = clean_old_attempts()
            
            # Record new attempt
            if ip not in failed_attempts:
                failed_attempts[ip] = {
                    'count': 1,
                    'first_attempt': current_time,
                    'username': username,
                    'attempts': [current_time]
                }
            else:
                failed_attempts[ip]['count'] += 1
                failed_attempts[ip]['attempts'].append(current_time)
                
            attempt_count = failed_attempts[ip]['count']
            logger.info(f"Failed attempt recorded - IP: {ip}, Count: {attempt_count}")
            
            # Check if threshold is exceeded
            if attempt_count >= ATTEMPT_THRESHOLD:
                logger.warning(f"⚠️ Potential brute force attack detected from IP: {ip}")
                logger.warning(f"   Failed attempts: {attempt_count}")
                send_alert(ip, username, attempt_count)
                # Reset counter after alert
                failed_attempts[ip]['count'] = 0
                return jsonify({
                    'status': 'alert_triggered',
                    'message': 'Brute force attack detected',
                    'attempts': attempt_count
                }), 403
            
        return jsonify({
            'status': 'recorded',
            'attempts': failed_attempts.get(ip, {}).get('count', 0)
        })
    except Exception as e:
        logger.error(f"Error processing login attempt: {str(e)}", exc_info=True)
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/security/status')
def get_status():
    try:
        current_attempts = clean_old_attempts()
        status_data = {
            'active': True,
            'tracking': {
                ip: {
                    'count': data['count'],
                    'username': data['username'],
                    'first_attempt': datetime.fromtimestamp(data['first_attempt']).isoformat(),
                    'attempts': [datetime.fromtimestamp(t).isoformat() for t in data['attempts']]
                }
                for ip, data in current_attempts.items()
            },
            'threshold': ATTEMPT_THRESHOLD,
            'window': TIME_WINDOW
        }
        return jsonify(status_data)
    except Exception as e:
        logger.error(f"Error getting status: {str(e)}", exc_info=True)
        return jsonify({'error': 'Internal server error'}), 500

if __name__ == "__main__":
    PORT = 5001  # Changed port to avoid conflict
    logger.info("Starting Brute Force Detection Agent...")
    logger.info(f"Monitoring for failed login attempts (Threshold: {ATTEMPT_THRESHOLD} attempts in {TIME_WINDOW/60} minutes)")
    logger.info("Available endpoints:")
    logger.info(f"  - http://localhost:{PORT}/ (API info)")
    logger.info(f"  - http://localhost:{PORT}/api/security/test (Service test)")
    logger.info(f"  - http://localhost:{PORT}/api/security/status (Current status)")
    logger.info(f"  - http://localhost:{PORT}/api/security/log-attempt (Log attempts)")
    
    try:
        app.run(host='0.0.0.0', port=PORT, debug=True)
        except Exception as e:
        logger.error(f"Failed to start server: {str(e)}", exc_info=True)
        sys.exit(1)