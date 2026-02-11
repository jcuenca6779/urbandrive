from sqlalchemy import Column, Integer, String, DateTime, Enum as SQLEnum, Float, ForeignKey, UniqueConstraint
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base
import enum


class SeveridadEnum(str, enum.Enum):
    """Enum para los niveles de severidad"""
    BAJA = "baja"
    MEDIA = "media"
    ALTA = "alta"
    CRITICA = "critica"


class EstadoIncidenteEnum(str, enum.Enum):
    """Enum para el estado del incidente"""
    PENDIENTE = "pendiente"
    VALIDADO = "validado"
    VERIFICADO = "verificado"
    ARCHIVADO = "archivado"


class Incidente(Base):
    """Modelo SQLAlchemy para incidentes de tráfico"""
    __tablename__ = "incidentes_trafico"

    id = Column(Integer, primary_key=True, index=True)
    tipo = Column(String(100), nullable=False, index=True)  # bache, choque, etc.
    descripcion = Column(String(1000), nullable=False)
    latitud = Column(Float, nullable=False, index=True)
    longitud = Column(Float, nullable=False, index=True)
    severidad = Column(SQLEnum(SeveridadEnum), nullable=False, index=True)
    estado = Column(SQLEnum(EstadoIncidenteEnum), nullable=False, default=EstadoIncidenteEnum.PENDIENTE, index=True)
    usuario_id = Column(Integer, nullable=False, index=True)
    validaciones_count = Column(Integer, nullable=False, default=0, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relación con validaciones
    validaciones = relationship("ValidacionIncidente", back_populates="incidente", cascade="all, delete-orphan")

    def __repr__(self):
        return (
            f"<Incidente(id={self.id}, tipo='{self.tipo}', "
            f"severidad='{self.severidad.value}', estado='{self.estado.value}', "
            f"validaciones={self.validaciones_count})>"
        )


class ValidacionIncidente(Base):
    """Modelo para rastrear validaciones de usuarios sobre incidentes"""
    __tablename__ = "validaciones_incidentes"

    id = Column(Integer, primary_key=True, index=True)
    incidente_id = Column(Integer, ForeignKey("incidentes_trafico.id", ondelete="CASCADE"), nullable=False, index=True)
    usuario_id = Column(Integer, nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relación con incidente
    incidente = relationship("Incidente", back_populates="validaciones")

    # Constraint único: un usuario solo puede validar un incidente una vez
    __table_args__ = (
        UniqueConstraint('incidente_id', 'usuario_id', name='uq_validacion_usuario_incidente'),
    )

    def __repr__(self):
        return (
            f"<ValidacionIncidente(id={self.id}, incidente_id={self.incidente_id}, "
            f"usuario_id={self.usuario_id})>"
        )
