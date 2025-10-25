from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from backend.models.security_event import SecurityEvent
from backend.models.user import User
from backend.db import db
from backend.services.event_processor import event_processor
from flask import current_app
import logging

logger = logging.getLogger(__name__)

events_bp = Blueprint('events', __name__)



@events_bp.route('/', methods=['GET'])
@jwt_required()
def get_events():
    """Get all events"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        
        events, total = SecurityEvent.get_all(
            filters=request.args.to_dict(),
            page=page,
            per_page=per_page
        )
        
        return jsonify({
            'events': [event.to_dict() for event in events],
            'total': total,
            'page': page,
            'per_page': per_page
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting events: {str(e)}")
        return jsonify({'error': 'Error getting events'}), 500

@events_bp.route('/<int:event_id>', methods=['GET'])
@jwt_required()
def get_event(event_id):
    """Get event by ID"""
    try:
        event = SecurityEvent.get_by_id(event_id)
        if not event:
            return jsonify({'error': 'Event not found'}), 404
            
        return jsonify(event.to_dict()), 200
        
    except Exception as e:
        logger.error(f"Error getting event: {str(e)}")
        return jsonify({'error': 'Error getting event'}), 500

@events_bp.route('/', methods=['POST'])
def create_event():
    """Create and analyze security event with real threat detection"""
    try:
        data = request.get_json() or {}

        # Map incoming fields to model schema
        # SecurityEvent requires source_ip (non-null). Fall back to client IP if not provided.
        source_ip = data.get('source_ip') or request.remote_addr or '127.0.0.1'

        event = SecurityEvent(
            event_type=data.get('event_type', 'unknown'),
            source_ip=source_ip,
            target_ip=data.get('target_ip'),
            username=data.get('username'),
            url=data.get('url'),
            severity=data.get('severity', 'medium'),
            description=data.get('description', '')
        )
        event.save()

        # Process through real threat detection pipeline
        import asyncio
        detection_result = asyncio.run(event_processor.process_event({
            'id': event.id,
            'process_name': data.get('process_name', ''),
            'command_line': data.get('command_line', ''),
            'network_connections': data.get('network_connections', []),
            'file_operations': data.get('file_operations', []),
            'registry_changes': data.get('registry_changes', []),
            'timestamp': event.timestamp.isoformat()
        }))

        return jsonify({
            'event': event.to_dict(),
            'detection_result': detection_result,
            'message': 'Event processed with real threat detection'
        }), 201

    except Exception as e:
        logger.error(f"Error processing event: {str(e)}")
        return jsonify({'error': str(e)}), 500

@events_bp.route('/<int:event_id>', methods=['PUT'])
@jwt_required()
def update_event(event_id):
    """Update an event"""
    try:
        event = SecurityEvent.get_by_id(event_id)
        if not event:
            return jsonify({'error': 'Event not found'}), 404
            
        data = request.get_json()
        event.update(**data)
        
        # Recalculate risk with real detection
        import asyncio
        detection_result = asyncio.run(event_processor.process_event(event.to_dict()))
        # Extract a risk score if provided by the detection pipeline
        risk_score = None
        try:
            if isinstance(detection_result, dict):
                risk_score = detection_result.get('risk_score')
        except Exception:
            pass
        
        return jsonify({
            'event': event.to_dict(),
            'risk_score': risk_score,
            'detection_result': detection_result
        }), 200
        
    except Exception as e:
        logger.error(f"Error updating event: {str(e)}")
        return jsonify({'error': 'Error updating event'}), 500

@events_bp.route('/<int:event_id>', methods=['DELETE'])
@jwt_required()
def delete_event(event_id):
    """Delete an event"""
    try:
        event = SecurityEvent.get_by_id(event_id)
        if not event:
            return jsonify({'error': 'Event not found'}), 404
            
        event.delete()
        
        # Notify clients about event deletion
        current_app.socketio.emit('event_deleted', {'event_id': event_id})
        
        return jsonify({'message': 'Event deleted successfully'}), 200
        
    except Exception as e:
        logger.error(f"Error deleting event: {str(e)}")
        return jsonify({'error': 'Error deleting event'}), 500