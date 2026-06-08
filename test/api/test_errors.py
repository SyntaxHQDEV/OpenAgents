import pytest
from fastapi.testclient import TestClient
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from api.main import app

client = TestClient(app)

def test_404_error_structure():
    response = client.get("/nonexistent-endpoint")
    assert response.status_code == 404
    data = response.json()
    assert "error" in data
    error = data["error"]
    assert error["code"] == "NOT_FOUND"
    assert "message" in error

def test_422_validation_error_structure():
    # Trigger a 422 by missing required query params
    response = client.get("/leaderboard?limit=not_an_int")
    assert response.status_code == 422
    data = response.json()
    assert "error" in data
    error = data["error"]
    assert error["code"] == "VALIDATION_ERROR"
    assert "details" in error
    assert "errors" in error["details"]

# We would need to mock an internal exception to test 500, but 404 and 422 cover the structure.
