"""
Service for anomaly detection using machine learning models
"""
from typing import Dict, List, Any, Optional, Tuple
import logging
from datetime import datetime, timedelta
import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import IsolationForest
from sklearn.model_selection import train_test_split
import joblib
import os
from dataclasses import dataclass
import json

logger = logging.getLogger(__name__)

@dataclass
class AnomalyConfig:
    """Configuration for anomaly detection"""
    contamination: float = 0.1
    n_estimators: int = 100
    max_samples: str = "auto"
    max_features: float = 1.0
    bootstrap: bool = False
    n_jobs: int = -1
    threshold_percentile: float = 95

class AnomalyDetector:
    def __init__(self, model_path: Optional[str] = None):
        """
        Initialize anomaly detector
        
        Args:
            model_path: Path to saved model (optional)
        """
        self.model = None
        self.scaler = None
        self.config = AnomalyConfig()
        self.feature_columns = []
        
        if model_path and os.path.exists(model_path):
            self.load_model(model_path)
        else:
            self._initialize_model()

    def _initialize_model(self):
        """Initialize new anomaly detection model"""
        self.model = IsolationForest(
            contamination=self.config.contamination,
            n_estimators=self.config.n_estimators,
            max_samples=self.config.max_samples,
            max_features=self.config.max_features,
            bootstrap=self.config.bootstrap,
            n_jobs=self.config.n_jobs,
            random_state=42
        )
        self.scaler = StandardScaler()

    def _extract_features(self, events: List[Dict[str, Any]]) -> Tuple[pd.DataFrame, List[str]]:
        """
        Extract features from events
        
        Args:
            events: List of security events
            
        Returns:
            Tuple of features DataFrame and feature names
        """
        # Convert events to DataFrame
        df = pd.DataFrame(events)
        
        # Extract timestamp features
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df['hour'] = df['timestamp'].dt.hour
        df['day_of_week'] = df['timestamp'].dt.dayofweek
        
        # Count events by type
        event_type_counts = pd.get_dummies(df['event_type'], prefix='event_type')
        
        # Count events by severity
        severity_counts = pd.get_dummies(df['severity'], prefix='severity')
        
        # Count events by source
        source_counts = pd.get_dummies(df['source'], prefix='source')
        
        # Extract numeric features
        numeric_features = df.select_dtypes(include=[np.number]).columns
        numeric_df = df[numeric_features]
        
        # Combine features
        features = pd.concat([
            numeric_df,
            event_type_counts,
            severity_counts,
            source_counts,
            df[['hour', 'day_of_week']]
        ], axis=1)
        
        # Store feature columns
        self.feature_columns = features.columns.tolist()
        
        return features, self.feature_columns

    def train(self,
             events: List[Dict[str, Any]],
             validation_split: float = 0.2) -> Dict[str, Any]:
        """
        Train anomaly detection model
        
        Args:
            events: List of security events
            validation_split: Fraction of data to use for validation
            
        Returns:
            Dictionary containing training metrics
        """
        try:
            # Extract features
            features, _ = self._extract_features(events)
            
            # Split data
            train_data, val_data = train_test_split(
                features,
                test_size=validation_split,
                random_state=42
            )
            
            # Fit scaler
            self.scaler.fit(train_data)
            
            # Scale data
            train_scaled = self.scaler.transform(train_data)
            val_scaled = self.scaler.transform(val_data)
            
            # Train model
            self.model.fit(train_scaled)
            
            # Get scores
            train_scores = -self.model.score_samples(train_scaled)
            val_scores = -self.model.score_samples(val_scaled)
            
            # Calculate threshold
            self.threshold = np.percentile(
                train_scores,
                self.config.threshold_percentile
            )
            
            # Calculate metrics
            train_predictions = (train_scores > self.threshold).astype(int)
            val_predictions = (val_scores > self.threshold).astype(int)
            
            train_anomaly_rate = train_predictions.mean()
            val_anomaly_rate = val_predictions.mean()
            
            return {
                "train_anomaly_rate": float(train_anomaly_rate),
                "val_anomaly_rate": float(val_anomaly_rate),
                "threshold": float(self.threshold),
                "num_features": len(self.feature_columns)
            }
            
        except Exception as e:
            logger.error(f"Error training model: {str(e)}")
            raise

    def predict(self, events: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Detect anomalies in events
        
        Args:
            events: List of security events
            
        Returns:
            List of events with anomaly scores and predictions
        """
        try:
            # Extract features
            features, _ = self._extract_features(events)
            
            # Scale features
            features_scaled = self.scaler.transform(features)
            
            # Get anomaly scores
            scores = -self.model.score_samples(features_scaled)
            
            # Make predictions
            predictions = (scores > self.threshold).astype(int)
            
            # Add results to events
            results = []
            for event, score, prediction in zip(events, scores, predictions):
                event_copy = event.copy()
                event_copy.update({
                    "anomaly_score": float(score),
                    "is_anomaly": bool(prediction),
                    "detection_time": datetime.utcnow().isoformat()
                })
                results.append(event_copy)
                
            return results
            
        except Exception as e:
            logger.error(f"Error detecting anomalies: {str(e)}")
            return events

    def save_model(self, path: str):
        """
        Save model to disk
        
        Args:
            path: Path to save model
        """
        try:
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(path), exist_ok=True)
            
            # Save model components
            model_path = f"{path}_model.joblib"
            scaler_path = f"{path}_scaler.joblib"
            config_path = f"{path}_config.json"
            features_path = f"{path}_features.json"
            
            joblib.dump(self.model, model_path)
            joblib.dump(self.scaler, scaler_path)
            
            with open(config_path, 'w') as f:
                json.dump({
                    "contamination": self.config.contamination,
                    "n_estimators": self.config.n_estimators,
                    "max_samples": self.config.max_samples,
                    "max_features": self.config.max_features,
                    "bootstrap": self.config.bootstrap,
                    "n_jobs": self.config.n_jobs,
                    "threshold_percentile": self.config.threshold_percentile,
                    "threshold": float(self.threshold)
                }, f)
                
            with open(features_path, 'w') as f:
                json.dump(self.feature_columns, f)
                
            logger.info(f"Model saved to {path}")
            
        except Exception as e:
            logger.error(f"Error saving model: {str(e)}")
            raise

    def load_model(self, path: str):
        """
        Load model from disk
        
        Args:
            path: Path to load model from
        """
        try:
            # Load model components
            model_path = f"{path}_model.joblib"
            scaler_path = f"{path}_scaler.joblib"
            config_path = f"{path}_config.json"
            features_path = f"{path}_features.json"
            
            self.model = joblib.load(model_path)
            self.scaler = joblib.load(scaler_path)
            
            with open(config_path, 'r') as f:
                config_dict = json.load(f)
                self.threshold = config_dict.pop('threshold')
                self.config = AnomalyConfig(**config_dict)
                
            with open(features_path, 'r') as f:
                self.feature_columns = json.load(f)
                
            logger.info(f"Model loaded from {path}")
            
        except Exception as e:
            logger.error(f"Error loading model: {str(e)}")
            raise

    def update_model(self,
                    events: List[Dict[str, Any]],
                    retrain: bool = False) -> Dict[str, Any]:
        """
        Update model with new events
        
        Args:
            events: List of new security events
            retrain: Whether to retrain model from scratch
            
        Returns:
            Dictionary containing update metrics
        """
        try:
            # Extract features
            features, _ = self._extract_features(events)
            
            if retrain:
                # Retrain model from scratch
                return self.train(events)
            else:
                # Partial fit not supported by IsolationForest
                # Could implement online learning here
                logger.warning("Partial fit not supported, use retrain=True")
                return {
                    "updated": False,
                    "message": "Partial fit not supported"
                }
                
        except Exception as e:
            logger.error(f"Error updating model: {str(e)}")
            raise

    def get_model_info(self) -> Dict[str, Any]:
        """Get model information and statistics"""
        return {
            "model_type": "IsolationForest",
            "num_features": len(self.feature_columns),
            "feature_names": self.feature_columns,
            "config": {
                "contamination": self.config.contamination,
                "n_estimators": self.config.n_estimators,
                "max_samples": self.config.max_samples,
                "max_features": self.config.max_features,
                "threshold_percentile": self.config.threshold_percentile
            },
            "threshold": float(self.threshold) if hasattr(self, 'threshold') else None
        }

    def analyze_anomalies(self,
                         events: List[Dict[str, Any]],
                         window: Optional[timedelta] = None) -> Dict[str, Any]:
        """
        Analyze detected anomalies
        
        Args:
            events: List of events with anomaly predictions
            window: Time window for analysis
            
        Returns:
            Dictionary containing anomaly analysis
        """
        try:
            # Convert to DataFrame
            df = pd.DataFrame(events)
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            
            # Filter by time window
            if window:
                cutoff_time = datetime.utcnow() - window
                df = df[df['timestamp'] > cutoff_time]
            
            # Calculate statistics
            total_events = len(df)
            anomalous_events = df['is_anomaly'].sum()
            anomaly_rate = anomalous_events / total_events if total_events > 0 else 0
            
            # Group by event type
            type_stats = df[df['is_anomaly']].groupby('event_type').size().to_dict()
            
            # Group by severity
            severity_stats = df[df['is_anomaly']].groupby('severity').size().to_dict()
            
            # Calculate score statistics
            score_stats = {
                "mean": float(df['anomaly_score'].mean()),
                "std": float(df['anomaly_score'].std()),
                "min": float(df['anomaly_score'].min()),
                "max": float(df['anomaly_score'].max())
            }
            
            return {
                "total_events": int(total_events),
                "anomalous_events": int(anomalous_events),
                "anomaly_rate": float(anomaly_rate),
                "by_type": type_stats,
                "by_severity": severity_stats,
                "score_stats": score_stats,
                "analysis_time": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error analyzing anomalies: {str(e)}")
            return {}