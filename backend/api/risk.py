from flask import Blueprint, request, jsonify
from backend.services.threat_detector import threat_detector
from backend.models.alert import Alert
from backend.models.risk_score import RiskScore, calculate_risk_score
from backend.models.asset import Asset
from backend.models.event import Event

# Create Blueprint for risk API
risk_bp = Blueprint('risk', __name__)

@risk_bp.route('/scores', methods=['GET'])
def get_risk_scores():
    """Get real risk scores from threat detection"""
    try:
        alerts = Alert.query.order_by(Alert.timestamp.desc()).limit(20).all()
        
        risk_data = []
        for alert in alerts:
            risk_data.append({
                'id': alert.id,
                'score': alert.risk_score,
                'threat_level': alert.threat_level,
                'techniques': alert.techniques,
                'timestamp': alert.timestamp.isoformat(),
                'category': 'high' if alert.risk_score >= 70 else 'medium' if alert.risk_score >= 40 else 'low'
            })
        
        return jsonify({
            'risk_scores': risk_data,
            'total': len(risk_data),
            'average_score': sum(r['score'] for r in risk_data) / len(risk_data) if risk_data else 0
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@risk_bp.route('/scores/<score_id>', methods=['GET'])
def get_risk_score(score_id):
    """Get details of a specific risk score"""
    risk_score = RiskScore.query.get_or_404(score_id)
    return jsonify(risk_score.to_dict())

@risk_bp.route('/scores', methods=['POST'])
def create_risk_score():
    """Calculate and create a new risk score"""
    data = request.json
    
    # Validate that we have either asset_id or event_id
    if not data.get('asset_id') and not data.get('event_id'):
        return jsonify({'error': 'Either asset_id or event_id is required'}), 400
    
    # Get asset and event information if available
    asset = None
    event = None
    
    if data.get('asset_id'):
        asset = Asset.query.get_or_404(data['asset_id'])
    
    if data.get('event_id'):
        event = Event.query.get_or_404(data['event_id'])
    
    # Calculate risk score
    score_result = calculate_risk_score(
        asset=asset,
        event=event,
        threat_info=data.get('threat_info', {}),
        context=data.get('context', {})
    )
    
    # Create new risk score record
    new_score = RiskScore(
        score=score_result['score'],
        asset_id=data.get('asset_id'),
        event_id=data.get('event_id'),
        factors=score_result['factors'],
        category=score_result['category'],
        timestamp=score_result['timestamp']
    )
    
    # Save to database
    new_score.save()
    
    return jsonify(new_score.to_dict()), 201

@risk_bp.route('/factors', methods=['GET'])
def get_risk_factors():
    """Get MITRE ATT&CK technique risk factors"""
    factors = {
        'T1059': {'weight': 8.0, 'name': 'Command and Scripting Interpreter'},
        'T1071': {'weight': 7.0, 'name': 'Application Layer Protocol'},
        'T1547': {'weight': 7.0, 'name': 'Boot or Logon Autostart Execution'},
        'T1566': {'weight': 8.5, 'name': 'Phishing'},
        'T1486': {'weight': 9.5, 'name': 'Data Encrypted for Impact'}
    }
    return jsonify({'risk_factors': factors})

@risk_bp.route('/assets/highest', methods=['GET'])
def get_highest_risk_assets():
    """Get assets with the highest risk scores"""
    limit = int(request.args.get('limit', 10))
    
    # Query assets with their latest risk scores
    high_risk_assets = Asset.query\
        .join(RiskScore, Asset.id == RiskScore.asset_id)\
        .order_by(RiskScore.score.desc())\
        .limit(limit)\
        .all()
    
    result = []
    for asset in high_risk_assets:
        # Get the latest risk score for this asset
        latest_score = RiskScore.query\
            .filter_by(asset_id=asset.id)\
            .order_by(RiskScore.timestamp.desc())\
            .first()
        
        result.append({
            'asset': asset.to_dict(),
            'risk_score': latest_score.to_dict() if latest_score else None
        })
    
    return jsonify({'high_risk_assets': result, 'count': len(result)})

@risk_bp.route('/threshold/check', methods=['POST'])
def check_risk_threshold():
    """Check if a given risk score exceeds thresholds for automated actions"""
    data = request.json
    
    # Validate required fields
    if 'score' not in data:
        return jsonify({'error': 'Score is required'}), 400
    
    score = float(data['score'])
    
    # Define response based on risk score thresholds
    response = {
        'score': score,
        'category': 'unknown',
        'actions_required': False,
        'recommended_actions': []
    }
    
    # Low risk classification
    if score < 30:
        response['category'] = 'low'
        response['actions_required'] = False
        response['recommended_actions'] = [
            'log',
            'monitor'
        ]
    
    # Medium risk classification
    elif 30 <= score < 70:
        response['category'] = 'medium'
        response['actions_required'] = True
        response['recommended_actions'] = [
            'alert',
            'increase_monitoring',
            'prepare_response'
        ]
    
    # High risk classification
    else:
        response['category'] = 'high'
        response['actions_required'] = True
        response['recommended_actions'] = [
            'isolate_host',
            'block_ip',
            'terminate_process',
            'alert_critical'
        ]
    
    return jsonify(response)