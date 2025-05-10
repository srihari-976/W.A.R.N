from flask import Blueprint, request, jsonify
from backend.models.risk_score import RiskScore
from backend.models.asset import Asset
from backend.models.event import Event
from backend.services.risk.scoring import calculate_risk_score, get_risk_factors

# Create Blueprint for risk API
risk_bp = Blueprint('risk', __name__)

@risk_bp.route('/scores', methods=['GET'])
def get_risk_scores():
    """Get risk scores with optional filtering"""
    # Get query parameters
    asset_id = request.args.get('asset_id')
    event_id = request.args.get('event_id')
    min_score = request.args.get('min_score')
    max_score = request.args.get('max_score')
    limit = int(request.args.get('limit', 100))
    offset = int(request.args.get('offset', 0))
    
    # Build base query
    query = RiskScore.query
    
    # Apply filters
    if asset_id:
        query = query.filter_by(asset_id=asset_id)
    if event_id:
        query = query.filter_by(event_id=event_id)
    if min_score:
        query = query.filter(RiskScore.score >= float(min_score))
    if max_score:
        query = query.filter(RiskScore.score <= float(max_score))
    
    # Apply pagination
    risk_scores = query.offset(offset).limit(limit).all()
    
    return jsonify({
        'risk_scores': [score.to_dict() for score in risk_scores],
        'total': query.count(),
        'limit': limit,
        'offset': offset
    })

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
def get_available_risk_factors():
    """Get all available risk factors and their weights"""
    factors = get_risk_factors()
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