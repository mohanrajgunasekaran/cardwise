from pydantic import BaseModel, EmailStr, Field, ConfigDict
from typing import Optional, List
from datetime import date, datetime
from decimal import Decimal

# --- User & Auth Schemas ---
class UserRegister(BaseModel):
    email: str
    password: str = Field(min_length=6)
    full_name: Optional[str] = None

class UserLogin(BaseModel):
    email: str
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
    masked_number: str = "Not available"
    network: str = "VISA"
    category: Optional[str] = None
    credit_limit: Optional[Decimal] = None
    available_limit: Optional[Decimal] = None
    billing_cycle_day: Optional[int] = None
    payment_due_days: Optional[int] = None
    annual_fee: Decimal = Decimal("0.00")
    joining_fee: Decimal = Decimal("0.00")
    reward_type: str = "CASHBACK"
    base_earn_rate: Decimal = Decimal("1.00")
    point_redemption_inr: Decimal = Decimal("0.2500")
    is_verified: bool = False
    verification_status: str = "Imported — needs verification"
    notes: Optional[str] = None

class CardUpdate(BaseModel):
    nickname: Optional[str] = None
    category: Optional[str] = None
    credit_limit: Optional[Decimal] = None
    available_limit: Optional[Decimal] = None
    billing_cycle_day: Optional[int] = None
    payment_due_days: Optional[int] = None
    is_verified: Optional[bool] = None
    verification_status: Optional[str] = None
    notes: Optional[str] = None
    is_archived: Optional[bool] = None

class CardProductTermsBase(BaseModel):
    issuer: str
    card_name: str
    exact_variant: Optional[str] = None
    masked_card_number: Optional[str] = None
    network: Optional[str] = None
    variant_verification_status: str = "Unverified"
    joining_fee: Optional[Decimal] = None
    annual_fee: Optional[Decimal] = None
    renewal_fee: Optional[Decimal] = None
    annual_fee_waiver_threshold: Optional[Decimal] = None
    waiver_period_and_conditions: Optional[str] = None
    interest_rate_monthly: Optional[Decimal] = None
    interest_rate_annual: Optional[Decimal] = None
    late_payment_fee_structure: Optional[str] = None
    cash_advance_fee: Optional[str] = None
    cash_advance_interest_terms: Optional[str] = None
    forex_markup: Optional[Decimal] = None
    over_limit_fee: Optional[str] = None
    emi_processing_fee: Optional[str] = None
    emi_foreclosure_terms: Optional[str] = None
    fuel_surcharge_terms: Optional[str] = None
    other_charges: Optional[str] = None
    applicable_gst_notes: Optional[str] = None
    reward_type: Optional[str] = None
    reward_rate: Optional[str] = None
    eligible_spend_categories: Optional[str] = None
    excluded_spend_categories: Optional[str] = None
    reward_point_value: Optional[Decimal] = None
    cashback_cap: Optional[str] = None
    reward_expiry: Optional[str] = None
    redemption_method: Optional[str] = None
    milestone_benefits: Optional[str] = None
    welcome_benefits: Optional[str] = None
    airport_lounge_access: Optional[str] = None
    railway_lounge_access: Optional[str] = None
    lounge_eligibility_conditions: Optional[str] = None
    travel_benefits: Optional[str] = None
    dining_and_entertainment_benefits: Optional[str] = None
    insurance_and_purchase_protection: Optional[str] = None
    benefit_validity: Optional[str] = None
    benefit_terms: Optional[str] = None
    source_url: Optional[str] = None
    source_title: Optional[str] = None
    source_type: Optional[str] = None
    date_verified: Optional[date] = None
    effective_date: Optional[str] = None
    verification_status: str = "Unverified"
    confidence_notes: Optional[str] = None
    unresolved_questions: Optional[str] = None
    source_document_id: Optional[str] = None
    document_citation: Optional[str] = None
    last_checked_date: Optional[date] = None
    superseded_status: Optional[str] = None

class SourceDocumentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    document_title: str
    file_name: str
    official_url: Optional[str] = None
    issuer: str
    covered_card_variants: Optional[str] = None
    document_type: str
    version_or_date: Optional[str] = None
    effective_date: Optional[str] = None
    retrieval_date: Optional[str] = None
    verification_status: str
    is_current: bool = True
    superseded_by_id: Optional[str] = None
    relevant_pages_or_sections: Optional[str] = None
    summary: Optional[str] = None
    created_at: datetime

class CardBenefitRecordResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    card_id: str
    source_document_id: Optional[str] = None
    benefit_category: str
    title: str
    description: str
    reward_rate_or_cashback: Optional[str] = None
    cap: Optional[str] = None
    eligibility_requirements: Optional[str] = None
    exclusions: Optional[str] = None
    redemption_value: Optional[str] = None
    validity_dates: Optional[str] = None
    status_label: str
    created_at: datetime

class CardFeeRecordResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    card_id: str
    source_document_id: Optional[str] = None
    charge_category: str
    charge_name: str
    amount_or_percentage: str
    min_amount: Optional[Decimal] = None
    max_amount: Optional[Decimal] = None
    calculation_basis: Optional[str] = None
    conditions: Optional[str] = None
    gst_treatment: str = "18% GST applicable"
    effective_start_date: Optional[str] = None
    effective_end_date: Optional[str] = None
    status_label: str
    created_at: datetime

