import pytest
from fastapi.testclient import TestClient
from decimal import Decimal
from app.main import app
from app.db.session import Base, engine, SessionLocal
from app.models.models import User, CreditCard, Statement, Payment

@pytest.fixture(scope="session", autouse=True)
def setup_database():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

@pytest.fixture
def client():
    return TestClient(app)

def test_health_check(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

def test_auth_and_cross_user_isolation(client):
    # 1. Register User 1
    r1 = client.post("/api/v1/auth/register", json={
        "email": "user1@example.com",
        "password": "Password123!",
        "full_name": "Test User One"
    })
    assert r1.status_code in (200, 400)

    # Login User 1
    login1 = client.post("/api/v1/auth/login", json={
        "email": "user1@example.com",
        "password": "Password123!"
    })
    assert login1.status_code == 200
    token1 = login1.json()["access_token"]
    headers1 = {"Authorization": f"Bearer {token1}"}

    # 2. Register User 2
    r2 = client.post("/api/v1/auth/register", json={
        "email": "user2@example.com",
        "password": "Password123!",
        "full_name": "Test User Two"
    })
    assert r2.status_code in (200, 400)

    # Login User 2
    login2 = client.post("/api/v1/auth/login", json={
        "email": "user2@example.com",
        "password": "Password123!"
    })
    assert login2.status_code == 200
    token2 = login2.json()["access_token"]
    headers2 = {"Authorization": f"Bearer {token2}"}

    # 3. User 1 creates a card
    card_res = client.post("/api/v1/cards", headers=headers1, json={
        "issuer": "ICICI Bank",
        "variant": "Coral",
        "nickname": "Secret Card",
        "masked_number": "XXXX-XXXX-XXXX-9999",
        "network": "VISA",
        "credit_limit": 100000.0,
        "available_limit": 80000.0,
        "billing_cycle_day": 15,
        "payment_due_days": 20,
        "annual_fee": 500.0,
        "joining_fee": 500.0,
        "reward_type": "REWARD_POINTS",
        "base_earn_rate": 2.0,
        "point_redemption_inr": 0.25,
        "is_verified": True
    })
    assert card_res.status_code == 201
    card_id = card_res.json()["id"]

    # 4. User 2 attempts to fetch User 1's card -> MUST return 404
    cross_res = client.get(f"/api/v1/cards/{card_id}", headers=headers2)
    assert cross_res.status_code == 404

    # 5. User 1 creates a statement
    stmt_res = client.post("/api/v1/statements", headers=headers1, json={
        "card_id": card_id,
        "statement_date": "2026-10-01",
        "payment_due_date": "2026-10-21",
        "period_start": "2026-09-01",
        "period_end": "2026-09-30",
        "total_balance": 15000.0,
        "minimum_due": 750.0,
        "source": "MANUAL"
    })
    assert stmt_res.status_code == 201
    stmt_id = stmt_res.json()["id"]

    # 6. Verify duplicate statement detection -> MUST return 409 Conflict
    dup_res = client.post("/api/v1/statements", headers=headers1, json={
        "card_id": card_id,
        "statement_date": "2026-10-01",
        "payment_due_date": "2026-10-21",
        "period_start": "2026-09-01",
        "period_end": "2026-09-30",
        "total_balance": 15000.0,
        "minimum_due": 750.0,
        "source": "MANUAL"
    })
    assert dup_res.status_code == 409

    # 7. User 1 plans a payment
    pmt_res = client.post("/api/v1/payments", headers=headers1, json={
        "statement_id": stmt_id,
        "amount": 5000.0,
        "planned_date": "2026-10-18",
        "notes": "First tranche"
    })
    assert pmt_res.status_code == 201
    pmt_id = pmt_res.json()["id"]

    # 8. User 1 confirms the payment
    conf_res = client.post(f"/api/v1/payments/{pmt_id}/confirm", headers=headers1, json={
        "notes": "Paid via Netbanking Reference 987654"
    })
    assert conf_res.status_code == 200
    assert conf_res.json()["status"] == "CONFIRMED"

    # 9. Verify statement remaining reflects confirmed payment
    stmt_updated = client.get(f"/api/v1/statements/{stmt_id}", headers=headers1).json()
    assert float(stmt_updated["confirmed_paid_amount"]) == 5000.0
    assert float(stmt_updated["remaining_to_plan"]) == 10000.0

def test_seed_and_matcher_endpoint(client):
    # Register new user
    client.post("/api/v1/auth/register", json={
        "email": "matcher_user@example.com",
        "password": "Password123!"
    })
    login = client.post("/api/v1/auth/login", json={
        "email": "matcher_user@example.com",
        "password": "Password123!"
    })
    token = login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Seed the 10 demonstration cards
    seed_res = client.post("/api/v1/auth/seed-demo-data", headers=headers)
    assert seed_res.status_code == 200
    assert "10 synthetic demonstration cards" in seed_res.json()["message"]

    # Verify wallet has 10 cards
    cards_res = client.get("/api/v1/cards", headers=headers)
    assert cards_res.status_code == 200
    assert len(cards_res.json()) == 10

    # Query Smart Card Matcher for Amazon purchase of ₹5,000
    match_res = client.post("/api/v1/matcher/recommend", headers=headers, json={
        "purchase_amount": 5000.0,
        "category": "SHOPPING",
        "merchant": "Amazon"
    })
    assert match_res.status_code == 200
    data = match_res.json()
    assert len(data["recommendations"]) == 10
    top_card = data["recommendations"][0]
    # Amazon Pay ICICI should be ranked #1 with 5% (₹250)
    assert "Amazon Pay" in top_card["variant"] or "ICICI" in top_card["issuer"]
    assert float(top_card["estimated_net_benefit_inr"]) == 250.0
    assert float(top_card["effective_rate_percent"]) == 5.0

    # Query Dashboard Summary
    dash_res = client.get("/api/v1/dashboard/summary", headers=headers)
    assert dash_res.status_code == 200
    assert dash_res.json()["total_cards_count"] == 10

