from decimal import Decimal, ROUND_HALF_UP
from typing import List, Optional, Dict, Any
from datetime import date
from pydantic import BaseModel

class EvaluationResult(BaseModel):
    card_id: str
    card_name: str
    issuer: str
    variant: str
    masked_number: str
    estimated_net_benefit_inr: Decimal
    effective_rate_percent: Decimal
    calculation_breakdown: str
    applied_rule: str
    eligibility_conditions: str
    offer_expiry: Optional[date] = None
    confidence: str

def evaluate_card_benefit(
    card: Any,
    offers: List[Any],
    purchase_amount: Decimal,
    category: str,
    merchant: Optional[str] = None,
    transaction_date: Optional[date] = None
) -> EvaluationResult:
    """
    Evaluates the net monetary benefit in INR for a given credit card on a planned purchase.
    Uses strict Decimal arithmetic with explicit rounding to two decimal places.
    """
    if transaction_date is None:
        transaction_date = date.today()

    norm_category = category.strip().upper()
    norm_merchant = merchant.strip().lower() if merchant else ""

    # Card base properties
    base_rate = Decimal(str(getattr(card, "base_earn_rate", 1.00)))
    reward_type = getattr(card, "reward_type", "CASHBACK").upper()
    point_value = Decimal(str(getattr(card, "point_redemption_inr", 0.25)))
    is_verified = getattr(card, "is_verified", False)
    confidence = "VERIFIED" if is_verified else "ESTIMATED"

    # Identify matching offers for this card and category/merchant
    applicable_offers = []
    for offer in offers:
        # Check validity window
        v_from = getattr(offer, "valid_from", None)
        v_to = getattr(offer, "valid_to", None)
        if v_from and transaction_date < v_from:
            continue
        if v_to and transaction_date > v_to:
            continue

        # Check category match
        off_cat = getattr(offer, "category", "").upper()
        if off_cat != norm_category and off_cat != "ALL":
            continue

        # Check merchant match if specified
        off_merch = (getattr(offer, "merchant_keyword", "") or "").lower()
        if off_merch and off_merch not in norm_merchant:
            continue

        applicable_offers.append(offer)

    # Determine best applicable offer vs base rate (avoid double-counting overlapping offers)
    best_rate = base_rate
    applied_rule_name = f"Base {base_rate}% {reward_type.title()}"
    eligibility_notes = "Standard card base reward"
    expiry_date = None
    max_cap: Optional[Decimal] = None
    is_excluded = False
    exclusion_reason = ""

    # Check category exclusions
    # Typically Fuel surcharge waivers have specific min/max spend rules or are excluded from points
    if norm_category == "FUEL":
        if "surcharge" in [getattr(o, "title", "").lower() for o in applicable_offers]:
            applied_rule_name = "1% Fuel Surcharge Waiver"
            eligibility_notes = "Transactions between ₹400 and ₹4,000 (Max ₹100-₹250 waiver/cycle)"
        else:
            is_excluded = True
            exclusion_reason = "Fuel purchases commonly excluded from reward points accrual"

    if applicable_offers and not is_excluded:
        # Sort by benefit_value descending
        applicable_offers.sort(key=lambda o: getattr(o, "benefit_value", Decimal("0")), reverse=True)
        top_offer = applicable_offers[0]

        min_spend = Decimal(str(getattr(top_offer, "min_spend", 0)))
        if purchase_amount >= min_spend:
            best_rate = Decimal(str(getattr(top_offer, "benefit_value", base_rate)))
            applied_rule_name = getattr(top_offer, "title", "Category Accelerated Benefit")
            eligibility_notes = getattr(top_offer, "exclusion_details", "") or f"Valid on {category.title()}"
            expiry_date = getattr(top_offer, "valid_to", None)
            if getattr(top_offer, "max_benefit_cap", None):
                max_cap = Decimal(str(top_offer.max_benefit_cap))
            if getattr(top_offer, "confidence", None):
                confidence = top_offer.confidence
        else:
            eligibility_notes = f"Offer requires minimum spend of ₹{min_spend:,.2f}; falling back to base rate."

    # Compute raw benefit
    if is_excluded:
        net_benefit = Decimal("0.00")
        breakdown = f"Category '{category}' is excluded from rewards for this card: {exclusion_reason}"
        effective_rate = Decimal("0.00")
    else:
        # If REWARD_POINTS, calculate points and convert to INR
        if reward_type == "REWARD_POINTS":
            # e.g., 4 points per ₹100 spent -> effective rate = (4 * point_value)%
            points_earned = (purchase_amount / Decimal("100")) * best_rate
            raw_benefit = points_earned * point_value
            benefit_unit_desc = f"{best_rate} pts per ₹100 (1 pt = ₹{point_value:,.2f})"
        else:
            # CASHBACK percentage
            raw_benefit = (purchase_amount * best_rate) / Decimal("100")
            benefit_unit_desc = f"{best_rate}% cashback"

        # Apply maximum benefit cap if defined
        if max_cap is not None and raw_benefit > max_cap:
            net_benefit = max_cap
            breakdown = (
                f"Calculated benefit of ₹{raw_benefit:,.2f} ({benefit_unit_desc}) "
                f"exceeded maximum cap. Capped at ₹{max_cap:,.2f}."
            )
        else:
            net_benefit = raw_benefit
            breakdown = f"Earned {benefit_unit_desc} on ₹{purchase_amount:,.2f} = ₹{net_benefit:,.2f}"

        effective_rate = ((net_benefit / purchase_amount) * Decimal("100")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    net_benefit = net_benefit.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    issuer = getattr(card, "issuer", "Bank")
    variant = getattr(card, "variant", "Card")
    nickname = getattr(card, "nickname", None)
    card_name = f"{issuer} {variant}" if not nickname else f"{nickname} ({issuer} {variant})"
    masked = getattr(card, "masked_number", "XXXX-0000")

    return EvaluationResult(
        card_id=str(getattr(card, "id", "")),
        card_name=card_name,
        issuer=issuer,
        variant=variant,
        masked_number=masked,
        estimated_net_benefit_inr=net_benefit,
        effective_rate_percent=effective_rate,
        calculation_breakdown=breakdown,
        applied_rule=applied_rule_name,
        eligibility_conditions=eligibility_notes,
        offer_expiry=expiry_date,
        confidence=confidence
    )

def match_best_cards(
    cards: List[Any],
    offers: List[Any],
    purchase_amount: Decimal,
    category: str,
    merchant: Optional[str] = None,
    transaction_date: Optional[date] = None
) -> List[EvaluationResult]:
    """
    Evaluates all active eligible cards and ranks them in descending order of net INR benefit.
    """
    results: List[EvaluationResult] = []
    for card in cards:
        if getattr(card, "is_archived", False):
            continue
        # Filter offers relevant to this card
        card_offers = [
            o for o in offers 
            if getattr(o, "card_id", None) == getattr(card, "id", None)
            or (getattr(o, "issuer", "").lower() == getattr(card, "issuer", "").lower()
                and (not getattr(o, "variant", None) or getattr(o, "variant", "").lower() == getattr(card, "variant", "").lower()))
        ]
        res = evaluate_card_benefit(
            card=card,
            offers=card_offers,
            purchase_amount=purchase_amount,
            category=category,
            merchant=merchant,
            transaction_date=transaction_date
        )
        results.append(res)

    results.sort(key=lambda r: r.estimated_net_benefit_inr, reverse=True)
    return results
