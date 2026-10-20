from typing import List, Optional
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.models import User, Statement, Payment
from app.schemas.schemas import PaymentCreate, PaymentConfirm, PaymentResponse
from app.api.deps import get_current_user

router = APIRouter()

@router.get("", response_model=List[PaymentResponse])
def list_payments(
    statement_id: Optional[str] = Query(None),
    status_filter: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    query = db.query(Payment).filter(Payment.user_id == current_user.id)
    if statement_id:
        query = query.filter(Payment.statement_id == statement_id)
    if status_filter:
        query = query.filter(Payment.status == status_filter.upper())
    return query.order_by(Payment.planned_date.desc()).all()

@router.post("", response_model=PaymentResponse, status_code=status.HTTP_201_CREATED)
def create_payment(
    payload: PaymentCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    statement = db.query(Statement).filter(
        Statement.id == payload.statement_id,
        Statement.user_id == current_user.id
    ).first()
    if not statement:
        raise HTTPException(status_code=404, detail="Associated statement not found.")

    payment = Payment(
        statement_id=payload.statement_id,
        user_id=current_user.id,
        amount=payload.amount,
        planned_date=payload.planned_date,
        status="PLANNED",
        notes=payload.notes
    )
    db.add(payment)
    db.commit()
    db.refresh(payment)
    return payment

@router.post("/{payment_id}/confirm", response_model=PaymentResponse)
def confirm_payment(
    payment_id: str,
    payload: PaymentConfirm,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Explicitly marks a planned payment as confirmed.
    Only user-entered confirmation or verified event transitions a payment to CONFIRMED.
    """
    payment = db.query(Payment).filter(
        Payment.id == payment_id,
        Payment.user_id == current_user.id
    ).first()
    if not payment:
        raise HTTPException(status_code=404, detail="Payment record not found.")

    payment.status = "CONFIRMED"
    payment.confirmed_at = datetime.now(timezone.utc)
    if payload.notes:
        payment.notes = payload.notes

    db.commit()
    db.refresh(payment)
    return payment

@router.delete("/{payment_id}")
def cancel_payment(
    payment_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    payment = db.query(Payment).filter(
        Payment.id == payment_id,
        Payment.user_id == current_user.id
    ).first()
    if not payment:
        raise HTTPException(status_code=404, detail="Payment record not found.")

    payment.status = "CANCELLED"
    db.commit()
    return {"message": "Payment cancelled successfully."}
