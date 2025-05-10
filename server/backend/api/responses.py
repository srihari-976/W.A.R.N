
from flask import Blueprint, request, jsonify
from backend.models.response import Response
from backend.models.event import Event
from backend.models.asset import Asset
from backend.services.response.actions import execute_response_action
from backend.services.response.automation import create_automation_workflow
from backend.services.response.orchestrator import ResponseOrchestrator
from backend.services.response.actions import ActionExecutor
from backend.utils.logging import get_logger

logger = get_logger(__name__)

# Create Blueprint for responses API
responses_bp = Blueprint('responses', __name__)

# Initialize response components
response_orchestrator = ResponseOrchestrator()
action_executor = ActionExecutor()

@responses_bp.route('/responses', methods=['GET'])
def get_responses():
    """Get list of response actions"""
    try:
        responses = Response.query.all()
        return jsonify({
            'responses': [response.to_dict() for response in responses]
        }), 200
    except Exception as e:
        logger.error(f"Error retrieving responses: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@responses_bp.route('/responses/<response_id>', methods=['GET'])
def get_response(response_id):
    """Get detailed information about a specific response action"""
    try:
        response = Response.query.get(response_id)
        
        if not response:
            return jsonify({'error': 'Response not found'}), 404
            
        return jsonify(response.to_dict()), 200
    except Exception as e:
        logger.error(f"Error retrieving response {response_id}: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@responses_bp.route('/responses', methods=['POST'])
def create_response():
    """Create a new response action"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['name', 'action_type', 'parameters']
        if not all(field in data for field in required_fields):
            return jsonify({'error': 'Missing required fields'}), 400
            
        # Create response
        response = Response(
            name=data['name'],
            action_type=data['action_type'],
            parameters=data['parameters'],
            status='active'
        )
        response.save()
        
        return jsonify({
            'message': 'Response created successfully',
            'response': response.to_dict()
        }), 201
    except Exception as e:
        logger.error(f"Error creating response: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@responses_bp.route('/responses/<response_id>', methods=['PUT'])
def update_response(response_id):
    """Update an existing response action"""
    try:
        response = Response.query.get(response_id)
        
        if not response:
            return jsonify({'error': 'Response not found'}), 404
            
        data = request.get_json()
        
        # Update fields
        if 'name' in data:
            response.name = data['name']
        if 'parameters' in data:
            response.parameters = data['parameters']
        if 'status' in data:
            response.status = data['status']
            
        response.save()
        
        return jsonify({
            'message': 'Response updated successfully',
            'response': response.to_dict()
        }), 200
    except Exception as e:
        logger.error(f"Error updating response {response_id}: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@responses_bp.route('/responses/<response_id>', methods=['DELETE'])
def delete_response(response_id):
    """Delete a response action"""
    try:
        response = Response.query.get(response_id)
        
        if not response:
            return jsonify({'error': 'Response not found'}), 404
            
        response.delete()
        
        return jsonify({
            'message': 'Response deleted successfully'
        }), 200
    except Exception as e:
        logger.error(f"Error deleting response {response_id}: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@responses_bp.route('/responses/execute', methods=['POST'])
def execute_response():
    """Execute a response action"""
    try:
        data = request.get_json()
        
        # Validate required fields
        if not all(k in data for k in ['response_id', 'context']):
            return jsonify({'error': 'Missing required fields'}), 400
            
        response = Response.query.get(data['response_id'])
        
        if not response:
            return jsonify({'error': 'Response not found'}), 404
            
        # Execute response
        result = action_executor.execute(
            response.action_type,
            response.parameters,
            data['context']
        )
        
        return jsonify({
            'message': 'Response executed successfully',
            'result': result
        }), 200
    except Exception as e:
        logger.error(f"Error executing response: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@responses_bp.route('/responses/orchestrate', methods=['POST'])
def orchestrate_responses():
    """Orchestrate multiple response actions based on alert context"""
    try:
        data = request.get_json()
        
        # Validate required fields
        if 'alert_id' not in data:
            return jsonify({'error': 'Missing alert ID'}), 400
            
        # Get orchestrated responses
        responses = response_orchestrator.get_responses(data['alert_id'])
        
        return jsonify({
            'responses': [response.to_dict() for response in responses]
        }), 200
    except Exception as e:
        logger.error(f"Error orchestrating responses: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@responses_bp.route('/responses/automation', methods=['POST'])
def create_automation():
    """Create a new automation workflow for response actions"""
    data = request.json
    
    # Validate required fields
    required_fields = ['name', 'trigger_conditions', 'actions']
    for field in required_fields:
        if field not in data:
            return jsonify({'error': f'Missing required field: {field}'}), 400
    
    # Create automation workflow
    workflow = create_automation_workflow(
        name=data['name'],
        description=data.get('description', ''),
        trigger_conditions=data['trigger_conditions'],
        actions=data['actions'],
        enabled=data.get('enabled', True)
    )
    
    return jsonify(workflow), 201

@responses_bp.route('/responses/actions', methods=['GET'])
def get_available_actions():
    """Get all available response actions and their parameters"""
    # This would typically come from a configuration or database
    available_actions = [
        {
            'type': 'block_ip',
            'description': 'Block an IP address at the firewall',
            'parameters': ['ip_address', 'duration'],
            'supported_assets': ['firewall', 'network'],
            'risk_level': 'high'
        },
        {
            'type': 'isolate_host',
            'description': 'Network isolation of a host',
            'parameters': ['host_id'],
            'supported_assets': ['endpoint', 'server'],
            'risk_level': 'high'
        },
        {
            'type': 'terminate_process',
            'description': 'Terminate a process on a host',
            'parameters': ['host_id', 'process_id'],
            'supported_assets': ['endpoint', 'server'],
            'risk_level': 'medium'
        },
        {
            'type': 'reset_credentials',
            'description': 'Reset user credentials',
            'parameters': ['user_id'],
            'supported_assets': ['user'],
            'risk_level': 'medium'
        }
    ]
    
    return jsonify({'available_actions': available_actions})