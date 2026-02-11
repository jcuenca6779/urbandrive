from sqlalchemy import Column, Integer, String, DateTime, Enum as SQLEnum
from sqlalchemy.sql import func
from app.database import Base
import enum


class RolEnum(str, enum.Enum):
    """Enum para los roles de usuario"""
    CONDUCTOR = "conductor"
    COLABORADOR = "colaborador"
    ADMIN = "admin"


class Usuario(Base):
    """Modelo SQLAlchemy para usuarios"""
    __tablename__ = "usuarios"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(100), nullable=False)
    email = Column(String(255), nullable=False, unique=True, index=True)
    password_hash = Column(String(255), nullable=False)
    rol = Column(SQLEnum(RolEnum), nullable=False, default=RolEnum.CONDUCTOR)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    is_active = Column(String(10), default="true", nullable=False)

    def __repr__(self):
        return f"<Usuario(id={self.id}, email='{self.email}', rol='{self.rol.value}')>"
