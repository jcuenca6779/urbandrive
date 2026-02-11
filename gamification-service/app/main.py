from fastapi import FastAPI, HTTPException, status
from typing import List
import logging

from app.redis_client import RedisGamificationClient
from app.gamification_logic import GamificationService
from app.rabbitmq_consumer import RabbitMQGamificationConsumer
from app.schemas import UserProfileResponse, LeaderboardResponse

logger = logging.getLogger(__name__)

app = FastAPI(
    title="UrbanDrive Gamification Service",
    description="Servicio de gamificación basado en eventos de tráfico",
    version="1.0.0",
)

# Instancias globales (se inicializan en startup)
redis_client: RedisGamificationClient | None = None
gamification_service: GamificationService | None = None
rabbitmq_consumer: RabbitMQGamificationConsumer | None = None


@app.on_event("startup")
async def startup_event():
    """
    Inicializa Redis y el consumidor de RabbitMQ en background.
    """
    global redis_client, gamification_service, rabbitmq_consumer

    logging.basicConfig(level=logging.INFO)
    logger.info("Iniciando UrbanDrive Gamification Service...")

    # Redis
    redis_client = RedisGamificationClient()
    gamification_service = GamificationService(redis_client=redis_client)

    # RabbitMQ consumer
    rabbitmq_consumer = RabbitMQGamificationConsumer(
        gamification_service=gamification_service
    )
    await rabbitmq_consumer.start()
    logger.info("Consumidor de RabbitMQ iniciado")


@app.on_event("shutdown")
async def shutdown_event():
    """
    Cierra conexiones al apagar el servicio.
    """
    global rabbitmq_consumer
    logger.info("Deteniendo UrbanDrive Gamification Service...")
    if rabbitmq_consumer:
        await rabbitmq_consumer.stop()


@app.get("/health")
async def health_check():
    """
    Health check básico del servicio de gamificación.
    """
    return {"status": "ok", "service": "gamification-service"}


@app.get("/info")
async def info():
    """
    Información general del servicio.
    """
    return {
        "service": "gamification-service",
        "description": "Servicio de gamificación de UrbanDrive",
        "events_consumed": ["reporte_creado", "reporte_validado"],
        "rewards": {
            "reporte_validado": {
                "xp": 10,
                "coins": 5
            }
        },
        "badges": {
            "100_xp": "Explorador Urbano"
        }
    }


@app.get(
    "/leaderboard",
    response_model=LeaderboardResponse,
    summary="Leaderboard de usuarios",
    description="Devuelve el ranking de usuarios por XP total acumulado usando Redis ZREVRANGE",
)
async def get_leaderboard(limit: int = 10):
    """
    Endpoint para consultar el ranking de usuarios (Leaderboard).
    
    Utiliza Redis ZREVRANGE para obtener los usuarios con mayor XP de forma eficiente.

    - **limit**: cantidad máxima de usuarios a retornar (default: 10, máximo recomendado: 100)
    """
    if not redis_client:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Redis no está inicializado",
        )

    try:
        if limit < 1 or limit > 100:
            limit = 10
        
        leaderboard = redis_client.get_leaderboard(limit=limit)
        return LeaderboardResponse(leaderboard=leaderboard)
    except Exception as e:
        logger.error(f"Error al obtener leaderboard: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener leaderboard: {e}",
        )


@app.get(
    "/profile/{user_id}",
    response_model=UserProfileResponse,
    summary="Perfil de usuario",
    description="Obtiene el perfil completo del usuario: nivel, XP total, UrbanCoins e insignias",
)
async def get_user_profile(user_id: int):
    """
    Endpoint para obtener el perfil completo de un usuario.
    
    Retorna:
    - **user_id**: ID del usuario
    - **xp**: XP total acumulado
    - **coins**: UrbanCoins totales acumulados
    - **level**: Nivel calculado basado en XP (fórmula: nivel = sqrt(XP / 100) + 1)
    - **badges**: Lista de insignias obtenidas

    - **user_id**: ID del usuario a consultar
    """
    if not redis_client:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Redis no está inicializado",
        )

    try:
        profile = redis_client.get_user_profile(user_id)
        return UserProfileResponse(**profile)
    except Exception as e:
        logger.error(f"Error al obtener perfil del usuario {user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener perfil: {e}",
        )

