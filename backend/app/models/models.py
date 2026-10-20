from datetime import datetime, timezone
import uuid
from sqlalchemy import (
    Column, String, Boolean, Numeric, Integer, Date, DateTime, ForeignKey, Text
)
from sqlalchemy.orm import relationship
from app.db.session import Base

def generate_uuid() -> str:
    return str(uuid.uuid4())

class User(Base):
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(120), nullable=True)
    currency = Column(String(3), default="INR")
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    cards = relationship("CreditCard", back_populates="owner", cascade="all, delete-orphan")
    statements = relationship("Statement", back_populates="user", cascade="all, delete-orphan")
    payments = relationship("Payment", back_populates="user", cascade="all, delete-orphan")

class CreditCard(Base):
    __tablename__ = "credit_cards"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    issuer = Column(String(80), nullable=False, index=True)
    variant = Column(String(80), nullable=False)
    nickname = Column(String(80), nullable=True)
    masked_number = Column(String(40), nullable=False, default="Not available")
    network = Column(String(20), default="VISA")
    category = Column(String(80), nullable=True)
    credit_limit = Column(Numeric(12, 2), nullable=True)
    available_limit = Column(Numeric(12, 2), nullable=True)
    billing_cycle_day = Column(Integer, nullable=True)
    payment_due_days = Column(Integer, nullable=True)
    annual_fee = Column(Numeric(10, 2), default=0.00)
    joining_fee = Column(Numeric(10, 2), default=0.00)
    reward_type = Column(String(40), default="CASHBACK")
    base_earn_rate = Column(Numeric(6, 3), default=1.00)
    point_redemption_inr = Column(Numeric(6, 4), default=0.2500)
    is_verified = Column(Boolean, default=False)
    verification_status = Column(String(80), default="Imported — needs verification")
    notes = Column(String(255), nullable=True)
    is_archived = Column(Boolean, default=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    owner = relationship("User", back_populates="cards")
    statements = relationship("Statement", back_populates="card", cascade="all, delete-orphan")
    offers = relationship("CardOffer", back_populates="card", cascade="all, delete-orphan")
    product_terms = relationship("CardProductTerms", uselist=False, back_populates="card", cascade="all, delete-orphan")
    benefits = relationship("CardBenefitRecord", back_populates="card", cascade="all, delete-orphan")
    fees = relationship("CardFeeRecord", back_populates="card", cascade="all, delete-orphan")

class Statement(Base):
    __tablename__ = "statements"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    card_id = Column(String(36), ForeignKey("credit_cards.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    statement_date = Column(Date, nullable=True)
    payment_due_date = Column(Date, nullable=True)
    period_start = Column(Date, nullable=True)
    period_end = Column(Date, nullable=True)
    total_balance = Column(Numeric(12, 2), nullable=True)
    minimum_due = Column(Numeric(12, 2), nullable=True)
    is_paid = Column(Boolean, default=False)
    is_credit_balance = Column(Boolean, default=False)
    is_historical = Column(Boolean, default=False)
    source = Column(String(40), default="MANUAL")
    document_ref = Column(String(255), nullable=True)
    notes = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    card = relationship("CreditCard", back_populates="statements")
    user = relationship("User", back_populates="statements")
    payments = relationship("Payment", back_populates="statement", cascade="all, delete-orphan")

class Payment(Base):
    __tablename__ = "payments"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    statement_id = Column(String(36), ForeignKey("statements.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    amount = Column(Numeric(12, 2), nullable=False)
    planned_date = Column(Date, nullable=False)
    status = Column(String(20), default="PLANNED")  # PLANNED, SUBMITTED, CONFIRMED, CANCELLED
    confirmed_at = Column(DateTime, nullable=True)
    notes = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    statement = relationship("Statement", back_populates="payments")
    user = relationship("User", back_populates="payments")

class CardOffer(Base):
    __tablename__ = "card_offers"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    card_id = Column(String(36), ForeignKey("credit_cards.id", ondelete="CASCADE"), nullable=True, index=True)
    issuer = Column(String(80), nullable=False, index=True)
    variant = Column(String(80), nullable=True)
    title = Column(String(160), nullable=False)
    category = Column(String(40), nullable=False, index=True)  # SHOPPING, TRAVEL, FLIGHTS, HOTELS, UTILITIES, GROCERIES, FUEL, INSURANCE, DINING, OTHER
    merchant_keyword = Column(String(100), nullable=True)
    benefit_type = Column(String(30), nullable=False)  # CASHBACK_PERCENT, MULTIPLIER, FLAT_DISCOUNT
    benefit_value = Column(Numeric(6, 2), nullable=False)
    min_spend = Column(Numeric(10, 2), default=0.00)
    max_benefit_cap = Column(Numeric(10, 2), nullable=True)
    exclusion_details = Column(String(255), nullable=True)
    valid_from = Column(Date, nullable=False)
    valid_to = Column(Date, nullable=False)
    confidence = Column(String(20), default="VERIFIED")  # VERIFIED, ESTIMATED, COMMUNITY
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    card = relationship("CreditCard", back_populates="offers")

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    action = Column(String(60), nullable=False)
    entity_type = Column(String(40), nullable=False)
    entity_id = Column(String(36), nullable=True)
    details = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

class SourceDocument(Base):
    __tablename__ = "source_documents"

    id = Column(String(50), primary_key=True)  # e.g. doc-idfc-mitc-lic
    document_title = Column(String(255), nullable=False)
    file_name = Column(String(255), nullable=False)
    official_url = Column(String(500), nullable=True)
    issuer = Column(String(80), nullable=False)
    covered_card_variants = Column(Text, nullable=True)
    document_type = Column(String(80), nullable=False)
    version_or_date = Column(String(100), nullable=True)
    effective_date = Column(String(100), nullable=True)
    retrieval_date = Column(String(50), nullable=True)
    verification_status = Column(String(100), nullable=False, default="Verified against current official document")
    is_current = Column(Boolean, default=True)
    superseded_by_id = Column(String(50), ForeignKey("source_documents.id", ondelete="SET NULL"), nullable=True)
    relevant_pages_or_sections = Column(Text, nullable=True)
    summary = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    product_terms = relationship("CardProductTerms", back_populates="source_document")
    benefits = relationship("CardBenefitRecord", back_populates="source_document", cascade="all, delete-orphan")
    fees = relationship("CardFeeRecord", back_populates="source_document", cascade="all, delete-orphan")

class CardProductTerms(Base):
    __tablename__ = "card_product_terms"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    card_id = Column(String(36), ForeignKey("credit_cards.id", ondelete="CASCADE"), unique=True, nullable=False, index=True)
    source_document_id = Column(String(50), ForeignKey("source_documents.id", ondelete="SET NULL"), nullable=True, index=True)

    # Card identity
    issuer = Column(String(80), nullable=False)
    card_name = Column(String(120), nullable=False)
    exact_variant = Column(String(120), nullable=True)
    masked_card_number = Column(String(30), nullable=True)
    network = Column(String(40), nullable=True)
    variant_verification_status = Column(String(120), nullable=False, default="Unverified")

    # Fees and charges
    joining_fee = Column(Numeric(10, 2), nullable=True)
    annual_fee = Column(Numeric(10, 2), nullable=True)
    renewal_fee = Column(Numeric(10, 2), nullable=True)
    annual_fee_waiver_threshold = Column(Numeric(12, 2), nullable=True)
    waiver_period_and_conditions = Column(Text, nullable=True)
    interest_rate_monthly = Column(Numeric(5, 2), nullable=True)
    interest_rate_annual = Column(Numeric(5, 2), nullable=True)
    late_payment_fee_structure = Column(Text, nullable=True)
    cash_advance_fee = Column(String(120), nullable=True)
    cash_advance_interest_terms = Column(Text, nullable=True)
    forex_markup = Column(Numeric(5, 2), nullable=True)
    over_limit_fee = Column(String(120), nullable=True)
    emi_processing_fee = Column(String(120), nullable=True)
    emi_foreclosure_terms = Column(Text, nullable=True)
    fuel_surcharge_terms = Column(Text, nullable=True)
    other_charges = Column(Text, nullable=True)
    applicable_gst_notes = Column(String(255), nullable=True)

    # Rewards and benefits
    reward_type = Column(String(50), nullable=True)  # CASHBACK, REWARD_POINTS, CUSTOMIZABLE, NONE
    reward_rate = Column(Text, nullable=True)
    eligible_spend_categories = Column(Text, nullable=True)
    excluded_spend_categories = Column(Text, nullable=True)
    reward_point_value = Column(Numeric(6, 4), nullable=True)
    cashback_cap = Column(String(120), nullable=True)
    reward_expiry = Column(String(120), nullable=True)
    redemption_method = Column(Text, nullable=True)
    milestone_benefits = Column(Text, nullable=True)
    welcome_benefits = Column(Text, nullable=True)
    airport_lounge_access = Column(Text, nullable=True)
    railway_lounge_access = Column(Text, nullable=True)
    lounge_eligibility_conditions = Column(Text, nullable=True)
    travel_benefits = Column(Text, nullable=True)
    dining_and_entertainment_benefits = Column(Text, nullable=True)
    insurance_and_purchase_protection = Column(Text, nullable=True)
    benefit_validity = Column(String(120), nullable=True)
    benefit_terms = Column(Text, nullable=True)

    # Verification and provenance
    source_url = Column(String(500), nullable=True)
    source_title = Column(String(200), nullable=True)
    source_type = Column(String(80), nullable=True)
    date_verified = Column(Date, nullable=True)
    effective_date = Column(String(100), nullable=True)
    verification_status = Column(String(100), nullable=False, default="Unverified")
    confidence_notes = Column(Text, nullable=True)
    unresolved_questions = Column(Text, nullable=True)
    document_citation = Column(Text, nullable=True)
    last_checked_date = Column(Date, nullable=True)
    superseded_status = Column(String(50), nullable=True)

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    card = relationship("CreditCard", back_populates="product_terms")
    source_document = relationship("SourceDocument", back_populates="product_terms")

class CardBenefitRecord(Base):
    __tablename__ = "card_benefits"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    card_id = Column(String(36), ForeignKey("credit_cards.id", ondelete="CASCADE"), nullable=False, index=True)
    source_document_id = Column(String(50), ForeignKey("source_documents.id", ondelete="SET NULL"), nullable=True, index=True)
    benefit_category = Column(String(80), nullable=False)  # REWARDS, TRAVEL, LOUNGE, INSURANCE, MOVIE, FUEL, DINING, ROAD_SIDE_ASSISTANCE
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=False)
    reward_rate_or_cashback = Column(String(120), nullable=True)
    cap = Column(String(120), nullable=True)
    eligibility_requirements = Column(Text, nullable=True)
    exclusions = Column(Text, nullable=True)
    redemption_value = Column(String(100), nullable=True)
    validity_dates = Column(String(100), nullable=True)
    status_label = Column(String(100), default="Verified against current official document")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    card = relationship("CreditCard", back_populates="benefits")
    source_document = relationship("SourceDocument", back_populates="benefits")

class CardFeeRecord(Base):
    __tablename__ = "card_fees"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    card_id = Column(String(36), ForeignKey("credit_cards.id", ondelete="CASCADE"), nullable=False, index=True)
    source_document_id = Column(String(50), ForeignKey("source_documents.id", ondelete="SET NULL"), nullable=True, index=True)
    charge_category = Column(String(80), nullable=False)  # JOINING, ANNUAL, FINANCE_CHARGE, LATE_PAYMENT, CASH_ADVANCE, FOREX, OVERLIMIT, RENT, FUEL, EMI
    charge_name = Column(String(200), nullable=False)
    amount_or_percentage = Column(String(120), nullable=False)
    min_amount = Column(Numeric(10, 2), nullable=True)
    max_amount = Column(Numeric(10, 2), nullable=True)
    calculation_basis = Column(Text, nullable=True)
    conditions = Column(Text, nullable=True)
    gst_treatment = Column(String(120), default="18% GST applicable")
    effective_start_date = Column(String(80), nullable=True)
    effective_end_date = Column(String(80), nullable=True)
    status_label = Column(String(100), default="Verified against current official document")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    card = relationship("CreditCard", back_populates="fees")
    source_document = relationship("SourceDocument", back_populates="fees")
