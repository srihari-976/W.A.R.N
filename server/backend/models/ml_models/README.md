# ML Models Directory

This directory contains trained machine learning models for the endpoint agent application.

## Contents

- Anomaly detection models
- Risk assessment models
- Behavioral analysis models

## Model Files

Models are saved in the following formats:
- `.joblib` - Scikit-learn models
- `.pt` - PyTorch models
- `.h5` - TensorFlow/Keras models

## Usage

Models in this directory are loaded by the ML service components for:
- Anomaly detection in security events
- Risk scoring and assessment
- Behavioral pattern analysis
- Threat detection

## Model Updates

Models are periodically updated through:
- Retraining on new data
- Fine-tuning existing models
- Deploying updated versions

Please ensure proper versioning when updating models. 