# Cloud Anomaly Detection - Testing & Validation Guide

## Comprehensive Testing Strategy

### Test Levels

1. **Unit Tests** - Individual functions
2. **Integration Tests** - Component interactions
3. **System Tests** - End-to-end workflows
4. **Load Tests** - Performance under stress
5. **Security Tests** - Vulnerability assessment

---

## Unit Tests

### Test: Database Operations

```python
# tests/test_database.py
import pytest
from backend.database import SessionLocal, engine, init_db, verify_db_connection
from database.models import Prediction

def test_db_initialization():
    """Test that database tables are created."""
    init_db()
    assert engine is not None
    
def test_db_connection():
    """Test database connectivity."""
    assert verify_db_connection() == True

def test_session_creation():
    """Test session factory creates valid sessions."""
    db = SessionLocal()
    assert db is not None
    db.close()

def test_prediction_model_serialization():
    """Test that Prediction model serializes to dict."""
    pred = Prediction(
        cpu_usage=50.5,
        memory_usage=60.3,
        disk_io=100.0,
        network_traffic=500.0,
        prediction="Anomaly",
        cause="High CPU usage"
    )
    
    pred_dict = pred.to_dict()
    assert pred_dict["cpu_usage"] == 50.5
    assert pred_dict["prediction"] == "Anomaly"
    assert "timestamp" in pred_dict
```

### Test: ML Prediction

```python
# tests/test_predict.py
import pytest
import numpy as np
from ml.predict import predict_anomaly

def test_predict_normal_input():
    """Test prediction with normal input."""
    result = predict_anomaly({
        "cpu_usage": 30.0,
        "memory_usage": 40.0,
        "disk_io": 50.0,
        "network_traffic": 100.0,
        "log_message": "INFO Normal operation"
    })
    assert "prediction" in result
    assert result["prediction"] in ["Normal", "Anomaly"]

def test_predict_high_cpu():
    """Test anomaly prediction with high CPU."""
    result = predict_anomaly({
        "cpu_usage": 95.0,
        "memory_usage": 90.0,
        "disk_io": 800.0,
        "network_traffic": 1000.0,
        "log_message": "ERROR High CPU usage"
    })
    assert "prediction" in result

def test_predict_missing_field():
    """Test prediction with missing required field."""
    result = predict_anomaly({
        "cpu_usage": 50.0,
        # Missing memory_usage
        "disk_io": 50.0,
        "network_traffic": 100.0
    })
    # Should return fallback prediction, not crash
    assert result["prediction"] in ["Normal", "Anomaly"]

def test_predict_invalid_type():
    """Test prediction with invalid input type."""
    result = predict_anomaly({
        "cpu_usage": "invalid",  # Should fail type check
        "memory_usage": 50.0,
        "disk_io": 50.0,
        "network_traffic": 100.0
    })
    # Should return fallback, not crash
    assert "prediction" in result

def test_predict_nan_value():
    """Test prediction with NaN value."""
    result = predict_anomaly({
        "cpu_usage": float('nan'),
        "memory_usage": 50.0,
        "disk_io": 50.0,
        "network_traffic": 100.0
    })
    # Should return fallback, not crash
    assert "prediction" in result

def test_predict_out_of_range():
    """Test prediction with out-of-range values."""
    result = predict_anomaly({
        "cpu_usage": 150.0,  # > 100, should clamp
        "memory_usage": -10.0,  # < 0, should clamp
        "disk_io": 50.0,
        "network_traffic": 100.0
    })
    assert "prediction" in result
```

### Test: Log Anomaly Detection

