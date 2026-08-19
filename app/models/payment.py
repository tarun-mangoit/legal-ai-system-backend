import enum
from sqlalchemy import Column, String, Float, ForeignKey, DateTime, Enum, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
from .base import BaseModel

class PaymentStatus(str, enum.Enum):
    PENDING = "PENDING"
    CREATED = "CREATED"
    PROCESSING = "PROCESSING"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"
    REFUNDED = "REFUNDED"
    PARTIALLY_REFUNDED = "PARTIALLY_REFUNDED"

class Payment(BaseModel):
    __tablename__ = "payments"

    case_id = Column(UUID(as_uuid=True), ForeignKey("cases.id"), nullable=False)
    client_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    amount = Column(Float, nullable=False)
    currency = Column(String(3), nullable=False, default="INR")
    status = Column(Enum(PaymentStatus, name="payment_status_enum", create_type=False), nullable=False, default=PaymentStatus.PENDING)
    
    payment_method = Column(String, nullable=True)
    gateway = Column(String, nullable=False, default="razorpay")
    
    gateway_order_id = Column(String, nullable=True, unique=True)
    gateway_payment_id = Column(String, nullable=True, unique=True)
    gateway_signature = Column(String, nullable=True)
    
    transaction_reference = Column(String, nullable=True, unique=True)
    remarks = Column(Text, nullable=True)

    # Relationships
    case = relationship("Case", back_populates="payments")
    client = relationship("User", foreign_keys=[client_id])
    transactions = relationship("PaymentTransaction", back_populates="payment", cascade="all, delete-orphan")
    invoice = relationship("Invoice", back_populates="payment", uselist=False, cascade="all, delete-orphan")
    refunds = relationship("Refund", back_populates="payment", cascade="all, delete-orphan")

class PaymentTransaction(BaseModel):
    __tablename__ = "payment_transactions"

    payment_id = Column(UUID(as_uuid=True), ForeignKey("payments.id"), nullable=False)
    status = Column(String, nullable=False)
    gateway_response = Column(Text, nullable=True)
    amount = Column(Float, nullable=False)
    
    # Relationships
    payment = relationship("Payment", back_populates="transactions")

class Invoice(BaseModel):
    __tablename__ = "invoices"

    payment_id = Column(UUID(as_uuid=True), ForeignKey("payments.id"), nullable=False, unique=True)
    invoice_number = Column(String, nullable=False, unique=True)
    invoice_date = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    subtotal = Column(Float, nullable=False)
    tax = Column(Float, nullable=False, default=0.0)
    discount = Column(Float, nullable=False, default=0.0)
    total = Column(Float, nullable=False)
    
    pdf_path = Column(String, nullable=True)
    status = Column(String, nullable=False, default="GENERATED")

    # Relationships
    payment = relationship("Payment", back_populates="invoice")

class Refund(BaseModel):
    __tablename__ = "refunds"

    payment_id = Column(UUID(as_uuid=True), ForeignKey("payments.id"), nullable=False)
    refund_amount = Column(Float, nullable=False)
    refund_reason = Column(Text, nullable=True)
    gateway_refund_id = Column(String, nullable=True, unique=True)
    status = Column(String, nullable=False, default="PENDING")

    # Relationships
    payment = relationship("Payment", back_populates="refunds")
