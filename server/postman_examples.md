# Postman API Examples

Base URL: http://127.0.0.1:5000

## 1. Authentication Endpoints

```json
// POST http://127.0.0.1:5000/api/auth/register
Request:
{
    "username": "testuser",
    "email": "test@example.com",
    "password": "SecurePass123!",
    "role": "analyst"
}

Response (201 Created):
{
    "message": "User registered successfully"
}

// POST http://127.0.0.1:5000/api/auth/login
Request:
{
    "username": "testuser",
    "password": "SecurePass123!"
}

Response (200 OK):
{
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

## 2. Agent Management Endpoints

```json
// POST http://127.0.0.1:5000/api/agent/register
Request:
{
    "hostname": "DESKTOP-ABC123",
    "os": "Windows 10",
    "ip_address": "192.168.1.100",
    "agent_version": "1.0.0"
}

Response (200 OK):
{
    "message": "Agent registered successfully",
    "asset_id": 123,
    "configuration": {
        "scan_interval": 300,
        "log_level": "INFO",
        "max_retries": 3
    }
}

// GET http://127.0.0.1:5000/api/agent/status/{agent_id}
Response (200 OK):
{
    "status": "active",
    "last_heartbeat": "2024-03-20T10:30:00Z",
    "current_tasks": [],
    "resource_usage": {
        "cpu": "15%",
        "memory": "1.2GB",
        "disk": "500MB"
    }
}
```

## 3. Asset Management Endpoints

```json
// GET http://127.0.0.1:5000/api/assets
Query Parameters:
- page (default: 1)
- per_page (default: 10)
- status (optional)
- type (optional)

Response (200 OK):
{
    "assets": [
        {
            "id": 1,
            "hostname": "DESKTOP-ABC123",
            "os_type": "Windows 10",
            "ip_address": "192.168.1.100",
            "agent_version": "1.0.0",
            "asset_type": "endpoint",
            "status": "active",
            "last_seen": "2024-03-20T10:30:00Z"
        }
    ],
    "total": 1,
    "page": 1,
    "per_page": 10
}

// GET http://127.0.0.1:5000/api/assets/{asset_id}
Response (200 OK):
{
    "id": 1,
    "hostname": "DESKTOP-ABC123",
    "os_type": "Windows 10",
    "ip_address": "192.168.1.100",
    "agent_version": "1.0.0",
    "asset_type": "endpoint",
    "status": "active",
    "last_seen": "2024-03-20T10:30:00Z"
}

// PUT http://127.0.0.1:5000/api/assets/{asset_id}
Request:
{
    "status": "maintenance",
    "notes": "Scheduled maintenance"
}

Response (200 OK):
{
    "message": "Asset updated successfully"
}
```

## 4. Event Management Endpoints

```json
// GET http://127.0.0.1:5000/api/events
Query Parameters:
- page (default: 1)
- per_page (default: 10)
- severity (optional)
- type (optional)
- start_date (optional)
- end_date (optional)

Response (200 OK):
{
    "events": [
        {
            "id": 1,
            "event_type": "login_attempt",
            "severity": "high",
            "source_ip": "192.168.1.100",
            "timestamp": "2024-03-20T10:30:00Z",
            "details": {
                "username": "admin",
                "success": false,
                "attempt_count": 5
            }
        }
    ],
    "total": 1,
    "page": 1,
    "per_page": 10
}

// POST http://127.0.0.1:5000/api/events
Request:
{
    "event_type": "file_access",
    "severity": "medium",
    "source_ip": "192.168.1.100",
    "details": {
        "filename": "sensitive.txt",
        "action": "read",
        "user": "john.doe"
    }
}

Response (201 Created):
{
    "message": "Event recorded successfully",
    "event_id": 2
}
```

## 5. Alert Management Endpoints

```json
// GET http://127.0.0.1:5000/api/alerts
Query Parameters:
- page (default: 1)
- per_page (default: 10)
- status (optional)
- severity (optional)

Response (200 OK):
{
    "alerts": [
        {
            "id": 1,
            "alert_type": "suspicious_activity",
            "severity": "high",
            "status": "new",
            "source": "endpoint_agent",
            "timestamp": "2024-03-20T10:30:00Z",
            "details": {
                "event_id": 1,
                "description": "Multiple failed login attempts detected"
            }
        }
    ],
    "total": 1,
    "page": 1,
    "per_page": 10
}

// PUT http://127.0.0.1:5000/api/alerts/{alert_id}
Request:
{
    "status": "acknowledged",
    "notes": "Investigating"
}

Response (200 OK):
{
    "message": "Alert updated successfully"
}
```

## 6. Risk Assessment Endpoints

```json
// GET http://127.0.0.1:5000/api/risk/scores
Query Parameters:
- asset_id (optional)
- min_score (optional)
- start_date (optional)
- end_date (optional)

Response (200 OK):
{
    "risk_scores": [
        {
            "id": 1,
            "asset_id": 1,
            "score": 0.85,
            "factors": {
                "vulnerability_score": 0.7,
                "threat_score": 0.9,
                "exposure_score": 0.8
            },
            "timestamp": "2024-03-20T10:30:00Z"
        }
    ],
    "total": 1,
    "limit": 100,
    "offset": 0
}

