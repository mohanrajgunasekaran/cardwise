from typing import List, Optional
from datetime import date, timedelta
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.models import CardOffer
from app.api.deps import get_current_user

router = APIRouter()

@router.get("")
def list_offers(
    category: Optional[str] = Query(None),
    issuer: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    query = db.query(CardOffer).filter(CardOffer.valid_to >= date.today())
    if category:
        query = query.filter(CardOffer.category == category.upper())
    if issuer:
        query = query.filter(CardOffer.issuer.ilike(f"%{issuer}%"))
    return query.order_by(CardOffer.valid_to.asc()).all()

@router.get("/expiring")
def list_expiring_offers(
    days: int = Query(14, ge=1, le=60),
    db: Session = Depends(get_db)
):
    cutoff = date.today() + timedelta(days=days)
    offers = db.query(CardOffer).filter(
        CardOffer.valid_to >= date.today(),
        CardOffer.valid_to <= cutoff
    ).order_by(CardOffer.valid_to.asc()).all()
    return offers
