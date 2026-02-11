from pydantic import BaseModel, EmailStr, Field, ConfigDict
from datetime import datetime
from typing import Optional
from app.models import RolEnum


class UsuarioBase(BaseModel):
    """Esquema base para usuario"""
    nombre: str = Field(..., min_length=1, max_length=100, description="Nombre del usuario")
    email: EmailStr = Field(..., description="Email del usuario")
    rol: RolEnum = Field(default=RolEnum.CONDUCTOR, description="Rol del usuario")


class UsuarioCreate(UsuarioBase):
    """Esquema para crear un usuario"""
    password: str = Field(..., min_length=8, max_length=100, description="Contraseña del usuario (mínimo 8 caracteres)")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "nombre": "Juan Pérez",
                "email": "juan.perez@example.com",
                "password": "password123",
                "rol": "conductor"
            }
        }
    )


class UsuarioResponse(UsuarioBase):
    """Esquema para la respuesta de usuario"""
    id: int
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class UsuarioLogin(BaseModel):
    """Esquema para login"""
    email: EmailStr = Field(..., description="Email del usuario")
    password: str = Field(..., description="Contraseña del usuario")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "email": "juan.perez@example.com",
                "password": "password123"
            }
        }
    )


class TokenResponse(BaseModel):
    """Esquema para respuesta de token"""
    access_token: str = Field(..., description="Token JWT de acceso")
    token_type: str = Field(default="bearer", description="Tipo de token")
    expires_in: int = Field(..., description="Tiempo de expiración en segundos")
    user: UsuarioResponse = Field(..., description="Información del usuario autenticado")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "token_type": "bearer",
                "expires_in": 3600,
                "user": {
                    "id": 1,
                    "nombre": "Juan Pérez",
                    "email": "juan.perez@example.com",
                    "rol": "conductor"
                }
            }
        }
    )


class TokenData(BaseModel):
    """Esquema para datos del token"""
    user_id: Optional[int] = None
    email: Optional[str] = None