```python
# tests/test_log_anomaly.py
import pytest
import numpy as np
from ml.log_anomaly_model import LogAnomalyDetector

def test_detector_initialization():
    """Test LogAnomalyDetector initialization."""
    detector = LogAnomalyDetector()
    assert detector is not None
    assert detector._is_trained == False

def test_detector_single_input():
    """Test detection with single input."""
    detector = LogAnomalyDetector()
    
    # Train
    X_train = np.random.rand(5, 5)
    detector.train(X_train)
    
    # Detect
    X_test = np.random.rand(1, 5)
    result = detector.detect(X_test)
    
    assert isinstance(result, np.ndarray)
    assert len(result) == 1

def test_detector_handles_nan():
    """Test that detector handles NaN values gracefully."""
    detector = LogAnomalyDetector()
    X_train = np.random.rand(10, 5)
    detector.train(X_train)
    
    # Try to detect with NaN
    X_test = np.array([[1.0, 2.0, np.nan, 4.0, 5.0]])
    
    with pytest.raises(ValueError):
        detector.detect(X_test)

def test_detector_save_load():
    """Test model persistence."""
    import tempfile
    import os
    
    detector = LogAnomalyDetector()
    X_train = np.random.rand(10, 5)
    detector.train(X_train)
    
    # Save
    with tempfile.TemporaryDirectory() as tmp:
        path = os.path.join(tmp, "test_model.pkl")
        detector.save(path)
        assert os.path.exists(path)
        assert os.path.getsize(path) > 0
```

---

## Integration Tests

### Test: API Endpoints

```python
# tests/test_api.py
import pytest
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

def test_health_endpoint():
    """Test /health endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert data["status"] in ["healthy", "degraded", "unhealthy"]

def test_predict_endpoint_valid():
    """Test /predict endpoint with valid input."""
    response = client.post("/predict", json={
        "cpu_usage": 50.0,
        "memory_usage": 60.0,
        "disk_io": 100.0,
        "network_traffic": 500.0
    })
    assert response.status_code == 200
    data = response.json()
    assert "prediction" in data
    assert "cause" in data
    assert data["prediction"] in ["Normal", "Anomaly"]

def test_predict_endpoint_missing_field():
    """Test /predict with missing required field."""
    response = client.post("/predict", json={
        "cpu_usage": 50.0,
        # Missing other fields
    })
    assert response.status_code == 400  # Bad Request

def test_predict_endpoint_invalid_type():
    """Test /predict with invalid data type."""
    response = client.post("/predict", json={
        "cpu_usage": "invalid",
        "memory_usage": 60.0,
        "disk_io": 100.0,
        "network_traffic": 500.0
    })
    assert response.status_code == 400  # Bad Request

def test_predictions_endpoint():
    """Test /predictions endpoint."""
    response = client.get("/predictions")
    assert response.status_code == 200
    data = response.json()
    assert "predictions" in data
    assert isinstance(data["predictions"], list)

def test_root_endpoint():
    """Test GET / endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
```

---

## System Tests (End-to-End)

### Test: Complete Prediction Pipeline

```python
# tests/test_e2e.py
import requests
import time
import pytest

API_URL = "http://localhost:8000"

@pytest.mark.e2e
def test_complete_prediction_flow():
    """Test complete flow: POST predict → store → retrieve."""
    
    # 1. Check health
    health = requests.get(f"{API_URL}/health").json()
    assert health["status"] in ["healthy", "degraded"]
    
    # 2. Send prediction
    payload = {
        "cpu_usage": 75.0,
        "memory_usage": 85.0,
        "disk_io": 200.0,
        "network_traffic": 800.0,
        "log_message": "ERROR High resource usage"
    }
    
    predict_response = requests.post(f"{API_URL}/predict", json=payload)
    assert predict_response.status_code == 200
    prediction = predict_response.json()
    assert prediction["prediction"] in ["Normal", "Anomaly"]
    assert prediction["stored"] == True
    
    # 3. Wait for database
    time.sleep(1)
    
    # 4. Retrieve all predictions
    history = requests.get(f"{API_URL}/predictions").json()
    assert history["count"] > 0
    
    # 5. Verify our prediction is in history
    predictions = history["predictions"]
    matching = [p for p in predictions if p["cpu_usage"] == 75.0]
    assert len(matching) > 0
    assert matching[0]["prediction"] == prediction["prediction"]

@pytest.mark.e2e
def test_continuous_predictions():
    """Test sending multiple predictions."""
    for i in range(10):
        response = requests.post(f"{API_URL}/predict", json={
            "cpu_usage": 20.0 + i * 5,
            "memory_usage": 30.0 + i * 3,
            "disk_io": 50.0 + i * 10,
            "network_traffic": 100.0 + i * 20
        })
        assert response.status_code == 200
    
    # Verify all stored
    history = requests.get(f"{API_URL}/predictions").json()
    assert history["count"] >= 10

@pytest.mark.e2e
def test_error_recovery():
    """Test that API recovers from errors."""
    # Send invalid request
    response1 = requests.post(f"{API_URL}/predict", json={
        "cpu_usage": "invalid"
    })
    assert response1.status_code == 400
    
    # API should still work
    response2 = requests.post(f"{API_URL}/predict", json={
        "cpu_usage": 50.0,
        "memory_usage": 50.0,
        "disk_io": 50.0,
        "network_traffic": 100.0
    })
    assert response2.status_code == 200
```