// GET http://127.0.0.1:5000/api/risk/factors
Response (200 OK):
{
    "risk_factors": [
        {
            "name": "vulnerability_score",
            "weight": 0.4,
            "description": "Based on known vulnerabilities"
        },
        {
            "name": "threat_score",
            "weight": 0.3,
            "description": "Based on active threats"
        },
        {
            "name": "exposure_score",
            "weight": 0.3,
            "description": "Based on system exposure"
        }
    ]
}

// POST http://127.0.0.1:5000/api/risk/calculate
Request:
{
    "asset_id": 1,
    "factors": {
        "vulnerability_score": 0.7,
        "threat_score": 0.9,
        "exposure_score": 0.8
    }
}

Response (200 OK):
{
    "risk_score": 0.85,
    "risk_level": "high",
    "recommendations": [
        "Update system patches",
        "Review access controls"
    ]
}
```

## 7. Response Management Endpoints

```json
// POST http://127.0.0.1:5000/api/responses
Request:
{
    "name": "Block Suspicious IP",
    "action_type": "block_ip",
    "parameters": {
        "ip_address": "192.168.1.100",
        "duration": 3600
    }
}

Response (201 Created):
{
    "message": "Response created successfully",
    "response": {
        "id": 1,
        "name": "Block Suspicious IP",
        "action_type": "block_ip",
        "parameters": {
            "ip_address": "192.168.1.100",
            "duration": 3600
        },
        "status": "active"
    }
}

// GET http://127.0.0.1:5000/api/responses/actions
Response (200 OK):
{
    "available_actions": [
        {
            "type": "block_ip",
            "description": "Block an IP address at the firewall",
            "parameters": ["ip_address", "duration"],
            "supported_assets": ["firewall", "network"],
            "risk_level": "high"
        },
        {
            "type": "isolate_host",
            "description": "Network isolation of a host",
            "parameters": ["host_id"],
            "supported_assets": ["endpoint", "server"],
            "risk_level": "high"
        }
    ]
}

// POST http://127.0.0.1:5000/api/responses/execute
Request:
{
    "action_type": "block_ip",
    "parameters": {
        "ip_address": "192.168.1.100",
        "duration": 3600
    },
    "reason": "Suspicious activity detected"
}

Response (200 OK):
{
    "message": "Response executed successfully",
    "execution_id": "exec_123",
    "status": "completed"
}
```

## 8. Machine Learning Endpoints

```json
// POST http://127.0.0.1:5000/api/ml/models
Request:
{
    "name": "Anomaly Detector v1",
    "model_type": "anomaly_detection",
    "description": "Detects anomalous behavior in system logs",
    "parameters": {
        "threshold": 0.95,
        "window_size": 1000
    },
    "performance_metrics": {
        "accuracy": 0.98,
        "f1_score": 0.97
    },
    "features": ["timestamp", "event_type", "source_ip"]
}

Response (201 Created):
{
    "message": "Model created successfully",
    "model": {
        "id": 1,
        "name": "Anomaly Detector v1",
        "model_type": "anomaly_detection",
        "description": "Detects anomalous behavior in system logs",
        "parameters": {
            "threshold": 0.95,
            "window_size": 1000
        },
        "performance_metrics": {
            "accuracy": 0.98,
            "f1_score": 0.97
        },
        "features": ["timestamp", "event_type", "source_ip"],
        "status": "active"
    }
}

// GET http://127.0.0.1:5000/api/ml/models/{model_id}/predict
Query Parameters:
- data (required): Base64 encoded event data

Response (200 OK):
{
    "prediction": {
        "anomaly_score": 0.95,
        "is_anomaly": true,
        "confidence": 0.98
    }
}

// GET http://127.0.0.1:5000/api/ml/models/{model_id}/metrics
Response (200 OK):
{
    "metrics": {
        "accuracy": 0.98,
        "precision": 0.97,
        "recall": 0.96,
        "f1_score": 0.97,
        "confusion_matrix": {
            "true_positives": 950,
            "false_positives": 30,
            "true_negatives": 970,
            "false_negatives": 50
        }
    }
}
```

## Testing Instructions

1. Set up environment variables in Postman:
   ```
   base_url: http://127.0.0.1:5000
   jwt_token: (will be set after login)
   ```

2. Create a new collection in Postman with the following structure:
   - Authentication
   - Agent Management
   - Asset Management
   - Event Management
   - Alert Management
   - Risk Assessment
   - Response Management
   - Machine Learning

3. For each endpoint:
   - Set the appropriate HTTP method
   - Use the complete URL: {{base_url}}/endpoint
   - Add required headers:
     ```
     Content-Type: application/json
     Authorization: Bearer {{jwt_token}}
     ```
   - Add request body for POST/PUT requests
   - Add query parameters where needed

4. Testing workflow:
   1. Start with POST /api/auth/register to create a user
   2. Use POST /api/auth/login to get JWT token
   3. Set the JWT token in environment variables
   4. Test other endpoints using the token

5. Common response codes:
   - 200: Success
   - 201: Created
   - 400: Bad Request
   - 401: Unauthorized
   - 403: Forbidden
   - 404: Not Found
   - 500: Internal Server Error 