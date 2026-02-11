import os
import redis
import logging
import math
from typing import List, Dict

logger = logging.getLogger(__name__)


class RedisGamificationClient:
    """
    Cliente de Redis para manejar XP, niveles, UrbanCoins e insignias de usuarios.

    Estructura de claves:
    - user:{user_id}:xp              -> XP total del usuario (string-int)
    - user:{user_id}:coins           -> UrbanCoins totales del usuario (string-int)
    - user:{user_id}:badges          -> conjunto (set) de insignias
    - leaderboard:xp                 -> sorted set (user_id -> xp) usando ZADD y ZREVRANGE
    """

    def __init__(self) -> None:
        redis_url = os.getenv("REDIS_URL", "redis://redis:6379/0")

        # Parseo simple de URL (redis://host:port/db)
        if redis_url.startswith("redis://"):
            redis_url = redis_url.replace("redis://", "")

        host_port = redis_url.split("/")[0]
        if ":" in host_port:
            host, port = host_port.split(":")
            port = int(port)
        else:
            host = host_port
            port = 6379

        db = int(redis_url.split("/")[-1]) if "/" in redis_url else 0

        self.client = redis.Redis(
            host=host,
            port=port,
            db=db,
            decode_responses=True,
        )

        try:
            self.client.ping()
            logger.info("Conectado a Redis para gamificación")
        except Exception as e:
            logger.error(f"No se pudo conectar a Redis: {e}")
            raise

    # ---- Claves auxiliares ----

    def _xp_key(self, user_id: int) -> str:
        return f"user:{user_id}:xp"

    def _badges_key(self, user_id: int) -> str:
        return f"user:{user_id}:badges"
    
    def _coins_key(self, user_id: int) -> str:
        return f"user:{user_id}:coins"

    # ---- XP y leaderboard ----

    def add_xp(self, user_id: int, xp: int) -> int:
        """
        Suma XP al usuario y actualiza el leaderboard.
        Devuelve el XP total acumulado.
        """
        total_xp = self.client.incrby(self._xp_key(user_id), xp)
        # Sorted set: score = XP, member = user_id
        self.client.zadd("leaderboard:xp", {str(user_id): total_xp})
        return total_xp

    def get_xp(self, user_id: int) -> int:
        value = self.client.get(self._xp_key(user_id))
        return int(value) if value is not None else 0

    def get_leaderboard(self, limit: int = 10) -> List[Dict]:
        """
        Devuelve top N usuarios ordenados por XP descendente usando ZREVRANGE.
        """
        # Usar ZREVRANGE con WITHSCORES para obtener ranking descendente
        results = self.client.zrevrange("leaderboard:xp", 0, limit - 1, withscores=True)
        leaderboard = []
        for idx, (user_id, xp) in enumerate(results, start=1):
            leaderboard.append(
                {
                    "rank": idx,
                    "user_id": int(user_id),
                    "xp": int(xp),
                }
            )
        return leaderboard

    # ---- UrbanCoins ----
    
    def add_coins(self, user_id: int, coins: int) -> int:
        """
        Suma UrbanCoins al usuario.
        Devuelve el total de UrbanCoins acumulado.
        """
        total_coins = self.client.incrby(self._coins_key(user_id), coins)
        return total_coins
    
    def get_coins(self, user_id: int) -> int:
        """Obtiene el total de UrbanCoins del usuario"""
        value = self.client.get(self._coins_key(user_id))
        return int(value) if value is not None else 0

    # ---- Insignias ----

    def add_badge(self, user_id: int, badge: str) -> None:
        """Agrega una insignia al usuario"""
        self.client.sadd(self._badges_key(user_id), badge)

    def get_badges(self, user_id: int) -> List[str]:
        """Obtiene todas las insignias del usuario"""
        return list(self.client.smembers(self._badges_key(user_id)))
    
    # ---- Perfil completo ----
    
    def get_user_profile(self, user_id: int) -> Dict:
        """
        Obtiene el perfil completo del usuario: XP, UrbanCoins, insignias y nivel.
        """
        xp = self.get_xp(user_id)
        coins = self.get_coins(user_id)
        badges = self.get_badges(user_id)
        
        # Calcular nivel basado en XP (fórmula: nivel = sqrt(XP / 100) + 1)
        level = int(math.sqrt(max(xp, 0) / 100)) + 1
        
        return {
            "user_id": user_id,
            "xp": xp,
            "coins": coins,
            "level": level,
            "badges": badges
        }

