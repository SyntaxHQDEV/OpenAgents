import pytest
from fastapi.testclient import TestClient
from fastapi import FastAPI, Depends
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from api.middleware.auth import api_key_router, get_current_user, create_access_token, _api_keys

app = FastAPI()
app.include_router(api_key_router)

@app.get("/protected")
def protected_route(user=Depends(get_current_user)):
    return {"user": user}

client = TestClient(app)

def test_jwt_auth():
    token = create_access_token({"sub": "user_123", "address": "0x123", "roles": []})
    response = client.get("/protected", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert response.json()["user"]["id"] == "user_123"

def test_api_key_auth_and_revocation():
    # First need a JWT to create an API key
    token = create_access_token({"sub": "user_123", "address": "0x123", "roles": []})
    
    # Create API key
    response = client.post("/auth/api-keys/", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    data = response.json()
    assert "api_key" in data
    api_key = data["api_key"]
    key_id = data["id"]
    
    # Authenticate with API key
    response = client.get("/protected", headers={"X-API-Key": api_key})
    assert response.status_code == 200
    assert response.json()["user"]["id"] == "user_123"
    
    # Revoke API key
    revoke_resp = client.delete(f"/auth/api-keys/{key_id}", headers={"Authorization": f"Bearer {token}"})
    assert revoke_resp.status_code == 200
    
    # Authenticate again (should fail)
    response = client.get("/protected", headers={"X-API-Key": api_key})
    assert response.status_code == 401
