from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text, func
from sqlalchemy.orm import relationship
from app.core.database import Base


class AnomalyAlert(Base):
    __tablename__ = "anomaly_alerts"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(String(50), default="")
    risk_score = Column(Float, default=0.0)
    risk_level = Column(String(20), default="NORMAL")  # NORMAL, ALERTE, CRITIQUE
    predicted_label = Column(Integer, default=0)  # 0=normal, 1=anomaly
    anomaly_type = Column(String(100), default="")
    reason_codes = Column(Text, default="")  # JSON list
    alert_explanation = Column(Text, default="")
    model_name = Column(String(50), default="Random Forest")
    status = Column(String(30), default="new")  # new, assigned, under_review, confirmed_fraud, false_positive, escalated, closed
    assigned_to = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    comments = relationship("AlertComment", back_populates="alert", cascade="all, delete-orphan")


class AlertComment(Base):
    __tablename__ = "alert_comments"

    id = Column(Integer, primary_key=True, index=True)
    alert_id = Column(Integer, ForeignKey("anomaly_alerts.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    comment = Column(Text, nullable=False)
    action = Column(String(50), default="")  # status_change, comment, escalate
    created_at = Column(DateTime, server_default=func.now())

    alert = relationship("AnomalyAlert", back_populates="comments")
