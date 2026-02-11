from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, Literal
from datetime import datetime


class ClasificacionSeveridadRequest(BaseModel):
    """Esquema para la petición de clasificación de severidad"""
    tipo_incidente: str = Field(..., description="Tipo de incidente")
    descripcion: str = Field(..., description="Descripción detallada del incidente")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "tipo_incidente": "Accidente",
                "descripcion": "Choque entre dos vehículos, tráfico lento"
            }
        }
    )


class ClasificacionSeveridadResponse(BaseModel):
    """Esquema para la respuesta de clasificación de severidad"""
    severidad: Literal["baja", "media", "alta", "critica"] = Field(..., description="Severidad clasificada")
    confianza: float = Field(..., ge=0.0, le=1.0, description="Nivel de confianza de la clasificación")


class ClasificacionIncidenteRequest(BaseModel):
    """Esquema para la petición de clasificación de tipo de incidente"""
    descripcion: str = Field(..., min_length=1, description="Descripción del incidente")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "descripcion": "Choque frontal entre dos autos en la intersección principal"
            }
        }
    )


class ClasificacionIncidenteResponse(BaseModel):
    """Esquema para la respuesta de clasificación de tipo de incidente"""
    tipo_incidente: Literal["Accidente Grave", "Tráfico Ligero", "Peligro en Vía"] = Field(
        ..., 
        description="Tipo de incidente clasificado"
    )
    confianza: float = Field(..., ge=0.0, le=1.0, description="Nivel de confianza de la clasificación")
    palabras_clave: list[str] = Field(default_factory=list, description="Palabras clave detectadas")


class DeteccionAnomaliaRequest(BaseModel):
    """Esquema para la petición de detección de anomalías"""
    ubicacion: str = Field(..., description="Ubicación del reporte")
    hora: datetime = Field(..., description="Hora del reporte")
    tipo_incidente: Optional[str] = Field(None, description="Tipo de incidente (opcional)")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "ubicacion": "Av. Principal 123",
                "hora": "2024-02-06T15:30:00",
                "tipo_incidente": "Accidente Grave"
            }
        }
    )


class DeteccionAnomaliaResponse(BaseModel):
    """Esquema para la respuesta de detección de anomalías"""
    es_anomalia: bool = Field(..., description="Indica si el reporte es una anomalía")
    score_anomalia: float = Field(..., ge=0.0, le=1.0, description="Score de anomalía (0=normal, 1=muy anormal)")
    razon: str = Field(..., description="Razón por la cual se considera o no una anomalía")
    estadisticas: dict = Field(default_factory=dict, description="Estadísticas históricas de la ubicación")


# ============================================
# Esquemas para Entrenamiento de Modelos
# ============================================

class TrainingExampleRequest(BaseModel):
    """Esquema para agregar un ejemplo de entrenamiento"""
    descripcion: Optional[str] = Field(None, description="Descripción del incidente (para análisis de sentimiento)")
    tipo_incidente: Optional[str] = Field(None, description="Tipo de incidente")
    hora: Optional[datetime] = Field(None, description="Hora del reporte (para detección de falsos positivos)")
    latitud: Optional[float] = Field(None, description="Latitud del reporte")
    longitud: Optional[float] = Field(None, description="Longitud del reporte")
    
    # Etiquetas
    severidad_label: Optional[Literal["baja", "media", "alta", "critica"]] = Field(
        None, 
        description="Etiqueta de severidad correcta (para re-entrenar modelo de sentimiento)"
    )
    is_false_positive: Optional[bool] = Field(
        None, 
        description="True si es falso positivo, False si es válido (para re-entrenar modelo de falsos positivos)"
    )
    
    # Metadatos
    usuario_id: Optional[int] = Field(None, description="ID del usuario que marca el ejemplo")
    incidente_id: Optional[int] = Field(None, description="ID del incidente original")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "descripcion": "Choque entre dos vehículos",
                "tipo_incidente": "choque",
                "hora": "2024-02-06T15:30:00",
                "latitud": -12.0464,
                "longitud": -77.0428,
                "severidad_label": "alta",
                "is_false_positive": False,
                "usuario_id": 1,
                "incidente_id": 123
            }
        }
    )


class TrainingRequest(BaseModel):
    """Esquema para solicitar re-entrenamiento de modelos"""
    model_type: Literal["sentiment", "false_positive", "both"] = Field(
        ...,
        description="Tipo de modelo a re-entrenar: 'sentiment', 'false_positive', o 'both'"
    )
    examples: list[TrainingExampleRequest] = Field(
        ...,
        min_length=1,
        description="Lista de ejemplos de entrenamiento"
    )
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "model_type": "both",
                "examples": [
                    {
                        "descripcion": "Choque grave con heridos",
                        "severidad_label": "alta",
                        "is_false_positive": False
                    },
                    {
                        "hora": "2024-02-06T03:00:00",
                        "latitud": -12.5,
                        "longitud": -78.0,
                        "tipo_incidente": "choque",
                        "is_false_positive": True
                    }
                ]
            }
        }
    )


class TrainingResponse(BaseModel):
    """Esquema para la respuesta de entrenamiento"""
    success: bool = Field(..., description="Indica si el entrenamiento fue exitoso")
    model_type: str = Field(..., description="Tipo de modelo entrenado")
    examples_used: int = Field(..., description="Número de ejemplos usados para entrenar")
    message: str = Field(..., description="Mensaje descriptivo del resultado")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "success": True,
                "model_type": "both",
                "examples_used": 10,
                "message": "Modelos re-entrenados exitosamente con 10 ejemplos nuevos"
            }
        }
    )


class DeteccionFalsoPositivoRequest(BaseModel):
    """Esquema para la petición de detección de falsos positivos"""
    hora: datetime = Field(..., description="Hora del reporte")
    latitud: float = Field(..., description="Latitud del reporte")
    longitud: float = Field(..., description="Longitud del reporte")
    tipo_incidente: str = Field(..., description="Tipo de incidente reportado")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "hora": "2024-02-06T15:30:00",
                "latitud": -12.0464,
                "longitud": -77.0428,
                "tipo_incidente": "choque"
            }
        }
    )


class DeteccionFalsoPositivoResponse(BaseModel):
    """Esquema para la respuesta de detección de falsos positivos"""
    es_falso_positivo: bool = Field(..., description="Indica si el reporte es probablemente un falso positivo")
    probabilidad: float = Field(..., ge=0.0, le=1.0, description="Probabilidad de ser falso positivo (0-1)")
    hora: str = Field(..., description="Hora del reporte (ISO format)")
    latitud: float = Field(..., description="Latitud del reporte")
    longitud: float = Field(..., description="Longitud del reporte")
    tipo_incidente: str = Field(..., description="Tipo de incidente reportado")
