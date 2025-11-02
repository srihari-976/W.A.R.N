# Asset management API
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from backend.models.asset import Asset
from backend.models.user import User
from backend.db import db
import logging

logger = logging.getLogger(__name__)

assets_bp = Blueprint('assets', __name__)

@assets_bp.route('/', methods=['GET'])
@jwt_required()
def get_assets():
    """Get all assets"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        
        assets = Asset.query.paginate(page=page, per_page=per_page)
        
        return jsonify({
            'assets': [asset.to_dict() for asset in assets.items],
            'total': assets.total,
            'page': page,
            'per_page': per_page
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting assets: {str(e)}")
        return jsonify({'error': 'Error getting assets'}), 500

@assets_bp.route('/<int:asset_id>', methods=['GET'])
@jwt_required()
def get_asset(asset_id):
    """Get asset by ID"""
    try:
        asset = Asset.query.get(asset_id)
        if not asset:
            return jsonify({'error': 'Asset not found'}), 404
            
        return jsonify(asset.to_dict()), 200
        
    except Exception as e:
        logger.error(f"Error getting asset: {str(e)}")
        return jsonify({'error': 'Error getting asset'}), 500

@assets_bp.route('/', methods=['POST'])
@jwt_required()
def create_asset():
    """Create a new asset"""
    try:
        data = request.get_json()
        user_id = int(get_jwt_identity())
        
        asset = Asset(
            name=data['name'],
            type=data['type'],
            ip_address=data.get('ip_address'),
            status=data.get('status', 'active'),
            criticality=data.get('criticality', 'medium'),
            description=data.get('description')
        )
        asset.owner_id = user_id
        
        db.session.add(asset)
        db.session.commit()
        
        return jsonify(asset.to_dict()), 201
        
    except Exception as e:
        logger.error(f"Error creating asset: {str(e)}")
        return jsonify({'error': 'Error creating asset'}), 500

@assets_bp.route('/<int:asset_id>', methods=['PUT'])
@jwt_required()
def update_asset(asset_id):
    """Update an asset"""
    try:
        asset = Asset.query.get(asset_id)
        if not asset:
            return jsonify({'error': 'Asset not found'}), 404
            
        data = request.get_json()
        
        # Update fields
        if 'name' in data:
            asset.name = data['name']
        if 'type' in data:
            asset.type = data['type']
        if 'ip_address' in data:
            asset.ip_address = data['ip_address']
        if 'status' in data:
            asset.status = data['status']
        if 'criticality' in data:
            asset.criticality = data['criticality']
        if 'description' in data:
            asset.description = data['description']
            
        db.session.commit()
        
        return jsonify(asset.to_dict()), 200
        
    except Exception as e:
        logger.error(f"Error updating asset: {str(e)}")
        return jsonify({'error': 'Error updating asset'}), 500

@assets_bp.route('/<int:asset_id>', methods=['DELETE'])
@jwt_required()
def delete_asset(asset_id):
    """Delete an asset"""
    try:
        asset = Asset.query.get(asset_id)
        if not asset:
            return jsonify({'error': 'Asset not found'}), 404
            
        db.session.delete(asset)
        db.session.commit()
        
        return jsonify({'message': 'Asset deleted successfully'}), 200
        
    except Exception as e:
        logger.error(f"Error deleting asset: {str(e)}")
        return jsonify({'error': 'Error deleting asset'}), 500