from decimal import Decimal, ROUND_HALF_UP
from typing import List, Dict, Any, Optional

MINIMUM_DUE_WARNING = (
    "Paying only the minimum due generally does not prevent interest on the unpaid statement balance. "
    "Interest is charged from the date of transaction on revolving balances."
)

class PaymentReconciliationResult:
    def __init__(
        self,
        statement_balance: Optional[Decimal],
        minimum_due: Optional[Decimal],
        confirmed_payments_total: Decimal,
        planned_payments_total: Decimal,
        remaining_to_plan: Decimal,
        is_fully_planned: bool,
        is_fully_confirmed: bool,
        has_overpayment: bool,
        is_credit_balance: bool = False,
        warning_message: str = MINIMUM_DUE_WARNING
    ):
        self.statement_balance = statement_balance.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP) if statement_balance is not None else None
        self.minimum_due = minimum_due.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP) if minimum_due is not None else None
        self.confirmed_payments_total = confirmed_payments_total.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        self.planned_payments_total = planned_payments_total.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        self.remaining_to_plan = remaining_to_plan.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        self.is_fully_planned = is_fully_planned
        self.is_fully_confirmed = is_fully_confirmed
        self.has_overpayment = has_overpayment
        self.is_credit_balance = is_credit_balance
        self.warning_message = warning_message

    def to_dict(self) -> Dict[str, Any]:
        return {
            "statement_balance": self.statement_balance,
            "minimum_due": self.minimum_due,
            "confirmed_payments_total": self.confirmed_payments_total,
            "planned_payments_total": self.planned_payments_total,
            "remaining_to_plan": self.remaining_to_plan,
            "is_fully_planned": self.is_fully_planned,
            "is_fully_confirmed": self.is_fully_confirmed,
            "has_overpayment": self.has_overpayment,
            "is_credit_balance": self.is_credit_balance,
            "warning_message": self.warning_message
        }

def calculate_payment_reconciliation(
    statement_balance: Optional[Decimal],
    minimum_due: Optional[Decimal],
    payments: List[Any],
    allow_overpayment: bool = False
) -> PaymentReconciliationResult:
    """
    Computes remaining unplanned amount and status breakdown for a credit card statement.
    Uses strict decimal arithmetic without floating-point conversion.
    
    Formula:
    Remaining amount to plan = statement balance - confirmed payments - planned payments.
    Handles credit balances (e.g. -₹1,035) where no payment is required.
    """
    if statement_balance is not None and not isinstance(statement_balance, Decimal):
        statement_balance = Decimal(str(statement_balance))
    if minimum_due is not None and not isinstance(minimum_due, Decimal):
        minimum_due = Decimal(str(minimum_due))

    confirmed_total = Decimal("0.00")
    planned_total = Decimal("0.00")

    for p in payments:
        amount = p.amount if hasattr(p, "amount") else p.get("amount", Decimal("0.00"))
        if not isinstance(amount, Decimal):
            amount = Decimal(str(amount))
            
        status = p.status if hasattr(p, "status") else p.get("status", "PLANNED")
        status = status.upper()

        if status == "CONFIRMED":
            confirmed_total += amount
        elif status in ("PLANNED", "SUBMITTED"):
            planned_total += amount
        # CANCELLED or FAILED are excluded from reconciliation

    if statement_balance is None:
        return PaymentReconciliationResult(
            statement_balance=None,
            minimum_due=minimum_due,
            confirmed_payments_total=confirmed_total,
            planned_payments_total=planned_total,
            remaining_to_plan=Decimal("0.00"),
            is_fully_planned=False,
            is_fully_confirmed=False,
            has_overpayment=False,
            is_credit_balance=False
        )

    # Credit Balance check
    is_credit_balance = statement_balance < Decimal("0.00")
    if is_credit_balance or statement_balance == Decimal("0.00"):
        return PaymentReconciliationResult(
            statement_balance=statement_balance,
            minimum_due=minimum_due or Decimal("0.00"),
            confirmed_payments_total=confirmed_total,
            planned_payments_total=planned_total,
            remaining_to_plan=Decimal("0.00"),
            is_fully_planned=True,
            is_fully_confirmed=True,
            has_overpayment=is_credit_balance,
            is_credit_balance=is_credit_balance
        )

    raw_remaining = statement_balance - confirmed_total - planned_total
    has_overpayment = raw_remaining < Decimal("0.00")

    if has_overpayment and not allow_overpayment:
        remaining_to_plan = Decimal("0.00")
    else:
        remaining_to_plan = raw_remaining

    is_fully_confirmed = confirmed_total >= statement_balance
    is_fully_planned = (confirmed_total + planned_total) >= statement_balance

    return PaymentReconciliationResult(
        statement_balance=statement_balance,
        minimum_due=minimum_due or Decimal("0.00"),
        confirmed_payments_total=confirmed_total,
        planned_payments_total=planned_total,
        remaining_to_plan=remaining_to_plan,
        is_fully_planned=is_fully_planned,
        is_fully_confirmed=is_fully_confirmed,
        has_overpayment=has_overpayment,
        is_credit_balance=False
    )
