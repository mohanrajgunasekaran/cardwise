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
    Enforces official product terms, category exclusions, reward caps, and distinguishes
    estimated net rewards from guaranteed savings.
    Returns 'Insufficient verified data' when the exact card variant or terms are unknown.
    """
    if transaction_date is None:
        transaction_date = date.today()

    norm_category = category.strip().upper()
    norm_merchant = merchant.strip().lower() if merchant else ""

    issuer = getattr(card, "issuer", "Bank")
    variant = getattr(card, "variant", "Card")
    nickname = getattr(card, "nickname", None)
    card_name = f"{issuer} {variant}" if not nickname else f"{nickname} ({issuer} {variant})"
    masked = getattr(card, "masked_number", "XXXX-0000")

    # Check Product Terms
    terms = getattr(card, "product_terms", None)
    terms_status = getattr(terms, "variant_verification_status", "") if terms else ""
    variant_lower = variant.lower()

    if terms is not None:
        is_variant_unverified = (
            "unverified" in terms_status.lower()
            or not getattr(terms, "exact_variant", None)
            or "variant unknown" in variant_lower
            or "variant unverified" in variant_lower
        )
    else:
        # Fallback for test mock objects or cards without populated product_terms
        is_variant_unverified = (
            "unknown" in variant_lower
            or "unverified" in variant_lower
            or not getattr(card, "is_verified", True)
        )

    # If variant is unverified, strictly return Insufficient Verified Data
    if is_variant_unverified:
        return EvaluationResult(
            card_id=str(getattr(card, "id", "")),
            card_name=card_name,
            issuer=issuer,
            variant=variant,
            masked_number=masked,
            estimated_net_benefit_inr=Decimal("0.00"),
            effective_rate_percent=Decimal("0.00"),
            calculation_breakdown=(
                "Insufficient verified data: Exact product variant is unverified. "
                "Benefits and reward calculations are withheld until the card variant is confirmed via statement or welcome documentation."
            ),
            applied_rule="Insufficient Verified Data",
            eligibility_conditions="Verification required: Card variant unverified. No assumptions made.",
            offer_expiry=None,
            confidence="UNVERIFIED"
        )

    # Base properties from card / verified terms
    reward_type = (getattr(terms, "reward_type", None) or getattr(card, "reward_type", "CASHBACK")).upper()
    point_value = Decimal(str(getattr(terms, "reward_point_value", None) or getattr(card, "point_redemption_inr", 0.25)))
    base_rate = Decimal(str(getattr(card, "base_earn_rate", 1.00)))

    # Identify matching offers for this card and category/merchant
    applicable_offers = []
    for offer in offers:
        v_from = getattr(offer, "valid_from", None)
        v_to = getattr(offer, "valid_to", None)
        if v_from and transaction_date < v_from:
            continue
        if v_to and transaction_date > v_to:
            continue

        off_cat = getattr(offer, "category", "").upper()
        if off_cat != norm_category and off_cat != "ALL":
            continue

        off_merch = (getattr(offer, "merchant_keyword", "") or "").lower()
        if off_merch and off_merch not in norm_merchant:
            continue

        applicable_offers.append(offer)

    # Check category exclusions
    excluded_cats_str = (getattr(terms, "excluded_spend_categories", "") or "").lower()
    is_excluded = False
    exclusion_reason = ""

    if norm_category == "FUEL":
        if applicable_offers and any("surcharge" in getattr(o, "title", "").lower() for o in applicable_offers):
            is_excluded = False
        else:
            is_excluded = True
            exclusion_reason = "Fuel purchases commonly excluded from reward points accrual"
    else:
        cat_keywords_map = {
            "RENT": ["rent", "rental"],
            "WALLET": ["wallet", "prepaid"],
            "UTILITIES": ["utility", "utilities", "electricity"],
            "EDUCATION": ["education", "school"],
            "GOVERNMENT": ["government", "taxes", "tax"],
            "CASH": ["cash advance", "atm", "cash"],
            "EMI": ["emi", "smart emi", "dial-an-emi"],
            "INSURANCE": ["insurance"]
        }
        for cat_key, kws in cat_keywords_map.items():
            if norm_category == cat_key or cat_key.lower() in norm_category.lower():
                for kw in kws:
                    if kw in excluded_cats_str:
                        is_excluded = True
                        exclusion_reason = f"Excluded under official card terms: {terms.excluded_spend_categories}"
                        break

    # Determine best rate and applied rule
    best_rate = base_rate
    applied_rule_name = f"Verified Base {base_rate}% {reward_type.title()}"
    eligibility_notes = "Official verified product terms base reward"
    expiry_date = None
    max_cap: Optional[Decimal] = None
    confidence = "VERIFIED"

    # Specific verified product rules
    exact_variant = (getattr(terms, "exact_variant", "") or "").lower()

    if "amazon pay" in exact_variant:
        if "amazon" in norm_merchant:
            best_rate = Decimal("5.00")
            applied_rule_name = "Amazon Prime 5% Unlimited Cashback (Amazon Spends)"
            eligibility_notes = "Requires active Amazon Prime membership; credited to Amazon Pay balance."
        elif norm_category in ("BILLS", "UTILITIES") or "recharge" in norm_merchant or "flight" in norm_merchant:
            best_rate = Decimal("2.00")
            applied_rule_name = "2% Unlimited Cashback on Bill Payments & Partner Merchants"
            eligibility_notes = "100+ Amazon Pay partner merchants and utility bill payments."
        else:
            best_rate = Decimal("1.00")
            applied_rule_name = "1% Unlimited Cashback on All Other Retail Spends"
            eligibility_notes = "Standard retail spend; fuel, wallet load and EMI excluded."
    elif "shoprite" in exact_variant:
        if norm_category in ("GROCERIES", "SUPERMARKET"):
            # 20 points per Rs 100 spent = 5% value back
            best_rate = Decimal("5.00")
            applied_rule_name = "5% Value Back on Groceries (20 Reward Points per ₹100)"
            eligibility_notes = "Max 1,000 reward points (₹250 value) per monthly billing cycle."
            max_cap = Decimal("250.00")
        else:
            best_rate = Decimal("0.25")
            applied_rule_name = "1 Reward Point per ₹100 Spent (0.25% Value Back)"
            eligibility_notes = "Standard retail spends; fuel, utilities, and wallet excluded."
    elif "lic first select" in exact_variant:
        if norm_category == "INSURANCE" or "lic" in norm_merchant:
            # 10X reward points = 2.50%
            best_rate = Decimal("2.50")
            applied_rule_name = "10X Reward Points on LIC Insurance Premium Payments"
            eligibility_notes = "10 pts per ₹125 spent (₹0.25/pt) via LIC payment portal / app."
        else:
            best_rate = Decimal("1.50")
            applied_rule_name = "6X Reward Points on Incremental Retail Spends"
            eligibility_notes = "6 pts per ₹125 spent up to ₹20k monthly spend threshold."
    elif "lit" in exact_variant:
        # AU LIT base: 1 pt per Rs 100
        best_rate = Decimal("0.25")
        applied_rule_name = "Base 1 Reward Point per ₹100 Spent (0.25% Value)"
        eligibility_notes = "AU LIT base rate. Optional 5X/10X or 2%/5% cashback are 90-day active boosters in AU 0101 app."
    elif "coral" in exact_variant:
        if norm_category in ("ENTERTAINMENT", "MOVIES") or "bookmyshow" in norm_merchant or "inox" in norm_merchant:
            best_rate = Decimal("25.00")
            applied_rule_name = "25% Movie Discount on BookMyShow / INOX"
            eligibility_notes = "Buy 1 Get 1 up to ₹100 off per ticket, max 2 times per month."
            max_cap = Decimal("100.00")
        elif norm_category == "DINING":
            best_rate = Decimal("15.00")
            applied_rule_name = "ICICI Culinary Treats: Up to 15% Savings at Partner Dining"
            eligibility_notes = "Valid at participating restaurants via ICICI Culinary Treats."
            max_cap = Decimal("500.00")
        elif norm_category in ("UTILITIES", "INSURANCE"):
            best_rate = Decimal("0.25")
            applied_rule_name = "1 Reward Point per ₹100 Spent on Utilities & Insurance (0.25% Value)"
            eligibility_notes = "Reduced rate for utility and insurance MCCs."
        else:
            best_rate = Decimal("0.50")
            applied_rule_name = "2 Reward Points per ₹100 Spent on General Retail (0.50% Value)"
            eligibility_notes = "2 PAYBACK/ICICI Rewards per ₹100 spent (₹0.25 per point)."
    elif "ace" in exact_variant:
        if "online" in norm_category.lower() or "shopping" in norm_category.lower() or "amazon" in norm_merchant or "flipkart" in norm_merchant:
            best_rate = Decimal("1.00")
            applied_rule_name = "8 Reward Points per ₹200 on Online Retail (1.00% Value)"
            eligibility_notes = "YES Bank ACE online spend accelerator (₹0.25 per point)."
        elif norm_category in ("UTILITIES", "RENT", "INSURANCE", "FUEL", "EDUCATION"):
            best_rate = Decimal("0.125")
            applied_rule_name = "1 Reward Point per ₹200 on Utilities/Rent/Gov/Edu (0.125% Value)"
            eligibility_notes = "Standard category capping applies."
        else:
            best_rate = Decimal("0.50")
            applied_rule_name = "4 Reward Points per ₹200 on Offline Retail (0.50% Value)"
            eligibility_notes = "4 YES Rewardz per ₹200 spent (₹0.25 per point)."
    elif "lazypay" in exact_variant:
        best_rate = Decimal("1.00")
        applied_rule_name = "1% Flat Cashback (Capped at ₹500/Month)"
        eligibility_notes = "Discontinued product with grandfathered active terms; max ₹500/cycle."
        max_cap = Decimal("500.00")

    # If applicable marketing offers override or supplement
    if applicable_offers and not is_excluded:
        applicable_offers.sort(key=lambda o: getattr(o, "benefit_value", Decimal("0")), reverse=True)
        top_offer = applicable_offers[0]
        min_spend = Decimal(str(getattr(top_offer, "min_spend", 0)))
        if purchase_amount >= min_spend:
            offer_rate = Decimal(str(getattr(top_offer, "benefit_value", 0)))
            if offer_rate > best_rate:
                best_rate = offer_rate
                applied_rule_name = getattr(top_offer, "title", "Promotional Offer")
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
        raw_benefit = (purchase_amount * best_rate) / Decimal("100")
        if max_cap is not None and raw_benefit > max_cap:
            net_benefit = max_cap
            breakdown = (
                f"Calculated benefit of ₹{raw_benefit:,.2f} exceeded maximum cap. Capped at ₹{max_cap:,.2f}. "
                f"Estimated Net Reward (Not Guaranteed): ₹{net_benefit:,.2f} "
                f"({best_rate}% effective yield capped at ₹{max_cap:,.2f} per cycle limit). "
                f"Savings are estimated based on verified product terms and subject to issuer settlement."
            )
        else:
            net_benefit = raw_benefit
            breakdown = (
                f"Estimated Net Reward (Not Guaranteed): ₹{net_benefit:,.2f} "
                f"({best_rate}% effective reward on ₹{purchase_amount:,.2f}). "
                f"Savings are estimated based on verified product terms and subject to issuer settlement."
            )

        effective_rate = ((net_benefit / purchase_amount) * Decimal("100")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    net_benefit = net_benefit.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

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
    Evaluates all active cards and ranks them:
    1. Verified cards with positive net benefit ranked descending.
    2. Verified cards with zero benefit / exclusions.
    3. Unverified cards with Insufficient Verified Data at the bottom.
    """
    results: List[EvaluationResult] = []
    for card in cards:
        if getattr(card, "is_archived", False):
            continue
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

    # Sort: Verified positive benefit first, then zero/excluded, then UNVERIFIED
    def sort_key(r: EvaluationResult):
        is_unverified = 1 if r.confidence == "UNVERIFIED" else 0
        return (is_unverified, -r.estimated_net_benefit_inr, -r.effective_rate_percent)

    results.sort(key=sort_key)
    return results
