"""
Persistencia de datos de entrenamiento para re-entrenamiento de modelos
"""
import os
import logging
from datetime import datetime
from typing import List, Optional
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Float, Boolean, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session

logger = logging.getLogger(__name__)

Base = declarative_base()


class TrainingExample(Base):
    """Modelo para almacenar ejemplos de entrenamiento"""
    __tablename__ = "training_examples"
    
    id = Column(Integer, primary_key=True, index=True)
    descripcion = Column(Text, nullable=True)  # Para análisis de sentimiento
    tipo_incidente = Column(String(100), nullable=True)
    hora = Column(DateTime, nullable=True)
    latitud = Column(Float, nullable=True)
    longitud = Column(Float, nullable=True)
    
    # Etiquetas
    severidad_label = Column(String(20), nullable=True)  # baja, media, alta, critica
    is_false_positive = Column(Boolean, nullable=True)  # True si es falso positivo
    
    # Metadatos
    usuario_id = Column(Integer, nullable=True)  # Usuario que marcó el ejemplo
    incidente_id = Column(Integer, nullable=True)  # ID del incidente original
    created_at = Column(DateTime, default=datetime.utcnow)
    
    def to_dict(self) -> dict:
        """Convierte el ejemplo a diccionario"""
        return {
            'id': self.id,
            'descripcion': self.descripcion,
            'tipo_incidente': self.tipo_incidente,
            'hora': self.hora.isoformat() if self.hora else None,
            'latitud': self.latitud,
            'longitud': self.longitud,
            'severidad_label': self.severidad_label,
            'is_false_positive': self.is_false_positive,
            'usuario_id': self.usuario_id,
            'incidente_id': self.incidente_id,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class TrainingDataManager:
    """Gestor de datos de entrenamiento"""
    
    def __init__(self):
        """Inicializa el gestor con conexión a base de datos"""
        database_url = os.getenv(
            "DATABASE_URL",
            "postgresql://urban_user:urban_pass_secure_2024@postgres:5432/ai_db"
        )
        
        try:
            self.engine = create_engine(database_url, pool_pre_ping=True)
            self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
            
            # Crear tablas si no existen
            Base.metadata.create_all(bind=self.engine)
            
            logger.info("Conexión a base de datos establecida para datos de entrenamiento")
        except Exception as e:
            logger.error(f"Error al conectar a base de datos: {str(e)}")
            self.engine = None
            self.SessionLocal = None
    
    def get_db(self) -> Session:
        """Obtiene una sesión de base de datos"""
        if not self.SessionLocal:
            raise Exception("Base de datos no inicializada")
        return self.SessionLocal()
    
    def add_example(
        self,
        descripcion: Optional[str] = None,
        tipo_incidente: Optional[str] = None,
        hora: Optional[datetime] = None,
        latitud: Optional[float] = None,
        longitud: Optional[float] = None,
        severidad_label: Optional[str] = None,
        is_false_positive: Optional[bool] = None,
        usuario_id: Optional[int] = None,
        incidente_id: Optional[int] = None
    ) -> TrainingExample:
        """
        Agrega un ejemplo de entrenamiento
        
        Returns:
            Ejemplo de entrenamiento creado
        """
        if not self.SessionLocal:
            raise Exception("Base de datos no inicializada")
        
        db = self.get_db()
        try:
            example = TrainingExample(
                descripcion=descripcion,
                tipo_incidente=tipo_incidente,
                hora=hora,
                latitud=latitud,
                longitud=longitud,
                severidad_label=severidad_label,
                is_false_positive=is_false_positive,
                usuario_id=usuario_id,
                incidente_id=incidente_id
            )
            
            db.add(example)
            db.commit()
            db.refresh(example)
            
            logger.info(f"Ejemplo de entrenamiento agregado: ID {example.id}")
            return example
        except Exception as e:
            db.rollback()
            logger.error(f"Error al agregar ejemplo: {str(e)}")
            raise
        finally:
            db.close()
    
    def get_sentiment_examples(self, limit: Optional[int] = None) -> List[TrainingExample]:
        """Obtiene ejemplos para entrenamiento de análisis de sentimiento"""
        if not self.SessionLocal:
            return []
        
        db = self.get_db()
        try:
            query = db.query(TrainingExample).filter(
                TrainingExample.descripcion.isnot(None),
                TrainingExample.severidad_label.isnot(None)
            )
            
            if limit:
                query = query.limit(limit)
            
            return query.all()
        finally:
            db.close()
    
    def get_false_positive_examples(self, limit: Optional[int] = None) -> List[TrainingExample]:
        """Obtiene ejemplos para entrenamiento de detección de falsos positivos"""
        if not self.SessionLocal:
            return []
        
        db = self.get_db()
        try:
            query = db.query(TrainingExample).filter(
                TrainingExample.hora.isnot(None),
                TrainingExample.latitud.isnot(None),
                TrainingExample.longitud.isnot(None),
                TrainingExample.tipo_incidente.isnot(None),
                TrainingExample.is_false_positive.isnot(None)
            )
            
            if limit:
                query = query.limit(limit)
            
            return query.all()
        finally:
            db.close()


# Instancia global del gestor
training_data_manager = TrainingDataManager()
