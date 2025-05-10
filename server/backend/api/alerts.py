# Alert management API
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from backend.models.alert import Alert
from backend.models.user import User
from backend.db import db
import logging

logger = logging.getLogger(__name__)

alerts_bp = Blueprint('alerts', __name__)

@alerts_bp.route('/', methods=['GET'])
@jwt_required()
def get_alerts():
    """Get all alerts"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        
        alerts, total = Alert.get_all(
            filters=request.args.to_dict(),
            page=page,
            per_page=per_page
        )
        
        return jsonify({
            'alerts': [alert.to_dict() for alert in alerts],
            'total': total,
            'page': page,
            'per_page': per_page
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting alerts: {str(e)}")
        return jsonify({'error': 'Error getting alerts'}), 500

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