class CardProductTermsCreate(CardProductTermsBase):
    card_id: str

class CardProductTermsUpdate(BaseModel):
    exact_variant: Optional[str] = None
    variant_verification_status: Optional[str] = None
    joining_fee: Optional[Decimal] = None
    annual_fee: Optional[Decimal] = None
    renewal_fee: Optional[Decimal] = None
    annual_fee_waiver_threshold: Optional[Decimal] = None
    waiver_period_and_conditions: Optional[str] = None
    interest_rate_monthly: Optional[Decimal] = None
    interest_rate_annual: Optional[Decimal] = None
    late_payment_fee_structure: Optional[str] = None
    cash_advance_fee: Optional[str] = None
    cash_advance_interest_terms: Optional[str] = None
    forex_markup: Optional[Decimal] = None
    over_limit_fee: Optional[str] = None
    emi_processing_fee: Optional[str] = None
    emi_foreclosure_terms: Optional[str] = None
    fuel_surcharge_terms: Optional[str] = None
    other_charges: Optional[str] = None
    applicable_gst_notes: Optional[str] = None
    reward_type: Optional[str] = None
    reward_rate: Optional[str] = None
    eligible_spend_categories: Optional[str] = None
    excluded_spend_categories: Optional[str] = None
    reward_point_value: Optional[Decimal] = None
    cashback_cap: Optional[str] = None
    reward_expiry: Optional[str] = None
    redemption_method: Optional[str] = None
    milestone_benefits: Optional[str] = None
    welcome_benefits: Optional[str] = None
    airport_lounge_access: Optional[str] = None
    railway_lounge_access: Optional[str] = None
    lounge_eligibility_conditions: Optional[str] = None
    travel_benefits: Optional[str] = None
    dining_and_entertainment_benefits: Optional[str] = None
    insurance_and_purchase_protection: Optional[str] = None
    benefit_validity: Optional[str] = None
    benefit_terms: Optional[str] = None
    source_url: Optional[str] = None
    source_title: Optional[str] = None
    source_type: Optional[str] = None
    date_verified: Optional[date] = None
    effective_date: Optional[str] = None
    verification_status: Optional[str] = None
    confidence_notes: Optional[str] = None
    unresolved_questions: Optional[str] = None
    source_document_id: Optional[str] = None
    document_citation: Optional[str] = None
    last_checked_date: Optional[date] = None
    superseded_status: Optional[str] = None

class CardProductTermsResponse(CardProductTermsBase):
    model_config = ConfigDict(from_attributes=True)
    id: str
    card_id: str
    created_at: datetime
    updated_at: datetime
    source_document: Optional[SourceDocumentResponse] = None

class CardResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    user_id: str
    issuer: str
    variant: str
    nickname: Optional[str] = None
    masked_number: str
    network: str
    category: Optional[str] = None
    credit_limit: Optional[Decimal] = None
    available_limit: Optional[Decimal] = None
    billing_cycle_day: Optional[int] = None
    payment_due_days: Optional[int] = None
    annual_fee: Decimal
    joining_fee: Decimal
    reward_type: str
    base_earn_rate: Decimal
    point_redemption_inr: Decimal
    is_verified: bool
    verification_status: str = "Imported — needs verification"
    notes: Optional[str] = None
    is_archived: bool
    created_at: datetime
    product_terms: Optional[CardProductTermsResponse] = None
    benefits: List[CardBenefitRecordResponse] = []
    fees: List[CardFeeRecordResponse] = []

# --- Statement Schemas ---
class StatementCreate(BaseModel):
    card_id: str
    statement_date: Optional[date] = None
    payment_due_date: Optional[date] = None
    period_start: Optional[date] = None
    period_end: Optional[date] = None
    total_balance: Optional[Decimal] = None
    minimum_due: Optional[Decimal] = None
    is_credit_balance: bool = False
    is_historical: bool = False
    source: str = "MANUAL"
    document_ref: Optional[str] = None
    notes: Optional[str] = None

class StatementUpdate(BaseModel):
    total_balance: Optional[Decimal] = None
    minimum_due: Optional[Decimal] = None
    payment_due_date: Optional[date] = None
    is_paid: Optional[bool] = None
    notes: Optional[str] = None

class StatementResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    card_id: str
    user_id: str
    statement_date: Optional[date] = None
    payment_due_date: Optional[date] = None
    period_start: Optional[date] = None
    period_end: Optional[date] = None
    total_balance: Optional[Decimal] = None
    minimum_due: Optional[Decimal] = None
    is_paid: bool
    is_credit_balance: bool = False
    is_historical: bool = False
    source: str
    document_ref: Optional[str] = None
    notes: Optional[str] = None
    created_at: datetime
    # Computed fields
    card_name: Optional[str] = None
    card_issuer: Optional[str] = None
    masked_number: Optional[str] = None
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
    total_credit_balances: Decimal = Decimal("0.00")
    total_minimum_due: Decimal
    upcoming_deadlines_count: int
    overdue_count: int
    verified_cards_count: int
    total_cards_count: int
    planned_payment_total: Decimal
    confirmed_payment_total: Decimal
    remaining_unplanned_total: Decimal
    warning_minimum_due_message: str = "Paying only the minimum due generally does not prevent interest on the unpaid statement balance."
