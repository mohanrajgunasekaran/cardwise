from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.models import User, CreditCard
from app.schemas.schemas import CardCreate, CardUpdate, CardResponse
from app.api.deps import get_current_user

router = APIRouter()

@router.get("", response_model=List[CardResponse])
def list_cards(
    include_archived: bool = Query(False),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    query = db.query(CreditCard).filter(CreditCard.user_id == current_user.id)
    if not include_archived:
        query = query.filter(CreditCard.is_archived == False)
    return query.order_by(CreditCard.created_at.desc()).all()

@router.post("", response_model=CardResponse, status_code=status.HTTP_201_CREATED)
def create_card(
    payload: CardCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    card = CreditCard(
        user_id=current_user.id,
        issuer=payload.issuer,
        variant=payload.variant,
        nickname=payload.nickname,
        masked_number=payload.masked_number,
        network=payload.network,
        credit_limit=payload.credit_limit,
        available_limit=payload.available_limit,
        billing_cycle_day=payload.billing_cycle_day,
        payment_due_days=payload.payment_due_days,
        annual_fee=payload.annual_fee,
        joining_fee=payload.joining_fee,
        reward_type=payload.reward_type,
        base_earn_rate=payload.base_earn_rate,
        point_redemption_inr=payload.point_redemption_inr,
        is_verified=payload.is_verified
    )
    db.add(card)
    db.commit()
    db.refresh(card)
    return card

@router.get("/{card_id}", response_model=CardResponse)
def get_card(
    card_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    card = db.query(CreditCard).filter(
        CreditCard.id == card_id,
        CreditCard.user_id == current_user.id
    ).first()
    if not card:
        raise HTTPException(status_code=404, detail="Credit card not found.")
    return card

@router.put("/{card_id}", response_model=CardResponse)
def update_card(
    card_id: str,
    payload: CardUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    card = db.query(CreditCard).filter(
        CreditCard.id == card_id,
        CreditCard.user_id == current_user.id
    ).first()
    if not card:
        raise HTTPException(status_code=404, detail="Credit card not found.")

    update_data = payload.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(card, field, value)

    db.commit()
    db.refresh(card)
    return card

@router.delete("/{card_id}")
def delete_card(
    card_id: str,
    permanent: bool = Query(False),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    card = db.query(CreditCard).filter(
        CreditCard.id == card_id,
        CreditCard.user_id == current_user.id
    ).first()
    if not card:
        raise HTTPException(status_code=404, detail="Credit card not found.")

    if permanent:
        db.delete(card)
    else:
        card.is_archived = True

    db.commit()
    return {"message": "Card deleted successfully." if permanent else "Card archived."}
