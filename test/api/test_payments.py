import pytest
from fastapi.testclient import TestClient
from datetime import datetime, timedelta
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from api.main import app
from api.models.database import Base, engine, SessionLocal, Payment, Task
from api.routes import payments

Base.metadata.create_all(bind=engine)
app.include_router(payments.router)
client = TestClient(app)

@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    
    # Insert task
    task = Task(id=1, title="Test Task", description="Test desc", reward_amount=100.0, creator_id="user_123", status="open")
    db.add(task)
    
    # Insert payments
    # Fresh payment
    db.add(Payment(
        id=1, task_id=1, from_address="0xABC", amount=100.0,
        status="escrowed", created_at=datetime.utcnow() - timedelta(days=5)
    ))
    # Expired payment
    db.add(Payment(
        id=2, task_id=1, from_address="0xDEF", amount=200.0,
        status="escrowed", created_at=datetime.utcnow() - timedelta(days=35)
    ))
    db.commit()
    db.close()

def test_process_expired_escrows():
    response = client.post("/payments/process-expired")
    assert response.status_code == 200
    data = response.json()
    assert data["processed"] == 1
    assert data["refunded_payments"][0]["payment_id"] == 2
    assert data["refunded_payments"][0]["amount"] == 200.0
    
    # Verify in DB
    db = SessionLocal()
    p1 = db.query(Payment).filter(Payment.id == 1).first()
    p2 = db.query(Payment).filter(Payment.id == 2).first()
    assert p1.status == "escrowed"
    assert p2.status == "refunded"
    assert p2.claimed_at is not None
    db.close()
