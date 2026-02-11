from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from typing import Optional, List, Dict, Any
from app.models import SeveridadEnum, EstadoIncidenteEnum


class IncidenteCreate(BaseModel):
    """Esquema para crear un incidente de tráfico"""
    tipo: str = Field(..., min_length=1, max_length=100, description="Tipo de incidente (bache, choque, etc.)")
    descripcion: str = Field(..., min_length=1, max_length=1000, description="Descripción detallada del incidente")
    latitud: float = Field(..., description="Latitud del incidente")
    longitud: float = Field(..., description="Longitud del incidente")
    usuario_id: int = Field(..., gt=0, description="ID del usuario que reporta")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "tipo": "choque",
                "descripcion": "Choque entre dos vehículos en la intersección principal",
                "latitud": -12.0464,
                "longitud": -77.0428,
                "usuario_id": 1
            }
        }
    )


class IncidenteResponse(BaseModel):
    """Esquema para la respuesta de un incidente de tráfico"""
    id: int
    tipo: str
    descripcion: str
    latitud: float
    longitud: float
    severidad: SeveridadEnum
    estado: EstadoIncidenteEnum
    usuario_id: int
    validaciones_count: int = Field(default=0, description="Número de validaciones recibidas")
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class ClasificacionSeveridadRequest(BaseModel):
    """Esquema para la petición al ai-service"""
    tipo_incidente: str
    descripcion: str


class ClasificacionSeveridadResponse(BaseModel):
    """Esquema para la respuesta del ai-service"""
    severidad: SeveridadEnum
    confianza: Optional[float] = Field(None, ge=0.0, le=1.0, description="Nivel de confianza de la clasificación")


# ============================================
# Esquemas GeoJSON
# ============================================

class PointGeometry(BaseModel):
    """Geometría Point para GeoJSON"""
    type: str = Field(default="Point", description="Tipo de geometría")
    coordinates: List[float] = Field(..., description="[longitud, latitud] en formato GeoJSON")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "type": "Point",
                "coordinates": [-77.0428, -12.0464]
            }
        }
    )


class IncidenteGeoJSONFeature(BaseModel):
    """Feature individual en formato GeoJSON"""
    type: str = Field(default="Feature", description="Tipo de feature GeoJSON")
    geometry: PointGeometry = Field(..., description="Geometría del punto")
    properties: Dict[str, Any] = Field(..., description="Propiedades del incidente")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": [-77.0428, -12.0464]
                },
                "properties": {
                    "id": 1,
                    "tipo": "choque",
                    "descripcion": "Choque frontal",
                    "severidad": "alta",
                    "estado": "pendiente",
                    "usuario_id": 1,
                    "distancia_km": 2.5,
                    "created_at": "2024-02-06T10:00:00Z"
                }
            }
        }
    )


class IncidenteGeoJSONCollection(BaseModel):
    """FeatureCollection en formato GeoJSON"""
    type: str = Field(default="FeatureCollection", description="Tipo de colección GeoJSON")
    features: List[IncidenteGeoJSONFeature] = Field(default_factory=list, description="Lista de features")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "type": "FeatureCollection",
                "features": [
                    {
                        "type": "Feature",
                        "geometry": {
                            "type": "Point",
                            "coordinates": [-77.0428, -12.0464]
                        },
                        "properties": {
                            "id": 1,
                            "tipo": "choque",
                            "descripcion": "Choque frontal",
                            "severidad": "alta",
                            "estado": "pendiente"
                        }
                    }
                ]
            }
        }
    )


# ============================================
# Esquemas para Validación Social
# ============================================

class ValidacionRequest(BaseModel):
    """Esquema para validar un incidente"""
    usuario_id: int = Field(..., gt=0, description="ID del usuario que valida el incidente")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "usuario_id": 2
            }
        }
    )


class ValidacionResponse(BaseModel):
    """Esquema para la respuesta de validación"""
    incidente_id: int
    usuario_id: int
    validaciones_count: int = Field(..., description="Número total de validaciones del incidente")
    estado: EstadoIncidenteEnum = Field(..., description="Estado actual del incidente")
    verificado: bool = Field(..., description="True si el incidente fue verificado (3+ validaciones)")
    mensaje: str = Field(..., description="Mensaje descriptivo del resultado")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "incidente_id": 1,
                "usuario_id": 2,
                "validaciones_count": 3,
                "estado": "verificado",
                "verificado": True,
                "mensaje": "Incidente verificado con 3 validaciones"
            }
        }
    )
