from datetime import datetime,timezone
from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship
from database import Base

class Account(Base):
    __tablename__ = "accounts"
    id = Column(String(64), primary_key=True, index=True)
    owner_name = Column(String(128), nullable=False)
    created_at = Column(DateTime, default=datetime.now(timezone.utc), index=True)

class Transaction(Base):
    __tablename__ = "transactions"
    id = Column(String(64), primary_key=True, index=True)
    sender_id = Column(String(64), ForeignKey("accounts.id"), index=True, nullable=False)
    receiver_id = Column(String(64), ForeignKey("accounts.id"), index=True, nullable=False)
    amount = Column(Float, nullable=False)
    device_id = Column(String(64), default="DEV_DEFAULT")
    timestamp = Column(DateTime, default=datetime.now(timezone.utc), index=True)

    sender = relationship("Account", foreign_keys=[sender_id])
    receiver = relationship("Account", foreign_keys=[receiver_id])
    audit = relationship("RiskAudit", back_populates="transaction", uselist=False)

class RiskAudit(Base):
    __tablename__ = "risk_audits"
    id = Column(Integer, primary_key=True, autoincrement=True)
    transaction_id = Column(String(64), ForeignKey("transactions.id"), unique=True, nullable=False)
    risk_score = Column(Float, nullable=False)
    decision = Column(String(32), nullable=False)  # APPROVE, CHALLENGE_STEP_UP, BLOCK_AND_REPORT
    trigger_signals = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.now(timezone.utc), index=True)

    transaction = relationship("Transaction", back_populates="audit")