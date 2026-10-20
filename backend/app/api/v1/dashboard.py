from decimal import Decimal
from datetime import date
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.models import User, CreditCard, Statement, Payment
from app.schemas.schemas import HomeDashboardSummary
from app.api.deps import get_current_user

router = APIRouter()

@router.get("/summary", response_model=HomeDashboardSummary)
def get_dashboard_summary(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    today = date.today()

    cards = db.query(CreditCard).filter(
        CreditCard.user_id == current_user.id,
        CreditCard.is_archived == False
    ).all()
    total_cards = len(cards)
    verified_cards = sum(1 for c in cards if c.is_verified)

    # Active statements that are unpaid
    statements = db.query(Statement).filter(
        Statement.user_id == current_user.id,
        Statement.is_paid == False
    ).all()

    total_statement_balances = sum((Decimal(str(s.total_balance)) for s in statements), Decimal("0.00"))
    total_minimum_due = sum((Decimal(str(s.minimum_due)) for s in statements), Decimal("0.00"))
    
    upcoming_deadlines = sum(1 for s in statements if s.payment_due_date >= today)
    overdue_count = sum(1 for s in statements if s.payment_due_date < today)

    # Payments reconciliation
    payments = db.query(Payment).filter(Payment.user_id == current_user.id).all()
    planned_payment_total = Decimal("0.00")
    confirmed_payment_total = Decimal("0.00")

    for p in payments:
        amt = Decimal(str(p.amount))
        if p.status == "CONFIRMED":
            confirmed_payment_total += amt
        elif p.status in ("PLANNED", "SUBMITTED"):
            planned_payment_total += amt

    remaining_unplanned = total_statement_balances - confirmed_payment_total - planned_payment_total
    if remaining_unplanned < Decimal("0.00"):
        remaining_unplanned = Decimal("0.00")

    return HomeDashboardSummary(
        total_statement_balances=total_statement_balances,
        total_minimum_due=total_minimum_due,
        upcoming_deadlines_count=upcoming_deadlines,
        overdue_count=overdue_count,
        verified_cards_count=verified_cards,
        total_cards_count=total_cards,
        planned_payment_total=planned_payment_total,
        confirmed_payment_total=confirmed_payment_total,
        remaining_unplanned_total=remaining_unplanned
    )
