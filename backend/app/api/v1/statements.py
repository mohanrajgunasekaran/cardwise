from typing import List, Optional
from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.models import User, Statement, CreditCard, Payment
from app.schemas.schemas import StatementCreate, StatementUpdate, StatementResponse
from app.api.deps import get_current_user
from app.services.payment_calculator import calculate_payment_reconciliation

router = APIRouter()

def enrich_statement_response(statement: Statement, db: Session) -> StatementResponse:
    payments = db.query(Payment).filter(Payment.statement_id == statement.id).all()
    bal = Decimal(str(statement.total_balance)) if statement.total_balance is not None else None
    min_d = Decimal(str(statement.minimum_due)) if statement.minimum_due is not None else None
    recon = calculate_payment_reconciliation(
        statement_balance=bal,
        minimum_due=min_d,
        payments=payments
    )
    res = StatementResponse.model_validate(statement)
    if statement.card:
        res.card_name = statement.card.nickname or statement.card.variant
        res.card_issuer = statement.card.issuer
        res.masked_number = statement.card.masked_number
    res.confirmed_paid_amount = recon.confirmed_payments_total
    res.planned_paid_amount = recon.planned_payments_total
    res.remaining_to_plan = recon.remaining_to_plan
    return res

@router.get("", response_model=List[StatementResponse])
def list_statements(
    card_id: Optional[str] = Query(None),
    is_paid: Optional[bool] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    query = db.query(Statement).filter(Statement.user_id == current_user.id)
    if card_id:
        query = query.filter(Statement.card_id == card_id)
    if is_paid is not None:
        query = query.filter(Statement.is_paid == is_paid)
    
    statements = query.order_by(Statement.payment_due_date.asc().nulls_last()).all()
    return [enrich_statement_response(s, db) for s in statements]

@router.post("", response_model=StatementResponse, status_code=status.HTTP_201_CREATED)
def create_statement(
    payload: StatementCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Verify card ownership
    card = db.query(CreditCard).filter(
        CreditCard.id == payload.card_id,
        CreditCard.user_id == current_user.id
    ).first()
    if not card:
        raise HTTPException(status_code=404, detail="Associated credit card not found.")

    # Duplicate detection: statement with same card and statement_date (if provided)
    if payload.statement_date:
        duplicate = db.query(Statement).filter(
            Statement.card_id == payload.card_id,
            Statement.statement_date == payload.statement_date
        ).first()
        if duplicate:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="A statement for this card and date already exists."
            )

    is_credit = False
    if payload.total_balance is not None and payload.total_balance < 0:
        is_credit = True

    statement = Statement(
        card_id=payload.card_id,
        user_id=current_user.id,
        statement_date=payload.statement_date,
        payment_due_date=payload.payment_due_date,
        period_start=payload.period_start,
        period_end=payload.period_end,
        total_balance=payload.total_balance,
        minimum_due=payload.minimum_due,
        is_credit_balance=is_credit or payload.is_credit_balance,
        is_historical=payload.is_historical,
        source=payload.source,
        document_ref=payload.document_ref,
        notes=payload.notes
    )
    db.add(statement)
    db.commit()
    db.refresh(statement)
    return enrich_statement_response(statement, db)

@router.get("/{statement_id}", response_model=StatementResponse)
def get_statement(
    statement_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    statement = db.query(Statement).filter(
        Statement.id == statement_id,
        Statement.user_id == current_user.id
    ).first()
    if not statement:
        raise HTTPException(status_code=404, detail="Statement not found.")
    return enrich_statement_response(statement, db)

@router.put("/{statement_id}", response_model=StatementResponse)
def update_statement(
    statement_id: str,
    payload: StatementUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    statement = db.query(Statement).filter(
        Statement.id == statement_id,
        Statement.user_id == current_user.id
    ).first()
    if not statement:
        raise HTTPException(status_code=404, detail="Statement not found.")

    update_data = payload.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(statement, field, value)

    db.commit()
    db.refresh(statement)
    return enrich_statement_response(statement, db)
