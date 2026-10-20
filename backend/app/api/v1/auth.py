from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.models import User, CreditCard, CardOffer, Statement, CardProductTerms, SourceDocument, CardBenefitRecord, CardFeeRecord
from app.schemas.schemas import UserRegister, UserLogin, Token, UserResponse
from app.core.security import verify_password, get_password_hash, create_access_token, create_refresh_token
from app.api.deps import get_current_user
from app.fixtures.synthetic_cards import (
    SYNTHETIC_CARDS_FIXTURES,
    SYNTHETIC_OFFERS_FIXTURES,
    SYNTHETIC_STATEMENTS_FIXTURES,
    SYNTHETIC_PRODUCT_TERMS_FIXTURES
)
from app.fixtures.official_documents_catalog import OFFICIAL_DOCUMENTS_CATALOG
from app.fixtures.granular_benefits_fees import SYNTHETIC_BENEFITS_FIXTURES, SYNTHETIC_FEES_FIXTURES

router = APIRouter()

@router.post("/register", response_model=UserResponse)
def register_user(payload: UserRegister, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.email == payload.email.lower()).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A user with this email already exists."
        )
    user = User(
        email=payload.email.lower(),
        hashed_password=get_password_hash(payload.password),
        full_name=payload.full_name,
        currency="INR"
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

@router.post("/login", response_model=Token)
def login(payload: UserLogin, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email.lower()).first()
    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return Token(
        access_token=create_access_token(user.id),
        refresh_token=create_refresh_token(user.id),
        token_type="bearer"
    )

@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    return current_user

@router.post("/seed-demo-data")
def seed_demo_data(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Explicitly populates the 10 credit card fixtures and statements for the authenticated user.
    """
    added_cards = 0
    card_map = {}

    for fixture in SYNTHETIC_CARDS_FIXTURES:
        existing = db.query(CreditCard).filter(
            CreditCard.user_id == current_user.id,
            CreditCard.issuer == fixture["issuer"],
            CreditCard.masked_number == fixture["masked_number"]
        ).first()

        if not existing:
            card_pk = fixture["id"]
            if db.query(CreditCard).filter(CreditCard.id == card_pk).first():
                card_pk = f"{fixture['id']}-{current_user.id[:8]}"
            card = CreditCard(
                id=card_pk,
                user_id=current_user.id,
                issuer=fixture["issuer"],
                variant=fixture["variant"],
                nickname=fixture.get("nickname"),
                category=fixture.get("category"),
                masked_number=fixture["masked_number"],
                network=fixture["network"],
                credit_limit=fixture.get("credit_limit"),
                available_limit=fixture.get("available_limit"),
                billing_cycle_day=fixture.get("billing_cycle_day"),
                payment_due_days=fixture.get("payment_due_days"),
                annual_fee=fixture["annual_fee"],
                joining_fee=fixture["joining_fee"],
                reward_type=fixture["reward_type"],
                base_earn_rate=fixture["base_earn_rate"],
                point_redemption_inr=fixture["point_redemption_inr"],
                is_verified=fixture["is_verified"],
                verification_status=fixture.get("verification_status", "Imported — needs verification"),
                notes=fixture.get("notes")
            )
            db.add(card)
            card_map[fixture["id"]] = card
            added_cards += 1
        else:
            # Update fields if needed
            existing.category = fixture.get("category")
            existing.verification_status = fixture.get("verification_status", existing.verification_status)
            existing.notes = fixture.get("notes")
            card_map[fixture["id"]] = existing

    # Commit cards first so foreign key constraints are met
    db.commit()

    # Re-fetch cards to ensure ID availability
    for fixture in SYNTHETIC_CARDS_FIXTURES:
        if fixture["id"] not in card_map or not card_map[fixture["id"]].id:
            c = db.query(CreditCard).filter(
                CreditCard.user_id == current_user.id,
                CreditCard.issuer == fixture["issuer"],
                CreditCard.masked_number == fixture["masked_number"]
            ).first()
            if c:
                card_map[fixture["id"]] = c

    # Populate statements for imported cards
    added_statements = 0
    for stmt_fixture in SYNTHETIC_STATEMENTS_FIXTURES:
        target_card = card_map.get(stmt_fixture["card_id"])
        if target_card:
            existing_stmt = db.query(Statement).filter(
                Statement.card_id == target_card.id,
                Statement.period_start == stmt_fixture.get("period_start"),
                Statement.period_end == stmt_fixture.get("period_end")
            ).first()

            if not existing_stmt:
                stmt_pk = stmt_fixture.get("id")
                if stmt_pk and db.query(Statement).filter(Statement.id == stmt_pk).first():
                    stmt_pk = f"{stmt_pk}-{current_user.id[:8]}"
                stmt = Statement(
                    id=stmt_pk,
                    card_id=target_card.id,
                    user_id=current_user.id,
                    statement_date=stmt_fixture.get("statement_date"),
                    payment_due_date=stmt_fixture.get("payment_due_date"),
                    period_start=stmt_fixture.get("period_start"),
                    period_end=stmt_fixture.get("period_end"),
                    total_balance=stmt_fixture.get("total_balance"),
                    minimum_due=stmt_fixture.get("minimum_due"),
                    is_paid=False,
                    is_credit_balance=stmt_fixture.get("is_credit_balance", False),
                    is_historical=stmt_fixture.get("is_historical", False),
                    source=stmt_fixture.get("source", "STATEMENT_IMPORT"),
                    notes=stmt_fixture.get("notes")
                )
                db.add(stmt)
                added_statements += 1

    # Populate offers catalog
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
            db.add(offer)

    # Populate official source documents
    for doc_data in OFFICIAL_DOCUMENTS_CATALOG:
        existing_doc = db.query(SourceDocument).filter(SourceDocument.id == doc_data["id"]).first()
        if not existing_doc:
            doc = SourceDocument(
                id=doc_data["id"],
                document_title=doc_data["document_title"],
                file_name=doc_data["file_name"],
                official_url=doc_data.get("official_url"),
                issuer=doc_data["issuer"],
                covered_card_variants=", ".join(doc_data["covered_card_variants"]) if isinstance(doc_data["covered_card_variants"], list) else doc_data["covered_card_variants"],
                document_type=doc_data["document_type"],
                version_or_date=doc_data.get("version_or_date"),
                effective_date=doc_data.get("effective_date"),
                retrieval_date=doc_data.get("retrieval_date"),
                verification_status=doc_data["verification_status"],
                is_current=doc_data.get("is_current", True),
                superseded_by_id=doc_data.get("superseded_by_id"),
                relevant_pages_or_sections=doc_data.get("relevant_pages_or_sections"),
                summary=doc_data.get("summary")
            )
            db.add(doc)

    # Populate product terms
    for term_fixture in SYNTHETIC_PRODUCT_TERMS_FIXTURES:
        target_card = card_map.get(term_fixture["card_id"])
        if target_card:
            existing_term = db.query(CardProductTerms).filter(CardProductTerms.card_id == target_card.id).first()
            if not existing_term:
                term_pk = term_fixture["id"]
                if db.query(CardProductTerms).filter(CardProductTerms.id == term_pk).first():
                    term_pk = f"{term_pk}-{current_user.id[:8]}"
                term = CardProductTerms(
                    id=term_pk,
                    card_id=target_card.id,
                    source_document_id=term_fixture.get("source_document_id"),
                    issuer=term_fixture["issuer"],
                    card_name=term_fixture["card_name"],
                    exact_variant=term_fixture.get("exact_variant"),
                    masked_card_number=term_fixture.get("masked_card_number"),
                    network=term_fixture.get("network"),
                    variant_verification_status=term_fixture.get("variant_verification_status", "Unverified"),
                    joining_fee=term_fixture.get("joining_fee"),
                    annual_fee=term_fixture.get("annual_fee"),
                    renewal_fee=term_fixture.get("renewal_fee"),
                    annual_fee_waiver_threshold=term_fixture.get("annual_fee_waiver_threshold"),
                    waiver_period_and_conditions=term_fixture.get("waiver_period_and_conditions"),
                    interest_rate_monthly=term_fixture.get("interest_rate_monthly"),
                    interest_rate_annual=term_fixture.get("interest_rate_annual"),
                    late_payment_fee_structure=term_fixture.get("late_payment_fee_structure"),
                    cash_advance_fee=term_fixture.get("cash_advance_fee"),
                    cash_advance_interest_terms=term_fixture.get("cash_advance_interest_terms"),
                    forex_markup=term_fixture.get("forex_markup"),
                    over_limit_fee=term_fixture.get("over_limit_fee"),
                    emi_processing_fee=term_fixture.get("emi_processing_fee"),
                    emi_foreclosure_terms=term_fixture.get("emi_foreclosure_terms"),
                    fuel_surcharge_terms=term_fixture.get("fuel_surcharge_terms"),
                    other_charges=term_fixture.get("other_charges"),
                    applicable_gst_notes=term_fixture.get("applicable_gst_notes"),
                    reward_type=term_fixture.get("reward_type"),
                    reward_rate=term_fixture.get("reward_rate"),
                    eligible_spend_categories=term_fixture.get("eligible_spend_categories"),
                    excluded_spend_categories=term_fixture.get("excluded_spend_categories"),
                    reward_point_value=term_fixture.get("reward_point_value"),
                    cashback_cap=term_fixture.get("cashback_cap"),
                    reward_expiry=term_fixture.get("reward_expiry"),
                    redemption_method=term_fixture.get("redemption_method"),
                    milestone_benefits=term_fixture.get("milestone_benefits"),
                    welcome_benefits=term_fixture.get("welcome_benefits"),
                    airport_lounge_access=term_fixture.get("airport_lounge_access"),
                    railway_lounge_access=term_fixture.get("railway_lounge_access"),
                    lounge_eligibility_conditions=term_fixture.get("lounge_eligibility_conditions"),
                    travel_benefits=term_fixture.get("travel_benefits"),
                    dining_and_entertainment_benefits=term_fixture.get("dining_and_entertainment_benefits"),
                    insurance_and_purchase_protection=term_fixture.get("insurance_and_purchase_protection"),
                    benefit_validity=term_fixture.get("benefit_validity"),
                    benefit_terms=term_fixture.get("benefit_terms"),
                    source_url=term_fixture.get("source_url"),
                    source_title=term_fixture.get("source_title"),
                    source_type=term_fixture.get("source_type"),
                    date_verified=term_fixture.get("date_verified"),
                    effective_date=term_fixture.get("effective_date"),
                    verification_status=term_fixture.get("verification_status", "Unverified"),
                    confidence_notes=term_fixture.get("confidence_notes"),
                    unresolved_questions=term_fixture.get("unresolved_questions"),
                    document_citation=term_fixture.get("document_citation"),
                    last_checked_date=term_fixture.get("last_checked_date"),
                    superseded_status=term_fixture.get("superseded_status")
                )
                db.add(term)
            else:
                for key, val in term_fixture.items():
                    if key not in ("id", "card_id"):
                        setattr(existing_term, key, val)

    # Populate granular benefits
    for b_data in SYNTHETIC_BENEFITS_FIXTURES:
        target_card = card_map.get(b_data["card_id"])
        if target_card:
            b_pk = f"{b_data['id']}-{target_card.id[-6:]}"
            existing_b = db.query(CardBenefitRecord).filter(CardBenefitRecord.id == b_pk).first()
            if not existing_b:
                b_rec = CardBenefitRecord(
                    id=b_pk,
                    card_id=target_card.id,
                    source_document_id=b_data.get("source_document_id"),
                    benefit_category=b_data["benefit_category"],
                    title=b_data["title"],
                    description=b_data["description"],
                    reward_rate_or_cashback=b_data.get("reward_rate_or_cashback"),
                    cap=b_data.get("cap"),
                    eligibility_requirements=b_data.get("eligibility_requirements"),
                    exclusions=b_data.get("exclusions"),
                    redemption_value=b_data.get("redemption_value"),
                    validity_dates=b_data.get("validity_dates"),
                    status_label=b_data.get("status_label", "Verified against current official document")
                )
                db.add(b_rec)

    # Populate granular fees
    for f_data in SYNTHETIC_FEES_FIXTURES:
        target_card = card_map.get(f_data["card_id"])
        if target_card:
            f_pk = f"{f_data['id']}-{target_card.id[-6:]}"
            existing_f = db.query(CardFeeRecord).filter(CardFeeRecord.id == f_pk).first()
            if not existing_f:
                f_rec = CardFeeRecord(
                    id=f_pk,
                    card_id=target_card.id,
                    source_document_id=f_data.get("source_document_id"),
                    charge_category=f_data["charge_category"],
                    charge_name=f_data["charge_name"],
                    amount_or_percentage=f_data["amount_or_percentage"],
                    min_amount=f_data.get("min_amount"),
                    max_amount=f_data.get("max_amount"),
                    calculation_basis=f_data.get("calculation_basis"),
                    conditions=f_data.get("conditions"),
                    gst_treatment=f_data.get("gst_treatment", "18% GST applicable"),
                    effective_start_date=f_data.get("effective_start_date"),
                    effective_end_date=f_data.get("effective_end_date"),
                    status_label=f_data.get("status_label", "Verified against current official document")
                )
                db.add(f_rec)

    db.commit()
    total_cards = db.query(CreditCard).filter(CreditCard.user_id == current_user.id).count()
    total_stmts = db.query(Statement).filter(Statement.user_id == current_user.id).count()
    return {
        "message": f"Successfully loaded {total_cards} credit cards and {total_stmts} statements with verified documents and terms.",
        "cards_count": total_cards,
        "statements_count": total_stmts
    }