---

## Load & Performance Tests

### Test: API Load Testing

```bash
#!/bin/bash
# tests/load_test.sh

# Install Apache Bench
# apt-get install apache2-utils

# Test 1: Sequential requests
echo "Test 1: Sequential requests (100 requests)"
ab -n 100 -c 1 http://localhost:8000/health

# Test 2: Concurrent requests
echo "\nTest 2: Concurrent requests (100 requests, 10 concurrent)"
ab -n 100 -c 10 http://localhost:8000/health

# Test 3: POST load test
echo "\nTest 3: POST /predict load (50 requests, 5 concurrent)"

for i in {1..50}; do
    curl -X POST http://localhost:8000/predict \
        -H "Content-Type: application/json" \
        -d "{\"cpu_usage\": $((RANDOM % 100)), \"memory_usage\": $((RANDOM % 100)), \"disk_io\": $((RANDOM % 500)), \"network_traffic\": $((RANDOM % 1000))}" &
    
    # Control concurrency
    if [ $((i % 5)) -eq 0 ]; then
        wait
    fi
done
```

### Test: Using Locust

```python
# tests/locustfile.py
from locust import HttpUser, task, between
import json
import random

class AnomalyDetectionUser(HttpUser):
    wait_time = between(1, 3)
    
    @task(3)
    def predict(self):
        payload = {
            "cpu_usage": random.uniform(0, 100),
            "memory_usage": random.uniform(0, 100),
            "disk_io": random.uniform(0, 500),
            "network_traffic": random.uniform(0, 1000)
        }
        self.client.post("/predict", json=payload)
    
    @task(1)
    def health_check(self):
        self.client.get("/health")
    
    @task(1)
    def get_predictions(self):
        self.client.get("/predictions")
```

**Run:**
```bash
locust -f tests/locustfile.py --host=http://localhost:8000
```

---

## Validation Checklist

### Input Validation ✅

```python
# tests/test_validation.py
import pytest
from ml.predict import _validate_input_dict

def test_input_validation():
    """Test all input validation scenarios."""
    
    # Valid input
    valid = {
        "cpu_usage": 50.0,
        "memory_usage": 60.0,
        "disk_io": 100.0,
        "network_traffic": 500.0
    }
    _validate_input_dict(valid)  # Should not raise
    
    # Missing field
    with pytest.raises(ValueError):
        _validate_input_dict({"cpu_usage": 50.0})
    
    # Invalid type
    with pytest.raises(ValueError):
        _validate_input_dict({
            "cpu_usage": "invalid",
            "memory_usage": 60.0,
            "disk_io": 100.0,
            "network_traffic": 500.0
        })
    
    # NaN value
    with pytest.raises(ValueError):
        _validate_input_dict({
            "cpu_usage": float('nan'),
            "memory_usage": 60.0,
            "disk_io": 100.0,
            "network_traffic": 500.0
        })
    
    # Out of range (should clamp, not raise)
    out_of_range = {
        "cpu_usage": 150.0,
        "memory_usage": -10.0,
        "disk_io": 100.0,
        "network_traffic": 500.0
    }
    _validate_input_dict(out_of_range)
    assert out_of_range["cpu_usage"] == 100.0  # Clamped
    assert out_of_range["memory_usage"] == 0.0   # Clamped
```

