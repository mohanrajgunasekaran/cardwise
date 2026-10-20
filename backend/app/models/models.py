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
    masked_number = Column(String(24), nullable=False)
    network = Column(String(20), default="VISA")  # VISA, MASTERCARD, RUPAY, AMEX
    credit_limit = Column(Numeric(12, 2), nullable=True)
    available_limit = Column(Numeric(12, 2), nullable=True)
    billing_cycle_day = Column(Integer, nullable=False, default=1)
    payment_due_days = Column(Integer, nullable=False, default=20)
    annual_fee = Column(Numeric(10, 2), default=0.00)
    joining_fee = Column(Numeric(10, 2), default=0.00)
    reward_type = Column(String(40), default="CASHBACK")  # CASHBACK, REWARD_POINTS, MILES
    base_earn_rate = Column(Numeric(6, 3), default=1.00)
    point_redemption_inr = Column(Numeric(6, 4), default=0.2500)
    is_verified = Column(Boolean, default=False)
    is_archived = Column(Boolean, default=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    owner = relationship("User", back_populates="cards")
    statements = relationship("Statement", back_populates="card", cascade="all, delete-orphan")
    offers = relationship("CardOffer", back_populates="card", cascade="all, delete-orphan")

class Statement(Base):
    __tablename__ = "statements"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    card_id = Column(String(36), ForeignKey("credit_cards.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    statement_date = Column(Date, nullable=False)
    payment_due_date = Column(Date, nullable=False)
    period_start = Column(Date, nullable=False)
    period_end = Column(Date, nullable=False)
    total_balance = Column(Numeric(12, 2), nullable=False)
    minimum_due = Column(Numeric(12, 2), nullable=False)
    is_paid = Column(Boolean, default=False)
    source = Column(String(40), default="MANUAL")
    document_ref = Column(String(255), nullable=True)
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
