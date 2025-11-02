# Alert management API
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from backend.models.alert import Alert
from backend.models.user import User
from backend.db import db
from backend.services.threat_detector import threat_detector
import logging

logger = logging.getLogger(__name__)

alerts_bp = Blueprint('alerts', __name__)

@alerts_bp.route('/', methods=['GET'])
def get_alerts():
    """Get real alerts from threat detection system"""
    try:
        # Ensure query works even when table is empty; return empty list, not 500
        alerts = Alert.query.order_by(Alert.timestamp.desc()).limit(50).all()
        
        return jsonify({
            'alerts': [{
                'id': alert.id,
                'type': alert.type,
                'severity': alert.severity,
                'risk_score': alert.risk_score,
                'threat_level': alert.threat_level,
                'techniques': alert.techniques,
                'analysis': alert.analysis,
                'is_anomaly': alert.is_anomaly,
                'timestamp': alert.timestamp.isoformat(),
                'status': alert.status
            } for alert in alerts],
            'total': len(alerts)
        }), 200
        
    except Exception as e:
        # Log full exception details and return safe empty payload
        logger.exception("Error getting alerts")
        return jsonify({'alerts': [], 'total': 0, 'error': str(e)}), 500

@alerts_bp.route('/<int:alert_id>', methods=['GET'])
@jwt_required()
def get_alert(alert_id):
    """Get alert by ID"""
    try:
        alert = Alert.get_by_id(alert_id)
        if not alert:
            return jsonify({'error': 'Alert not found'}), 404
            
        return jsonify(alert.to_dict()), 200
        
    except Exception as e:
        logger.error(f"Error getting alert: {str(e)}")
        return jsonify({'error': 'Error getting alert'}), 500

@alerts_bp.route('/', methods=['POST'])
@jwt_required()
def create_alert():
    """Create a new alert"""
    try:
        data = request.get_json()
        user_id = int(get_jwt_identity())
        
        alert = Alert(
            type=data['type'],
            severity=data['severity'],
            description=data['description'],
            asset_id=data.get('asset_id'),
            created_by_id=user_id
        )
        
        alert.save()
        
        return jsonify(alert.to_dict()), 201
        
    except Exception as e:
        logger.error(f"Error creating alert: {str(e)}")
        return jsonify({'error': 'Error creating alert'}), 500

@alerts_bp.route('/<int:alert_id>', methods=['PUT'])
@jwt_required()
def update_alert(alert_id):
    """Update an alert"""
    try:
        alert = Alert.get_by_id(alert_id)
        if not alert:
            return jsonify({'error': 'Alert not found'}), 404
            
        data = request.get_json()
        alert.update(**data)
        
        return jsonify(alert.to_dict()), 200
        
    except Exception as e:
        logger.error(f"Error updating alert: {str(e)}")
        return jsonify({'error': 'Error updating alert'}), 500

@alerts_bp.route('/<int:alert_id>/status', methods=['PUT'])
@jwt_required()
def update_alert_status(alert_id):
    """Update only the status of an alert (frontend contract)"""
    try:
        alert = Alert.get_by_id(alert_id)
        if not alert:
            return jsonify({'error': 'Alert not found'}), 404

        data = request.get_json() or {}
        new_status = data.get('status')
        if not new_status:
            return jsonify({'error': 'Missing status'}), 400

        # Basic allow-list of statuses (fallback if config not available)
        allowed = {'new', 'in_progress', 'resolved', 'false_positive', 'ignored', 'active'}
        if new_status not in allowed:
            return jsonify({'error': 'Invalid status'}), 400

        alert.status = new_status
        db.session.commit()
        return jsonify({'id': alert.id, 'status': alert.status}), 200
    except Exception as e:
        logger.error(f"Error updating alert status: {str(e)}")
        return jsonify({'error': 'Error updating alert status'}), 500

@alerts_bp.route('/<int:alert_id>', methods=['DELETE'])
@jwt_required()
def delete_alert(alert_id):
    """Delete an alert"""
    try:
        alert = Alert.get_by_id(alert_id)
        if not alert:
            return jsonify({'error': 'Alert not found'}), 404
            
        alert.delete()
        
        return jsonify({'message': 'Alert deleted successfully'}), 200
        
    except Exception as e:
        logger.error(f"Error deleting alert: {str(e)}")
        return jsonify({'error': 'Error deleting alert'}), 500