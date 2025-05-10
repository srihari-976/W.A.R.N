"""
/backend/api/ml.py - Machine learning API
Handles endpoints for ML model management, training, and inference.
"""

from flask import Blueprint, request, jsonify
from models.ml_model import MLModel
from services.ml.anomaly import AnomalyDetector, detect_anomalies
from services.ml.classifier import SecurityClassifier
from services.ml.feature_extraction import FeatureExtractor
from services.llm.fine_tuning import FineTuningManager
from services.llm.inference import analyze_event_context
from . import api_bp
import logging
import numpy as np
import os

logger = logging.getLogger(__name__)

# Create Blueprint for ML API
ml_bp = Blueprint('ml', __name__)

# Initialize ML components
anomaly_detector = AnomalyDetector()
threat_classifier = SecurityClassifier()
feature_extractor = FeatureExtractor()
fine_tuning_manager = FineTuningManager(
    base_model='llama2-7b',
    output_dir=os.path.join('models', 'llm'),
    use_peft=True,
    use_lora=True
)

@ml_bp.route('/ml/models', methods=['GET'])
def get_models():
    """Get list of available ML models"""
    try:
        models = MLModel.query.all()
        return jsonify({
            'models': [model.to_dict() for model in models]
        }), 200
    except Exception as e:
        logger.error(f"Error retrieving ML models: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@ml_bp.route('/ml/models/<model_id>', methods=['GET'])
def get_model(model_id):
    """Get detailed information about a specific ML model"""
    try:
        model = MLModel.query.get(model_id)
        
        if not model:
            return jsonify({'error': 'Model not found'}), 404
            
        return jsonify(model.to_dict()), 200
    except Exception as e:
        logger.error(f"Error retrieving model {model_id}: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@ml_bp.route('/ml/models', methods=['POST'])
def create_model():
    """Create a new ML model"""
    data = request.json
    
    # Validate required fields
    required_fields = ['name', 'model_type', 'description']
    for field in required_fields:
        if field not in data:
            return jsonify({'error': f'Missing required field: {field}'}), 400
    
    # Create new model
    new_model = MLModel(
        name=data['name'],
        model_type=data['model_type'],
        description=data['description'],
        parameters=data.get('parameters', {}),
        performance_metrics=data.get('performance_metrics', {}),
        features=data.get('features', []),
        status='created'
    )
    
    # Save to database
    new_model.save()
    
    return jsonify(new_model.to_dict()), 201

@ml_bp.route('/ml/models/<model_id>/train', methods=['POST'])
def train_model(model_id):
    """Train a specific ML model"""
    model = MLModel.query.get_or_404(model_id)
    data = request.json
    
    # Update model status
    model.update(status='training')
    
    # Train model based on model type
    if model.model_type == 'anomaly_detection':
        training_data = data.get('training_data', [])
        params = data.get('parameters', {})
        
        # Extract features for training
        features = np.vstack([
            anomaly_detector.extract_features(event)[0]
            for event in training_data
        ])
        
        # Train the model
        anomaly_detector.fit(features)
        
        # Save model if path is provided
        if model.model_path:
            anomaly_detector.save_model(model.model_path)
        
        model.update(
            status='trained',
            performance_metrics={'contamination': anomaly_detector.model.contamination}
        )
    elif model.model_type == 'classifier':
        training_data = data.get('training_data', [])
        labels = data.get('labels', [])
        params = data.get('parameters', {})
        
        # Extract features for training
        features = np.vstack([
            threat_classifier.extract_features(event)[0]
            for event in training_data
        ])
        
        # Convert labels to numpy array
        labels = np.array(labels)
        
        # Train the model
        threat_classifier.train(features, labels)
        
        # Save model if path is provided
        if model.model_path:
            threat_classifier.save_model(model.model_path)
        
        # Evaluate model performance
        metrics = threat_classifier.evaluate(features, labels)
        
        model.update(
            status='trained',
            performance_metrics=metrics
        )
    elif model.model_type == 'llm':
        training_data = data.get('training_data', [])
        
        # Run fine-tuning
        model_path = fine_tuning_manager.run_fine_tuning(
            training_data=training_data,
            num_epochs=data.get('num_epochs', 3),
            learning_rate=data.get('learning_rate', 2e-5),
            batch_size=data.get('batch_size', 4)
        )
        
        # Evaluate model
        metrics = fine_tuning_manager.evaluate_model(model_path, training_data[:10])
        
        model.update(
            status='trained',
            model_path=model_path,
            performance_metrics=metrics
        )
    else:
        return jsonify({'error': 'Unsupported model type'}), 400
    
    return jsonify(model.to_dict())

@ml_bp.route('/ml/models/<model_id>/predict', methods=['POST'])
def predict(model_id):
    """Make predictions using a trained model"""
    model = MLModel.query.get_or_404(model_id)
    
    # Check if model is trained
    if model.status != 'trained':
        return jsonify({'error': 'Model is not trained yet'}), 400
    
    data = request.json
    input_data = data.get('input_data', [])
    
    # Generate predictions based on model type
    if model.model_type == 'anomaly_detection':
        results = detect_anomalies(input_data, model.model_path)
    elif model.model_type == 'classifier':
        results = []
        for event in input_data:
            prediction, confidence = threat_classifier.predict(event)
            results.append({
                'prediction': prediction,
                'confidence': confidence,
                'event': event
            })
    elif model.model_type == 'llm':
        text_input = data.get('text', '')
        results = analyze_event_context(text_input, model_id)
    else:
        return jsonify({'error': 'Unsupported model type'}), 400
    
    return jsonify({'predictions': results})

@ml_bp.route('/ml/features/extract', methods=['POST'])
def extract_event_features():
    """Extract features from security events"""
    try:
        data = request.json
        events = data.get('events', [])
        feature_types = data.get('feature_types', ['all'])
        
        # Extract features using the feature extractor
        features = feature_extractor.extract_features(events)
        
        return jsonify({
            'features': features.tolist(),
            'feature_names': feature_extractor.get_feature_names()
        }), 200
    except Exception as e:
        logger.error(f"Error extracting features: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

    data = request.json
    events = data.get('events', [])
    feature_types = data.get('feature_types', ['all'])
    
    features = extract_features(events, feature_types)
    
    return jsonify({'features': features})

@api_bp.route('/ml/detect-anomalies', methods=['POST'])
def detect_anomalies():
    """Detect anomalies in event data"""
    try:
        data = request.get_json()
        
        # Validate required fields
        if 'events' not in data:
            return jsonify({'error': 'Missing events data'}), 400
            
        # Extract features
        features = feature_extractor.extract_features(data['events'])
        
        # Detect anomalies
        anomalies = anomaly_detector.detect_anomalies(features)
        
        return jsonify({
            'anomalies': bool(anomalies[0]),
            'confidence': float(anomaly_detector.get_anomaly_score(features)[0])
        }), 200
    except Exception as e:
        logger.error(f"Error detecting anomalies: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@api_bp.route('/ml/classify-threat', methods=['POST'])
def classify_threat():
    """Classify security events into threat categories"""
    try:
        data = request.get_json()
        
        # Validate required fields
        if 'event' not in data:
            return jsonify({'error': 'Missing event data'}), 400
            
        # Extract features
        features = feature_extractor.extract_features([data['event']])
        
        # Classify threat
        prediction = threat_classifier.predict(features)
        probabilities = threat_classifier.predict_proba(features)
        
        return jsonify({
            'threat_type': prediction[0],
            'confidence': float(np.max(probabilities[0])),
            'probabilities': {
                threat_classifier.classes_[i]: float(prob)
                for i, prob in enumerate(probabilities[0])
            }
        }), 200
    except Exception as e:
        logger.error(f"Error classifying threat: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@api_bp.route('/ml/train', methods=['POST'])
def train_model():
    """Train or retrain ML models"""
    try:
        data = request.get_json()
        
        # Validate required fields
        if not all(k in data for k in ['model_type', 'training_data']):
            return jsonify({'error': 'Missing required fields'}), 400
            
        model_type = data['model_type']
        training_data = data['training_data']
        
        # Train appropriate model
        if model_type == 'anomaly':
            anomaly_detector.train(training_data)
            model = MLModel(
                name='Anomaly Detector',
                type='anomaly',
                version=anomaly_detector.version,
                status='active'
            )
        elif model_type == 'classifier':
            threat_classifier.train(training_data)
            model = MLModel(
                name='Threat Classifier',
                type='classifier',
                version=threat_classifier.version,
                status='active'
            )
        else:
            return jsonify({'error': 'Invalid model type'}), 400
            
        model.save()
        
        return jsonify({
            'message': f'{model_type} model trained successfully',
            'model': model.to_dict()
        }), 200
    except Exception as e:
        logger.error(f"Error training model: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500