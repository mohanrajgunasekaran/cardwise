from decimal import Decimal
from datetime import date, timedelta
import pytest
from app.services.payment_calculator import calculate_payment_reconciliation
from app.services.matching_engine import evaluate_card_benefit, match_best_cards

class MockCard:
    def __init__(self, id, issuer, variant, reward_type, base_earn_rate, point_redemption_inr, is_verified=True, masked="XXXX-1234", is_archived=False):
        self.id = id
        self.issuer = issuer
        self.variant = variant
        self.reward_type = reward_type
        self.base_earn_rate = Decimal(str(base_earn_rate))
        self.point_redemption_inr = Decimal(str(point_redemption_inr))
        self.is_verified = is_verified
        self.masked_number = masked
        self.is_archived = is_archived

class MockOffer:
    def __init__(self, id, issuer, variant, title, category, benefit_type, benefit_value, min_spend=0, max_benefit_cap=None, merchant_keyword=None, valid_days=30, confidence="VERIFIED"):
        self.id = id
        self.issuer = issuer
        self.variant = variant
        self.title = title
        self.category = category
        self.benefit_type = benefit_type
        self.benefit_value = Decimal(str(benefit_value))
        self.min_spend = Decimal(str(min_spend))
        self.max_benefit_cap = Decimal(str(max_benefit_cap)) if max_benefit_cap else None
        self.merchant_keyword = merchant_keyword
        self.valid_from = date.today() - timedelta(days=5)
        self.valid_to = date.today() + timedelta(days=valid_days)
        self.exclusion_details = ""
        self.confidence = confidence

# --- Financial Calculation Tests ---

def test_decimal_precision_exact_cents():
    """Verify absence of floating point representation artifacts (e.g., 0.1 + 0.2 != 0.3)"""
    balance = Decimal("1999.99")
    payments = [
        {"amount": Decimal("1000.00"), "status": "CONFIRMED"},
        {"amount": Decimal("999.99"), "status": "PLANNED"}
    ]
    recon = calculate_payment_reconciliation(balance, Decimal("100.00"), payments)
    assert recon.remaining_to_plan == Decimal("0.00")
    assert recon.is_fully_planned is True
    assert recon.is_fully_confirmed is False

def test_reward_maximum_cap_enforcement():
    """Verify that benefit cannot exceed configured maximum cap"""
    card = MockCard("c1", "RBL Bank", "Shoprite", "CASHBACK", "1.00", "1.00")
    offer = MockOffer(
        "o1", "RBL Bank", "Shoprite", "5% Grocery Value", "GROCERIES",
        "CASHBACK_PERCENT", "5.00", min_spend=500, max_benefit_cap=250
    )
    # Spend ₹10,000 -> 5% is ₹500, but cap is ₹250
    res = evaluate_card_benefit(card, [offer], Decimal("10000.00"), "GROCERIES")
    assert res.estimated_net_benefit_inr == Decimal("250.00")
    assert "Capped at ₹250.00" in res.calculation_breakdown

def test_minimum_spend_hurdle_fallback():
    """Verify that transactions below minimum spend hurdle fall back to base rate"""
    card = MockCard("c1", "ICICI Bank", "Coral", "CASHBACK", "1.00", "1.00")
    offer = MockOffer(
        "o1", "ICICI Bank", "Coral", "15% Dining Savings", "DINING",
        "CASHBACK_PERCENT", "15.00", min_spend=1500
    )
    # Spend ₹1,000 (below ₹1,500 hurdle)
    res = evaluate_card_benefit(card, [offer], Decimal("1000.00"), "DINING")
    # Should get 1% base rate = ₹10.00
    assert res.estimated_net_benefit_inr == Decimal("10.00")
    assert "falling back to base rate" in res.eligibility_conditions

def test_fuel_category_exclusion():
    """Verify that category exclusions (like Fuel) yield zero rewards when no waiver is active"""
    card = MockCard("c1", "HDFC Bank", "Millennia", "CASHBACK", "1.00", "1.00")
    res = evaluate_card_benefit(card, [], Decimal("2500.00"), "FUEL")
    assert res.estimated_net_benefit_inr == Decimal("0.00")
    assert "excluded from rewards" in res.calculation_breakdown

def test_offer_expiry_date_handling():
    """Verify expired offers are ignored and base rate applies"""
    card = MockCard("c1", "Amazon Pay", "ICICI", "CASHBACK", "1.00", "1.00")
    expired_offer = MockOffer(
        "o1", "Amazon Pay", "ICICI", "10% Festive Sale", "SHOPPING",
        "CASHBACK_PERCENT", "10.00", valid_days=-2  # expired 2 days ago
    )
    res = evaluate_card_benefit(card, [expired_offer], Decimal("5000.00"), "SHOPPING")
    # Base 1% of 5000 = 50
    assert res.estimated_net_benefit_inr == Decimal("50.00")

def test_multiple_planned_payments_and_confirmed_reconciliation():
    """Verify multiple planned disbursements correctly reduce remaining balance without altering confirmed totals"""
    statement_balance = Decimal("25000.00")
    min_due = Decimal("1250.00")
    payments = [
        {"amount": Decimal("5000.00"), "status": "CONFIRMED"},
        {"amount": Decimal("10000.00"), "status": "PLANNED"},
        {"amount": Decimal("7500.00"), "status": "PLANNED"},
        {"amount": Decimal("2000.00"), "status": "CANCELLED"},  # Should not be counted
    ]
    recon = calculate_payment_reconciliation(statement_balance, min_due, payments)
    assert recon.confirmed_payments_total == Decimal("5000.00")
    assert recon.planned_payments_total == Decimal("17500.00")
    # Remaining = 25000 - 5000 - 17500 = 2500.00
    assert recon.remaining_to_plan == Decimal("2500.00")
    assert recon.is_fully_planned is False
    assert recon.is_fully_confirmed is False

def test_overpayment_and_credit_balance():
    """Verify overpayment boundary behavior"""
    statement_balance = Decimal("5000.00")
    payments = [{"amount": Decimal("6000.00"), "status": "CONFIRMED"}]
    # With default allow_overpayment=False, remaining is capped at 0.00 and has_overpayment is True
    recon = calculate_payment_reconciliation(statement_balance, Decimal("250.00"), payments, allow_overpayment=False)
    assert recon.remaining_to_plan == Decimal("0.00")
    assert recon.has_overpayment is True

    # With explicit allow_overpayment=True
    recon_allowed = calculate_payment_reconciliation(statement_balance, Decimal("250.00"), payments, allow_overpayment=True)
    assert recon_allowed.remaining_to_plan == Decimal("-1000.00")
    assert recon_allowed.has_overpayment is True
