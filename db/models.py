# ==============================================================================
# CypherLabelGuard CORE EDITION v2.0
# Relational Database Models (Users, Cards, Subscriptions, Invoices, Job History)
# ==============================================================================

import time
import uuid
from sqlalchemy import (
    Column,
    String,
    Integer,
    Float,
    Boolean,
    Text,
    DateTime,
    ForeignKey,
)
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from db.database import Base


def generate_uuid():
    return str(uuid.uuid4())


class User(Base):
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(100), nullable=False, default="Enterprise User")
    role = Column(String(50), nullable=False, default="User")
    workspace_name = Column(String(100), nullable=False, default="Enterprise Workspace")
    credits_balance = Column(Integer, default=5000)  # Default 5,000 token credits (~$50.00)
    stripe_customer_id = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    payment_methods = relationship("PaymentMethod", back_populates="user", cascade="all, delete-orphan")
    subscriptions = relationship("Subscription", back_populates="user", cascade="all, delete-orphan")
    transactions = relationship("Transaction", back_populates="user", cascade="all, delete-orphan")
    jobs = relationship("JobRecord", back_populates="user", cascade="all, delete-orphan")
    audit_logs = relationship("AuditLogEntry", back_populates="user", cascade="all, delete-orphan")

    def to_dict(self):
        return {
            "id": self.id,
            "email": self.email,
            "full_name": self.full_name,
            "role": self.role,
            "workspace_name": self.workspace_name,
            "credits_balance": self.credits_balance,
            "stripe_customer_id": self.stripe_customer_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class PaymentMethod(Base):
    """Credit Card details (PCI-DSS compliant: stores tokenized brand, last4, exp)."""
    __tablename__ = "payment_methods"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    stripe_payment_method_id = Column(String(100), nullable=True)
    card_brand = Column(String(50), nullable=False, default="visa")  # visa, mastercard, amex
    last4 = Column(String(4), nullable=False)
    exp_month = Column(Integer, nullable=False)
    exp_year = Column(Integer, nullable=False)
    cardholder_name = Column(String(100), nullable=False, default="Authorized Cardholder")
    is_default = Column(Boolean, default=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    user = relationship("User", back_populates="payment_methods")

    def to_dict(self):
        return {
            "id": self.id,
            "card_brand": self.card_brand,
            "brand": self.card_brand,
            "last4": self.last4,
            "exp_month": self.exp_month,
            "exp_year": self.exp_year,
            "cardholder_name": self.cardholder_name,
            "is_default": self.is_default,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class Subscription(Base):
    """Active SaaS Plan subscription details."""
    __tablename__ = "subscriptions"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    plan_name = Column(String(50), nullable=False, default="Core")  # Free, Core, Pro, Enterprise
    monthly_price = Column(Float, nullable=False, default=129.00)
    status = Column(String(50), nullable=False, default="Active")  # Active, Past Due, Canceled
    stripe_subscription_id = Column(String(100), nullable=True)
    current_period_start = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    current_period_end = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    cancel_at_period_end = Column(Boolean, default=False)

    user = relationship("User", back_populates="subscriptions")

    def to_dict(self):
        return {
            "id": self.id,
            "plan_name": self.plan_name,
            "monthly_price": self.monthly_price,
            "status": self.status,
            "current_period_end": self.current_period_end.isoformat() if self.current_period_end else None,
            "cancel_at_period_end": self.cancel_at_period_end,
        }


class Transaction(Base):
    """Invoices and billing charge records."""
    __tablename__ = "transactions"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    invoice_number = Column(String(50), unique=True, nullable=False)
    description = Column(String(255), nullable=False)
    amount = Column(Float, nullable=False)
    currency = Column(String(10), default="USD")
    status = Column(String(50), default="Paid")  # Paid, Pending, Failed
    stripe_charge_id = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    user = relationship("User", back_populates="transactions")

    def to_dict(self):
        return {
            "id": self.id,
            "invoice_number": self.invoice_number,
            "description": self.description,
            "amount": self.amount,
            "currency": self.currency,
            "status": self.status,
            "created_at": self.created_at.strftime("%b %d, %Y") if self.created_at else "Today",
        }


class JobRecord(Base):
    """Persistent Job History metadata (preserves auditability without retaining raw RAM payloads)."""
    __tablename__ = "job_records"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    job_number = Column(String(20), unique=True, nullable=False, index=True)
    name = Column(String(200), nullable=False)
    modality = Column(String(50), nullable=False, default="Text")
    status = Column(String(50), nullable=False, default="Completed")
    progress = Column(Integer, default=100)
    labels_count = Column(Integer, default=1)
    cost = Column(String(20), default="$0.01")
    consensus_label = Column(String(100), default="CONFIRMED")
    affirmative_votes = Column(Integer, default=32)
    trace_id = Column(String(100), nullable=True)
    lineage_hash = Column(String(64), nullable=True)
    image_url = Column(Text, nullable=True)
    criteria_json = Column(Text, nullable=True)
    annotations_json = Column(Text, nullable=True)
    folder_name = Column(String(100), default="General Workspace", nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    user = relationship("User", back_populates="jobs")

    def to_dict(self):
        import json
        crit_res = []
        if self.criteria_json:
            try:
                crit_res = json.loads(self.criteria_json)
            except Exception:
                crit_res = []

        ann_res = []
        if self.annotations_json:
            try:
                ann_res = json.loads(self.annotations_json)
            except Exception:
                ann_res = []

        has_anom = any(bool(c.get("anomaly")) for c in crit_res) or (self.consensus_label and "REJECT" in self.consensus_label)
        confs = [float(c.get("confidence", 0)) for c in crit_res if not c.get("anomaly")]
        overall_conf = 0.0 if (has_anom or not confs) else round(sum(confs) / len(confs), 1)

        is_zero_criteria = (len(crit_res) == 0)
        eff_label = "UNVERIFIED (0 CRITERIA)" if (is_zero_criteria and (not self.consensus_label or self.consensus_label in ["Content Safety", "CONFIRMED", "COMPLETED"])) else self.consensus_label
        eff_votes = 0 if (is_zero_criteria or has_anom) else (self.affirmative_votes or 0)

        return {
            "id": self.job_number,
            "uuid": self.id,
            "job_number": self.job_number,
            "name": self.name,
            "type": self.modality,
            "status": self.status,
            "progress": self.progress,
            "labels": self.labels_count,
            "cost": self.cost,
            "consensus_label": eff_label,
            "affirmative_votes": eff_votes,
            "trace_id": self.trace_id,
            "imageUrl": self.image_url,
            "criteria_results": crit_res,
            "overall_criteria_confidence": overall_conf,
            "anomaly_detected": has_anom,
            "imageAnnotations": ann_res,
            "folder_name": getattr(self, "folder_name", None) or "General Workspace",
            "created": self.created_at.strftime("%b %d, %I:%M %p") if self.created_at else "Just now",
        }



class AuditLogEntry(Base):
    """Immutable User Activity Log."""
    __tablename__ = "audit_log_entries"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    action = Column(String(150), nullable=False)
    details = Column(Text, nullable=True)
    ip_address = Column(String(50), default="127.0.0.1")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    user = relationship("User", back_populates="audit_logs")

    def to_dict(self):
        return {
            "id": self.id,
            "action": self.action,
            "details": self.details,
            "ip_address": self.ip_address,
            "created_at": self.created_at.strftime("%b %d, %H:%M:%S") if self.created_at else "Just now",
        }


class FolderRecord(Base):
    """Persistent user-defined folders for organizing datasets and jobs."""
    __tablename__ = "folder_records"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    name = Column(String(100), unique=True, nullable=False, index=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

