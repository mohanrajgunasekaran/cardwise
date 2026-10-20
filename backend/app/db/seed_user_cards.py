import os
from datetime import date
from decimal import Decimal
from app.db.session import SessionLocal, engine, Base
from app.models.models import User, CreditCard, Statement, CardOffer, CardProductTerms
from app.fixtures.synthetic_cards import (
    SYNTHETIC_CARDS_FIXTURES,
    SYNTHETIC_STATEMENTS_FIXTURES,
    SYNTHETIC_OFFERS_FIXTURES,
    SYNTHETIC_PRODUCT_TERMS_FIXTURES
)
from app.core.security import get_password_hash

def seed():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    demo_email = "demo_user@cardwise.local"
    user = db.query(User).filter(User.email == demo_email).first()
    if not user:
        user = User(
            email=demo_email,
            hashed_password=get_password_hash("Password123!"),
            full_name="CardWise Explorer",
            currency="INR"
        )
        db.add(user)
        db.commit()
        db.refresh(user)

    print(f"Target User: {user.email} ({user.id})")

    card_map = {}
    cards_added = 0
    cards_updated = 0

    for f in SYNTHETIC_CARDS_FIXTURES:
        existing = db.query(CreditCard).filter(
            CreditCard.user_id == user.id,
            CreditCard.issuer == f["issuer"],
            CreditCard.masked_number == f["masked_number"]
        ).first()

        if not existing:
            card = CreditCard(
                id=f["id"],
                user_id=user.id,
                issuer=f["issuer"],
                variant=f["variant"],
                nickname=f.get("nickname"),
                category=f.get("category"),
                masked_number=f["masked_number"],
                network=f["network"],
                credit_limit=f.get("credit_limit"),
                available_limit=f.get("available_limit"),
                billing_cycle_day=f.get("billing_cycle_day"),
                payment_due_days=f.get("payment_due_days"),
                annual_fee=f["annual_fee"],
                joining_fee=f["joining_fee"],
                reward_type=f["reward_type"],
                base_earn_rate=f["base_earn_rate"],
                point_redemption_inr=f["point_redemption_inr"],
                is_verified=f["is_verified"],
                verification_status=f.get("verification_status", "Imported — needs verification"),
                notes=f.get("notes")
            )
            db.add(card)
            card_map[f["id"]] = card
            cards_added += 1
        else:
            existing.category = f.get("category")
            existing.verification_status = f.get("verification_status", existing.verification_status)
            existing.notes = f.get("notes")
            existing.credit_limit = f.get("credit_limit")
            existing.available_limit = f.get("available_limit")
            existing.billing_cycle_day = f.get("billing_cycle_day")
            existing.nickname = f.get("nickname")
            existing.variant = f["variant"]
            card_map[f["id"]] = existing
            cards_updated += 1

    db.commit()

    # Re-fetch cards
    for f in SYNTHETIC_CARDS_FIXTURES:
        c = db.query(CreditCard).filter(
            CreditCard.user_id == user.id,
            CreditCard.issuer == f["issuer"],
            CreditCard.masked_number == f["masked_number"]
        ).first()
        if c:
            card_map[f["id"]] = c

    # Populate statements
    stmts_added = 0
    stmts_updated = 0
    for sf in SYNTHETIC_STATEMENTS_FIXTURES:
        target_card = card_map.get(sf["card_id"])
        if target_card:
            existing_stmt = db.query(Statement).filter(
                Statement.card_id == target_card.id,
                Statement.period_start == sf.get("period_start"),
                Statement.period_end == sf.get("period_end")
            ).first()

            if not existing_stmt:
                stmt = Statement(
                    id=sf.get("id"),
                    card_id=target_card.id,
                    user_id=user.id,
                    statement_date=sf.get("statement_date"),
                    payment_due_date=sf.get("payment_due_date"),
                    period_start=sf.get("period_start"),
                    period_end=sf.get("period_end"),
                    total_balance=sf.get("total_balance"),
                    minimum_due=sf.get("minimum_due"),
                    is_paid=False,
                    is_credit_balance=sf.get("is_credit_balance", False),
                    is_historical=sf.get("is_historical", False),
                    source=sf.get("source", "STATEMENT_IMPORT"),
                    notes=sf.get("notes")
                )
                db.add(stmt)
                stmts_added += 1
            else:
                existing_stmt.total_balance = sf.get("total_balance")
                existing_stmt.minimum_due = sf.get("minimum_due")
                existing_stmt.statement_date = sf.get("statement_date")
                existing_stmt.payment_due_date = sf.get("payment_due_date")
                existing_stmt.is_credit_balance = sf.get("is_credit_balance", False)
                existing_stmt.is_historical = sf.get("is_historical", False)
                existing_stmt.notes = sf.get("notes")
                stmts_updated += 1

    # Offers
    for off in SYNTHETIC_OFFERS_FIXTURES:
        exist_offer = db.query(CardOffer).filter(CardOffer.title == off["title"]).first()
        if not exist_offer:
            offer = CardOffer(
                issuer=off["issuer"],
                variant=off.get("variant"),
                title=off["title"],
                category=off["category"],
                merchant_keyword=off.get("merchant_keyword"),
                benefit_type=off["benefit_type"],
                benefit_value=off["benefit_value"],
                min_spend=off["min_spend"],
                max_benefit_cap=off.get("max_benefit_cap"),
                exclusion_details=off.get("exclusion_details"),
                valid_from=off["valid_from"],
                valid_to=off["valid_to"],
                confidence=off["confidence"]
            )
    # Product Terms
    terms_added = 0
    terms_updated = 0
    for tf in SYNTHETIC_PRODUCT_TERMS_FIXTURES:
        target_card = card_map.get(tf["card_id"])
        if target_card:
            existing_term = db.query(CardProductTerms).filter(CardProductTerms.card_id == target_card.id).first()
            if not existing_term:
                term = CardProductTerms(
                    id=tf["id"],
                    card_id=target_card.id,
                    issuer=tf["issuer"],
                    card_name=tf["card_name"],
                    exact_variant=tf.get("exact_variant"),
                    masked_card_number=tf.get("masked_card_number"),
                    network=tf.get("network"),
                    variant_verification_status=tf.get("variant_verification_status", "Unverified"),
                    joining_fee=tf.get("joining_fee"),
                    annual_fee=tf.get("annual_fee"),
                    renewal_fee=tf.get("renewal_fee"),
                    annual_fee_waiver_threshold=tf.get("annual_fee_waiver_threshold"),
                    waiver_period_and_conditions=tf.get("waiver_period_and_conditions"),
                    interest_rate_monthly=tf.get("interest_rate_monthly"),
                    interest_rate_annual=tf.get("interest_rate_annual"),
                    late_payment_fee_structure=tf.get("late_payment_fee_structure"),
                    cash_advance_fee=tf.get("cash_advance_fee"),
                    cash_advance_interest_terms=tf.get("cash_advance_interest_terms"),
                    forex_markup=tf.get("forex_markup"),
                    over_limit_fee=tf.get("over_limit_fee"),
                    emi_processing_fee=tf.get("emi_processing_fee"),
                    emi_foreclosure_terms=tf.get("emi_foreclosure_terms"),
                    fuel_surcharge_terms=tf.get("fuel_surcharge_terms"),
                    other_charges=tf.get("other_charges"),
                    applicable_gst_notes=tf.get("applicable_gst_notes"),
                    reward_type=tf.get("reward_type"),
                    reward_rate=tf.get("reward_rate"),
                    eligible_spend_categories=tf.get("eligible_spend_categories"),
                    excluded_spend_categories=tf.get("excluded_spend_categories"),
                    reward_point_value=tf.get("reward_point_value"),
                    cashback_cap=tf.get("cashback_cap"),
                    reward_expiry=tf.get("reward_expiry"),
                    redemption_method=tf.get("redemption_method"),
                    milestone_benefits=tf.get("milestone_benefits"),
                    welcome_benefits=tf.get("welcome_benefits"),
                    airport_lounge_access=tf.get("airport_lounge_access"),
                    railway_lounge_access=tf.get("railway_lounge_access"),
                    lounge_eligibility_conditions=tf.get("lounge_eligibility_conditions"),
                    travel_benefits=tf.get("travel_benefits"),
                    dining_and_entertainment_benefits=tf.get("dining_and_entertainment_benefits"),
                    insurance_and_purchase_protection=tf.get("insurance_and_purchase_protection"),
                    benefit_validity=tf.get("benefit_validity"),
                    benefit_terms=tf.get("benefit_terms"),
                    source_url=tf.get("source_url"),
                    source_title=tf.get("source_title"),
                    source_type=tf.get("source_type"),
                    date_verified=tf.get("date_verified"),
                    effective_date=tf.get("effective_date"),
                    verification_status=tf.get("verification_status", "Unverified"),
                    confidence_notes=tf.get("confidence_notes"),
                    unresolved_questions=tf.get("unresolved_questions")
                )
                db.add(term)
                terms_added += 1
            else:
                for key, val in tf.items():
                    if key not in ("id", "card_id"):
                        setattr(existing_term, key, val)
                terms_updated += 1

    db.commit()

    all_cards = db.query(CreditCard).filter(CreditCard.user_id == user.id).all()
    all_stmts = db.query(Statement).filter(Statement.user_id == user.id).all()

    print(f"\nSeeding summary:")
    print(f"- Cards added: {cards_added}, updated: {cards_updated}. Total in DB: {len(all_cards)}")
    print(f"- Statements added: {stmts_added}, updated: {stmts_updated}. Total in DB: {len(all_stmts)}")
    print(f"\nImported Cards verification list:")
    for idx, c in enumerate(all_cards, 1):
        print(f"  {idx}. {c.issuer} | {c.variant} | {c.masked_number} | Category: {c.category} | Limit: {c.credit_limit} | Status: {c.verification_status}")

    print(f"\nImported Statements list:")
    for s in all_stmts:
        print(f"  - Card ID: {s.card_id} | Due: {s.payment_due_date} | Total Balance: {s.total_balance} | Min Due: {s.minimum_due} | Credit Bal: {s.is_credit_balance} | Historical: {s.is_historical}")

    db.close()

if __name__ == "__main__":
    seed()
