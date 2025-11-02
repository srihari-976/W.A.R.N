python# Endpoint agent API
from flask import request, jsonify, current_app
from . import api_bp
from ..models.asset import Asset
from ..endpoint_agent.comms import process_agent_data
import logging

logger = logging.getLogger(__name__)

@api_bp.route('/agent/register', methods=['POST'])
def register_agent():
    """Register a new endpoint agent"""
    try:
        data = request.get_json()
        # Validate required fields
        if not all(k in data for k in ['hostname', 'os', 'ip_address', 'agent_version']):
            return jsonify({'error': 'Missing required fields'}), 400
            
        # Check if agent already exists
        asset = Asset.query.filter_by(hostname=data['hostname']).first()
        if asset:
            # Update existing asset
            asset.update_from_dict(data)
            message = 'Agent updated successfully'
        else:
            # Create new asset
            asset = Asset(
                hostname=data['hostname'],
                os_type=data['os'],
                ip_address=data['ip_address'],
                agent_version=data['agent_version'],
                asset_type='endpoint',
                status='active'
            )
            asset.save()
            message = 'Agent registered successfully'
            
        return jsonify({
            'message': message,
            'asset_id': asset.id,
            'configuration': current_app.config.get('AGENT_CONFIG', {})
        }), 200
    except Exception as e:
        logger.error(f"Error registering agent: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@api_bp.route('/agent/heartbeat', methods=['POST'])
def agent_heartbeat():
    """Receive heartbeat from endpoint agent"""
    try:
        data = request.get_json()
        asset_id = data.get('asset_id')
        
        if not asset_id:
            return jsonify({'error': 'Missing asset ID'}), 400
            
        asset = Asset.query.get(asset_id)
        if not asset:
            return jsonify({'error': 'Unknown agent'}), 404
            
        # Update last seen timestamp
        asset.update_last_seen()
        
        # Return any pending commands for the agent
        pending_commands = asset.get_pending_commands()
        
        return jsonify({
            'status': 'ok',
            'commands': pending_commands
        }), 200
    except Exception as e:
        logger.error(f"Error processing heartbeat: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@api_bp.route('/agent/data', methods=['POST'])
def receive_agent_data():
    """Receive and process data from endpoint agent"""
    try:
        data = request.get_json()
        asset_id = data.get('asset_id')
        telemetry = data.get('telemetry')
        
        if not asset_id or not telemetry:
            return jsonify({'error': 'Missing required data'}), 400
            
        asset = Asset.query.get(asset_id)
        if not asset:
            return jsonify({'error': 'Unknown agent'}), 404
            
        # Process the received telemetry data
        result = process_agent_data(asset, telemetry)
        
        return jsonify({'status': 'ok', 'processed': result}), 200
    except Exception as e:
        logger.error(f"Error processing agent data: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500