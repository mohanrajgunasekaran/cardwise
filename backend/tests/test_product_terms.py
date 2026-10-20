import pytest
from decimal import Decimal
from fastapi.testclient import TestClient
from app.main import app

@pytest.fixture
def test_user_client():
    client = TestClient(app)
    # Register and login a unique user for product terms testing
    email = "terms_eval_user@example.com"
    client.post("/api/v1/auth/register", json={
        "email": email,
        "password": "Password123!",
        "full_name": "Terms Evaluator"
    })
    login_res = client.post("/api/v1/auth/login", json={
        "email": email,
        "password": "Password123!"
    })
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Seed 10 reference cards
    seed_res = client.post("/api/v1/auth/seed-demo-data", headers=headers)
    assert seed_res.status_code == 200

    return client, headers

def test_all_10_cards_have_product_terms(test_user_client):
    client, headers = test_user_client
    res = client.get("/api/v1/cards", headers=headers)
    assert res.status_code == 200
    cards = res.json()
    assert len(cards) == 10

    for card in cards:
        terms = card.get("product_terms")
        assert terms is not None, f"Card {card['variant']} missing product_terms"
        assert terms["issuer"] == card["issuer"]
        assert "variant_verification_status" in terms

def test_unverified_variants_withhold_perks(test_user_client):
    client, headers = test_user_client
    res = client.get("/api/v1/cards", headers=headers)
    cards = res.json()

    unverified = [c for c in cards if c["masked_number"] in ["XX3767", "XX7207", "XX8377"]]
    assert len(unverified) == 3

    for card in unverified:
        terms = card["product_terms"]
        assert "unverified" in terms["variant_verification_status"].lower()
        assert terms["exact_variant"] is None
        assert terms["annual_fee"] is None
        assert terms["joining_fee"] is None
        assert terms["unresolved_questions"] is not None

def test_verified_cards_have_official_provenance(test_user_client):
    client, headers = test_user_client
    res = client.get("/api/v1/cards", headers=headers)
    cards = res.json()

    verified = [c for c in cards if c["masked_number"] not in ["XX3767", "XX7207", "XX8377"]]
    assert len(verified) == 7

    for card in verified:
        terms = card["product_terms"]
        assert terms["exact_variant"] is not None
        assert terms["source_url"] is not None
        assert terms["source_url"].startswith("http")
        assert terms["date_verified"] is not None
        assert terms["source_title"] is not None
        assert terms["late_payment_fee_structure"] is not None

def test_matcher_ranks_verified_over_unverified(test_user_client):
    client, headers = test_user_client
    res = client.post("/api/v1/matcher/recommend", headers=headers, json={
        "purchase_amount": 10000.0,
        "category": "SHOPPING",
        "merchant": "Amazon"
    })
    assert res.status_code == 200
    data = res.json()
    recs = data["recommendations"]
    assert len(recs) == 10

    # Top recommendation should be Amazon Pay ICICI
    top = recs[0]
    assert "Amazon Pay" in top["card_name"] or "ICICI" in top["card_name"]
    assert float(top["estimated_net_benefit_inr"]) > 0
    assert top["confidence"] == "VERIFIED"

    # Bottom 3 should be unverified cards
    bottom_3 = recs[-3:]
    for r in bottom_3:
        assert r["confidence"] == "UNVERIFIED"
        assert float(r["estimated_net_benefit_inr"]) == 0.0
        assert "Insufficient verified data" in r["calculation_breakdown"]
