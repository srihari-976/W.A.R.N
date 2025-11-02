import numpy as np
import pandas as pd
from typing import Dict, List, Any, Optional, Union, Tuple
import pickle
from sklearn.ensemble import RandomForestClassifier
from sklearn.svm import SVC
from sklearn.neural_network import MLPClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
import joblib
from datetime import datetime
from pathlib import Path
import logging

from .feature_extraction import FeatureExtractor

logger = logging.getLogger(__name__)

class SecurityEventClassifier:
    """Classify security events using multiple machine learning algorithms"""
    
    def __init__(self, model_dir: str = "models"):
        self.model_dir = Path(model_dir)
        self.model_dir.mkdir(exist_ok=True)
        self.scaler = StandardScaler()
        self.feature_extractor = FeatureExtractor()
        
        # Initialize multiple classifiers
        self.models = {
            'random_forest': RandomForestClassifier(
                n_estimators=100,
                max_depth=10,
                random_state=42
            ),
            'svm': SVC(
                probability=True,
                random_state=42
            ),
            'neural_net': MLPClassifier(
                hidden_layer_sizes=(100, 50),
                max_iter=1000,
                random_state=42
            )
        }
        
        self._load_or_initialize_models()
    
    def _load_or_initialize_models(self):
        """Load existing models or initialize new ones"""
        for model_name, model in self.models.items():
            model_path = self.model_dir / f"classifier_{model_name}.joblib"
            if model_path.exists():
                try:
                    self.models[model_name] = joblib.load(model_path)
                    logger.info(f"Loaded {model_name} classifier from {model_path}")
                except Exception as e:
                    logger.error(f"Error loading {model_name} classifier: {e}")
                    self.models[model_name] = model
    
    def _save_models(self):
        """Save all models to disk"""
        for model_name, model in self.models.items():
            model_path = self.model_dir / f"classifier_{model_name}.joblib"
            try:
                joblib.dump(model, model_path)
                logger.info(f"Saved {model_name} classifier to {model_path}")
            except Exception as e:
                logger.error(f"Error saving {model_name} classifier: {e}")
    
    def train(self, events_data: List[Dict[str, Any]], labels: List[str]):
        """Train all classifiers"""
        try:
            # Extract features
            features = self.feature_extractor.extract_features(events_data)
            
            # Scale features
            scaled_features = self.scaler.fit_transform(features)
            
            # Split data for validation
            X_train, X_val, y_train, y_val = train_test_split(
                scaled_features, labels,
                test_size=0.2,
                random_state=42
            )
            
            # Train each model
            for model_name, model in self.models.items():
                model.fit(X_train, y_train)
                
                # Evaluate model
                train_score = model.score(X_train, y_train)
                val_score = model.score(X_val, y_val)
                logger.info(f"{model_name} - Train accuracy: {train_score:.3f}, Validation accuracy: {val_score:.3f}")
            
            # Save models
            self._save_models()
            logger.info("Successfully trained all classifiers")
            
        except Exception as e:
            logger.error(f"Error training classifiers: {e}")
            raise
    
    def predict(self, events_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Predict security event types using ensemble of models"""
        try:
            # Extract features
            features = self.feature_extractor.extract_features(events_data)
            
            # Scale features
            scaled_features = self.scaler.transform(features)
            
            # Get predictions from each model
            predictions = {}
            probabilities = {}
            
            for model_name, model in self.models.items():
                pred = model.predict(scaled_features)
                prob = model.predict_proba(scaled_features)
                predictions[model_name] = pred
                probabilities[model_name] = prob
            
            # Combine predictions using voting
            final_predictions = []
            for i in range(len(events_data)):
                # Get predictions from all models for this event
                event_preds = [pred[i] for pred in predictions.values()]
                
                # Get probabilities from all models
                event_probs = {
                    model_name: {
                        class_name: float(prob[i][j])
                        for j, class_name in enumerate(model.classes_)
                    }
                    for model_name, (model, prob) in zip(self.models.keys(), probabilities.items())
                }
                
                # Use majority voting for final prediction
                from collections import Counter
                final_pred = Counter(event_preds).most_common(1)[0][0]
                
                # Calculate confidence as average probability across models
                confidence = np.mean([
                    prob[final_pred]
                    for prob in probabilities.values()
                ])
                
                result = {
                    'prediction': final_pred,
                    'confidence': float(confidence),
                    'model_predictions': {
                        model_name: pred[i]
                        for model_name, pred in predictions.items()
                    },
                    'model_probabilities': event_probs
                }
                
                final_predictions.append(result)
            
            return final_predictions
            
        except Exception as e:
            logger.error(f"Error predicting security events: {e}")
            raise
    
    def get_feature_importance(self) -> Dict[str, float]:
        """Get feature importance from Random Forest model"""
        try:
            if not isinstance(self.models['random_forest'], RandomForestClassifier):
                return {}
            
            importances = self.models['random_forest'].feature_importances_
            feature_names = self.feature_extractor.get_feature_names()
            
            # Sort features by importance
            indices = np.argsort(importances)[::-1]
            
            return {
                feature_names[i]: float(importances[i])
                for i in indices
            }
            
        except Exception as e:
            logger.error(f"Error getting feature importance: {e}")
            return {}
