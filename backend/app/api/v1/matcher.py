from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.models import User, CreditCard, CardOffer
from app.schemas.schemas import MatcherRequest, MatcherResponse, MatcherRecommendation
from app.api.deps import get_current_user
from app.services.matching_engine import match_best_cards

router = APIRouter()

@router.post("/recommend", response_model=MatcherResponse)
def recommend_best_card(
    payload: MatcherRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    cards = db.query(CreditCard).filter(
        CreditCard.user_id == current_user.id,
        CreditCard.is_archived == False
    ).all()

    if not cards:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No active credit cards found in your wallet. Please add a card first."
        )

    offers = db.query(CardOffer).all()

    results = match_best_cards(
        cards=cards,
        offers=offers,
        purchase_amount=payload.purchase_amount,
        category=payload.category,
        merchant=payload.merchant,
        transaction_date=payload.transaction_date
    )

    best_card_id = results[0].card_id if results else None

    recommendations = [
        MatcherRecommendation(
            card_id=r.card_id,
            card_name=r.card_name,
            issuer=r.issuer,
            variant=r.variant,
            masked_number=r.masked_number,
            estimated_net_benefit_inr=r.estimated_net_benefit_inr,
            effective_rate_percent=r.effective_rate_percent,
            calculation_breakdown=r.calculation_breakdown,
            applied_rule=r.applied_rule,
            eligibility_conditions=r.eligibility_conditions,
            offer_expiry=r.offer_expiry,
            confidence=r.confidence
        )
        for r in results
    ]

    return MatcherResponse(
        purchase_amount=payload.purchase_amount,
        category=payload.category,
        merchant=payload.merchant,
        best_card_id=best_card_id,
        recommendations=recommendations
    )
