from fastapi.testclient import TestClient
from main import app 
import os
client = TestClient(app)

def test_read_root():
    response = client.get("/")
    assert response.status_code == 200
    assert "message" in response.json()
    assert "GitOps Pipeline Demo" in response.json()["message"]

def test_health_check():
    os.environ["FAIL_HEALTH"] = "false"
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

def test_version_endpoint():
    response = client.get("/version")
    assert response.status_code == 200
    assert "version" in response.json()


