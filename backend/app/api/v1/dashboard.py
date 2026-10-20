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

    # Separate payable debts from credit balances (e.g. -₹1,035 credit balance must NEVER be treated as payable debt)
    total_payable_statement_balances = Decimal("0.00")
    total_credit_balances = Decimal("0.00")
    total_minimum_due = Decimal("0.00")
    upcoming_deadlines = 0
    overdue_count = 0

    for s in statements:
        if s.total_balance is not None:
            bal = Decimal(str(s.total_balance))
            if bal > Decimal("0.00"):
                total_payable_statement_balances += bal
                if s.payment_due_date:
                    if s.payment_due_date >= today:
                        upcoming_deadlines += 1
                    else:
                        overdue_count += 1
            elif bal < Decimal("0.00"):
                total_credit_balances += abs(bal)

        if s.minimum_due is not None:
            min_d = Decimal(str(s.minimum_due))
            if min_d > Decimal("0.00"):
                total_minimum_due += min_d

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

    remaining_unplanned = total_payable_statement_balances - confirmed_payment_total - planned_payment_total
    if remaining_unplanned < Decimal("0.00"):
        remaining_unplanned = Decimal("0.00")

    return HomeDashboardSummary(
        total_statement_balances=total_payable_statement_balances,
        total_credit_balances=total_credit_balances,
        total_minimum_due=total_minimum_due,
        upcoming_deadlines_count=upcoming_deadlines,
        overdue_count=overdue_count,
        verified_cards_count=verified_cards,
        total_cards_count=total_cards,
        planned_payment_total=planned_payment_total,
        confirmed_payment_total=confirmed_payment_total,
        remaining_unplanned_total=remaining_unplanned
    )
