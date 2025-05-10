from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from backend.models.event import SecurityEvent
from backend.models.user import User
from backend.db import db
from backend.services.event_processor import EventProcessor
from flask import current_app
import logging

logger = logging.getLogger(__name__)

events_bp = Blueprint('events', __name__)

def get_event_processor():
    return EventProcessor(current_app.socketio)

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
@jwt_required()
def create_event():
    """Create a new event"""
    try:
        data = request.get_json()
        
        # Process event using EventProcessor
        event_processor = get_event_processor()
        event, risk_score = event_processor.process_event(data)
        
        return jsonify({
            'event': event.to_dict(),
            'risk_score': risk_score
        }), 201
        
    except Exception as e:
        logger.error(f"Error creating event: {str(e)}")
        return jsonify({'error': 'Error creating event'}), 500

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
        
        # Recalculate risk score after update
        event_processor = get_event_processor()
        risk_score = event_processor.process_event(event.to_dict())
        
        return jsonify({
            'event': event.to_dict(),
            'risk_score': risk_score
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