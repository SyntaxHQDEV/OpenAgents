import pytest
from fastapi.testclient import TestClient
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from api.main import app

client = TestClient(app)

def test_request_id_added():
    response = client.get("/health")
    assert response.status_code == 200
    assert "X-Request-ID" in response.headers
    assert len(response.headers["X-Request-ID"]) > 0

def test_client_provided_id_preserved():
    test_id = "test-custom-id-12345"
    response = client.get("/health", headers={"X-Request-ID": test_id})
    assert response.status_code == 200
    assert response.headers["X-Request-ID"] == test_id

def test_unique_ids_generated():
    response1 = client.get("/health")
    response2 = client.get("/health")
    assert response1.headers["X-Request-ID"] != response2.headers["X-Request-ID"]
