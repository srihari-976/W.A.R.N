from flask import Blueprint, request, jsonify
from backend.models.security_event import SecurityEvent, BlockedIP, LockedAccount
from backend.db import db
import logging
import re
from datetime import datetime

logger = logging.getLogger(__name__)

security_bp = Blueprint('security', __name__)

@security_bp.route('/security/scan-url', methods=['POST'])
def scan_url():
    """Scan URL for phishing threats"""
    try:
        data = request.get_json()
        url = data.get('url', '')
        
        # Simple phishing detection logic
        phishing_indicators = [
            'phishing', 'fake', 'scam', 'suspicious', 'malicious',
            'login-verify', 'account-suspended', 'urgent-action'
        ]
        
        is_phishing = any(indicator in url.lower() for indicator in phishing_indicators)
        risk_level = 'high' if is_phishing else 'low'
        confidence = 0.95 if is_phishing else 0.85
        
        # Log the scan
        event = SecurityEvent(
            event_type='phishing_scan',
            source_ip=request.remote_addr,
            url=url,
            severity=risk_level,
            description=f"URL scan: {'Phishing detected' if is_phishing else 'Safe URL'}"
        )
        db.session.add(event)
        db.session.commit()
        
        result = {
            'is_phishing': is_phishing,
            'risk_level': risk_level,
            'confidence': confidence,
            'threat_indicators': phishing_indicators if is_phishing else []
        }
        
        return jsonify(result), 200
        
    except Exception as e:
        logger.error(f"Error scanning URL: {e}")
        return jsonify({'error': 'Scan failed'}), 500

@security_bp.route('/security/blocked-ips', methods=['GET'])
def get_blocked_ips():
    """Get list of blocked IP addresses"""
    try:
        blocked_ips = BlockedIP.query.all()
        return jsonify({
            'blocked_ips': [ip.to_dict() for ip in blocked_ips]
        }), 200
    except Exception as e:
        logger.error(f"Error getting blocked IPs: {e}")
        return jsonify({'error': 'Failed to get blocked IPs'}), 500

@security_bp.route('/security/unblock-ip', methods=['POST'])
def unblock_ip():
    """Unblock an IP address"""
    try:
        data = request.get_json()
        ip_address = data.get('ip_address')
        
        blocked_ip = BlockedIP.query.filter_by(address=ip_address).first()
        if blocked_ip:
            db.session.delete(blocked_ip)
            db.session.commit()
            
        return jsonify({'message': f'IP {ip_address} unblocked'}), 200
    except Exception as e:
        logger.error(f"Error unblocking IP: {e}")
        return jsonify({'error': 'Failed to unblock IP'}), 500

@security_bp.route('/security/locked-accounts', methods=['GET'])
def get_locked_accounts():
    """Get list of locked accounts"""
    try:
        locked_accounts = LockedAccount.query.all()
        return jsonify({
            'locked_accounts': [account.to_dict() for account in locked_accounts]
        }), 200
    except Exception as e:
        logger.error(f"Error getting locked accounts: {e}")
        return jsonify({'error': 'Failed to get locked accounts'}), 500

@security_bp.route('/security/unlock-account', methods=['POST'])
def unlock_account():
    """Unlock a user account"""
    try:
        data = request.get_json()
        username = data.get('username')
        
        locked_account = LockedAccount.query.filter_by(username=username).first()
        if locked_account:
            db.session.delete(locked_account)
            db.session.commit()
            
        return jsonify({'message': f'Account {username} unlocked'}), 200
    except Exception as e:
        logger.error(f"Error unlocking account: {e}")
        return jsonify({'error': 'Failed to unlock account'}), 500

@security_bp.route('/security/events', methods=['GET'])
def get_security_events():
    """Get recent security events"""
    try:
        events = SecurityEvent.query.order_by(SecurityEvent.timestamp.desc()).limit(50).all()
        return jsonify({
            'events': [event.to_dict() for event in events]
        }), 200
    except Exception as e:
        logger.error(f"Error getting security events: {e}")
        return jsonify({'error': 'Failed to get events'}), 500