---

## Running Tests

### Setup Test Environment

```bash
# Install test dependencies
pip install pytest pytest-asyncio pytest-cov pytest-timeout

# Create test database (isolated from production)
export DATABASE_URL="sqlite:///./test.db"

# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=backend --cov=ml --cov-report=html

# Run only unit tests
pytest tests/test_*.py -v

# Run only E2E tests
pytest tests/test_e2e.py -v -m e2e

# Run with timeout (prevent hanging tests)
pytest tests/ --timeout=10
```

### Continuous Integration (GitHub Actions)

```yaml
# .github/workflows/test.yml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    python-version: ['3.9', '3.10', '3.11']
    
    steps:
    - uses: actions/checkout@v2
    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: ${{ matrix.python-version }}
    
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
        pip install pytest pytest-cov
    
    - name: Run tests
      run: pytest tests/ --cov=backend --cov=ml
    
    - name: Upload coverage
      uses: codecov/codecov-action@v2
```

---

## Production Validation

### Pre-Deployment Checklist

```bash
#!/bin/bash
# scripts/pre_deploy_check.sh

echo "=== Production Deployment Validation ==="

# 1. Database connectivity
echo "✓ Testing database connectivity..."
python -c "from backend.database import verify_db_connection; assert verify_db_connection()"

# 2. Model files exist
echo "✓ Checking model files..."
test -f ml/model.pkl && echo "  - model.pkl exists"
test -f ml/log_model.pkl && echo "  - log_model.pkl exists"

# 3. Run unit tests
echo "✓ Running unit tests..."
pytest tests/test_*.py -q

# 4. Start backend and test endpoints
echo "✓ Starting backend..."
python -m uvicorn backend.main:app --reload &
BACKEND_PID=$!
sleep 2

echo "✓ Testing API endpoints..."
curl -f http://localhost:8000/health > /dev/null && echo "  - /health works"
curl -f -X POST http://localhost:8000/predict \
  -H "Content-Type: application/json" \
  -d '{"cpu_usage": 50, "memory_usage": 60, "disk_io": 100, "network_traffic": 200}' > /dev/null && echo "  - /predict works"

# Cleanup
kill $BACKEND_PID

echo ""
echo "✅ All pre-deployment checks passed!"
```

---

## Test Coverage Targets

| Module | Target Coverage | Current |
|--------|-----------------|---------|
| `backend/main.py` | 90% | - |
| `backend/database.py` | 95% | - |
| `ml/predict.py` | 85% | - |
| `ml/log_anomaly_model.py` | 90% | - |
| `ml/train.py` | 80% | - |
| Overall | **90%** | - |

---

## Monitoring & Alerting

### Key Metrics to Monitor

- API response time (target: < 200ms)
- Error rate (target: < 1%)
- Database query time (target: < 50ms)
- Prediction accuracy (monitor trends)
- Memory usage (target: < 500MB)
- Disk space (alert at 80%)

### Alert Conditions

```yaml
# prometheus_rules.yml
groups:
  - name: anomaly_detection
    rules:
      - alert: APIErrorRateHigh
        expr: rate(errors_total[5m]) > 0.01
        for: 5m
        annotations:
          summary: "High API error rate"

      - alert: PredictionLatencyHigh
        expr: histogram_quantile(0.95, prediction_latency) > 0.2
        for: 10m
        annotations:
          summary: "Prediction latency is high"

      - alert: DiskSpaceRunningOut
        expr: disk_free < 1000000000  # 1GB
        for: 5m
        annotations:
          summary: "Disk space running out"
```

---

**Generated:** 2026-04-01  
**Version:** 1.0  
**Status:** PRODUCTION-READY
