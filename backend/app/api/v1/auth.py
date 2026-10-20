from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.models import User, CreditCard, CardOffer
from app.schemas.schemas import UserRegister, UserLogin, Token, UserResponse
from app.core.security import verify_password, get_password_hash, create_access_token, create_refresh_token
from app.api.deps import get_current_user
from app.fixtures.synthetic_cards import SYNTHETIC_CARDS_FIXTURES, SYNTHETIC_OFFERS_FIXTURES

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
    Explicitly populates the 10 synthetic credit card fixtures for the authenticated user.
    Production builds never auto-load demonstration records without user intent.
    """
    added_cards = 0
    for fixture in SYNTHETIC_CARDS_FIXTURES:
        existing = db.query(CreditCard).filter(
            CreditCard.user_id == current_user.id,
            CreditCard.issuer == fixture["issuer"],
            CreditCard.masked_number == fixture["masked_number"]
        ).first()
        if not existing:
            card = CreditCard(
                user_id=current_user.id,
                issuer=fixture["issuer"],
                variant=fixture["variant"],
                nickname=fixture.get("nickname"),
                masked_number=fixture["masked_number"],
                network=fixture["network"],
                credit_limit=fixture.get("credit_limit"),
                available_limit=fixture.get("available_limit"),
                billing_cycle_day=fixture["billing_cycle_day"],
                payment_due_days=fixture["payment_due_days"],
                annual_fee=fixture["annual_fee"],
                joining_fee=fixture["joining_fee"],
                reward_type=fixture["reward_type"],
                base_earn_rate=fixture["base_earn_rate"],
                point_redemption_inr=fixture["point_redemption_inr"],
                is_verified=fixture["is_verified"]
            )
            db.add(card)
            added_cards += 1

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

    db.commit()
    return {"message": f"Successfully loaded {added_cards} synthetic demonstration cards."}
