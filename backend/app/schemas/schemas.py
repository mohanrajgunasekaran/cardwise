from pydantic import BaseModel, EmailStr, Field, ConfigDict
from typing import Optional, List
from datetime import date, datetime
from decimal import Decimal

# --- User & Auth Schemas ---
class UserRegister(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6)
    full_name: Optional[str] = None

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"

class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    email: str
    full_name: Optional[str] = None
    currency: str = "INR"
    is_active: bool
    created_at: datetime

# --- Card Schemas ---
class CardCreate(BaseModel):
    issuer: str
    variant: str
    nickname: Optional[str] = None
    masked_number: str
    network: str = "VISA"
    credit_limit: Optional[Decimal] = None
    available_limit: Optional[Decimal] = None
    billing_cycle_day: int = Field(ge=1, le=31)
    payment_due_days: int = Field(default=20, ge=10, le=35)
    annual_fee: Decimal = Decimal("0.00")
    joining_fee: Decimal = Decimal("0.00")
    reward_type: str = "CASHBACK"
    base_earn_rate: Decimal = Decimal("1.00")
    point_redemption_inr: Decimal = Decimal("0.2500")
    is_verified: bool = False

class CardUpdate(BaseModel):
    nickname: Optional[str] = None
    credit_limit: Optional[Decimal] = None
    available_limit: Optional[Decimal] = None
    billing_cycle_day: Optional[int] = Field(None, ge=1, le=31)
    payment_due_days: Optional[int] = Field(None, ge=10, le=35)
    is_verified: Optional[bool] = None
    is_archived: Optional[bool] = None

class CardResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    user_id: str
    issuer: str
    variant: str
    nickname: Optional[str] = None
    masked_number: str
    network: str
    credit_limit: Optional[Decimal] = None
    available_limit: Optional[Decimal] = None
    billing_cycle_day: int
    payment_due_days: int
    annual_fee: Decimal
    joining_fee: Decimal
    reward_type: str
    base_earn_rate: Decimal
    point_redemption_inr: Decimal
    is_verified: bool
    is_archived: bool
    created_at: datetime

# --- Statement Schemas ---
class StatementCreate(BaseModel):
    card_id: str
    statement_date: date
    payment_due_date: date
    period_start: date
    period_end: date
    total_balance: Decimal = Field(ge=0)
    minimum_due: Decimal = Field(ge=0)
    source: str = "MANUAL"
    document_ref: Optional[str] = None

class StatementUpdate(BaseModel):
    total_balance: Optional[Decimal] = None
    minimum_due: Optional[Decimal] = None
    is_paid: Optional[bool] = None

class StatementResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    card_id: str
    user_id: str
    statement_date: date
    payment_due_date: date
    period_start: date
    period_end: date
    total_balance: Decimal
    minimum_due: Decimal
    is_paid: bool
    source: str
    document_ref: Optional[str] = None
    created_at: datetime
    # Computed fields
    confirmed_paid_amount: Decimal = Decimal("0.00")
    planned_paid_amount: Decimal = Decimal("0.00")
    remaining_to_plan: Decimal = Decimal("0.00")

# --- Payment Schemas ---
class PaymentCreate(BaseModel):
    statement_id: str
    amount: Decimal = Field(gt=0)
    planned_date: date
    notes: Optional[str] = None

class PaymentConfirm(BaseModel):
    notes: Optional[str] = None

class PaymentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    statement_id: str
    user_id: str
    amount: Decimal
    planned_date: date
    status: str
    confirmed_at: Optional[datetime] = None
    notes: Optional[str] = None
    created_at: datetime

# --- Matcher Schemas ---
class MatcherRequest(BaseModel):
    purchase_amount: Decimal = Field(gt=0)
    category: str
    merchant: Optional[str] = None
    transaction_date: Optional[date] = None

class MatcherRecommendation(BaseModel):
    card_id: str
    card_name: str
    issuer: str
    variant: str
    masked_number: str
    estimated_net_benefit_inr: Decimal
    effective_rate_percent: Decimal
    calculation_breakdown: str
    applied_rule: str
    eligibility_conditions: str
    offer_expiry: Optional[date] = None
    confidence: str

class MatcherResponse(BaseModel):
    purchase_amount: Decimal
    category: str
    merchant: Optional[str] = None
    best_card_id: Optional[str] = None
    recommendations: List[MatcherRecommendation]

# --- Home Dashboard Summary ---
class HomeDashboardSummary(BaseModel):
    total_statement_balances: Decimal
    total_minimum_due: Decimal
    upcoming_deadlines_count: int
    overdue_count: int
    verified_cards_count: int
    total_cards_count: int
    planned_payment_total: Decimal
    confirmed_payment_total: Decimal
    remaining_unplanned_total: Decimal
    warning_minimum_due_message: str = "Paying only the minimum due generally does not prevent interest on the unpaid statement balance."
