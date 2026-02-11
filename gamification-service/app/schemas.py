from pydantic import BaseModel, Field, ConfigDict
from typing import List


class UserProfileResponse(BaseModel):
    """Esquema para la respuesta del perfil de usuario"""
    user_id: int = Field(..., description="ID del usuario")
    xp: int = Field(..., ge=0, description="XP total acumulado")
    coins: int = Field(..., ge=0, description="UrbanCoins totales acumulados")
    level: int = Field(..., ge=1, description="Nivel del usuario basado en XP")
    badges: List[str] = Field(default_factory=list, description="Lista de insignias obtenidas")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "user_id": 1,
                "xp": 150,
                "coins": 75,
                "level": 2,
                "badges": ["Explorador Urbano"]
            }
        }
    )


class LeaderboardEntry(BaseModel):
    """Esquema para una entrada del leaderboard"""
    rank: int = Field(..., ge=1, description="Posición en el ranking")
    user_id: int = Field(..., description="ID del usuario")
    xp: int = Field(..., ge=0, description="XP total del usuario")


class LeaderboardResponse(BaseModel):
    """Esquema para la respuesta del leaderboard"""
    leaderboard: List[LeaderboardEntry] = Field(..., description="Lista de usuarios en el ranking")
