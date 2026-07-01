from typing import Optional

import uuid
from datetime import date, datetime

from sqlalchemy import String, Date, DateTime, ForeignKey, Enum as SAEnum, Float, Boolean, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship
import enum

from app.database import Base


class UserRole(str, enum.Enum):
    employee = "employee"
    manager = "manager"
    admin = "admin"


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    first_name: Mapped[str] = mapped_column(String(100))
    last_name: Mapped[str] = mapped_column(String(100))
    role: Mapped[UserRole] = mapped_column(SAEnum(UserRole), default=UserRole.employee)
    department_id: Mapped[Optional[uuid.UUID]] = mapped_column(Uuid, ForeignKey("departments.id"), nullable=True)
    manager_id: Mapped[Optional[uuid.UUID]] = mapped_column(Uuid, ForeignKey("users.id"), nullable=True)
    position: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    salary: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    hire_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    phone: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    department = relationship("Department", back_populates="employees", foreign_keys=[department_id])
    manager = relationship("User", remote_side="User.id", back_populates="direct_reports", foreign_keys=[manager_id])
    direct_reports = relationship("User", back_populates="manager", foreign_keys=[manager_id])

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"
