from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, func
from app.core.database import Base


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    action = Column(String(50), nullable=False)  # login, create_order, update_product, etc.
    entity_type = Column(String(50), default="")  # order, product, user, etc.
    entity_id = Column(Integer, nullable=True)
    details = Column(Text, default="")  # JSON string with extra info
    ip_address = Column(String(50), default="")
    created_at = Column(DateTime, server_default=func.now())
