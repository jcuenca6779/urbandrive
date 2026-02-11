from typing import Dict, List, Tuple
import logging

from app.redis_client import RedisGamificationClient

logger = logging.getLogger(__name__)


class GamificationService:
    """
    Lógica de gamificación:
    - Sumar XP y UrbanCoins por reporte validado
    - Otorgar insignias según umbrales de XP
    - Manejar eventos de reporte_creado y reporte_validado
    """

    # Recompensas por reporte validado
    XP_PER_VALID_REPORT = 10
    COINS_PER_VALID_REPORT = 5

    # Umbrales de insignias (ajustado: 100 XP = Explorador Urbano)
    BADGE_THRESHOLDS = [
        (100, "Explorador Urbano"),  # Insignia principal a los 100 XP
        (250, "Guardián de la Ciudad"),
        (500, "Héroe del Tráfico"),
        (1000, "Leyenda Urbana"),
    ]

    def __init__(self, redis_client: RedisGamificationClient) -> None:
        self.redis = redis_client

    def process_created_report(self, event: Dict) -> Dict:
        """
        Procesa un evento de 'reporte_creado'.
        Por ahora solo registra el evento, sin recompensas.
        
        Se espera un payload:
        {
            "type": "reporte_creado",
            "data": {
                "reporte_id": int,
                "usuario_id": int,
                ...
            }
        }
        """
        data = event.get("data") or {}
        user_id = data.get("usuario_id")
        if user_id is None:
            logger.warning("Evento reporte_creado sin usuario_id: %s", event)
            return {"error": "usuario_id faltante"}
        
        logger.info("Reporte creado registrado para user_id=%s", user_id)
        return {
            "user_id": user_id,
            "event": "reporte_creado",
            "message": "Reporte registrado, pendiente de validación"
        }

    def process_validated_report(self, event: Dict) -> Dict:
        """
        Procesa un evento de 'reporte_validado'.
        Otorga 10 XP y 5 UrbanCoins al usuario.

        Se espera un payload mínimo:
        {
            "type": "reporte_validado",
            "data": {
                "reporte_id": int,
                "usuario_id": int,
                "severidad": str,  # opcional pero útil para futuras reglas
                ...
            }
        }
        """
        data = event.get("data") or {}
        user_id = data.get("usuario_id")
        if user_id is None:
            logger.warning("Evento reporte_validado sin usuario_id: %s", event)
            return {"error": "usuario_id faltante"}

        # 1) Sumar XP (10 puntos)
        total_xp = self.redis.add_xp(user_id=user_id, xp=self.XP_PER_VALID_REPORT)

        # 2) Sumar UrbanCoins (5 monedas)
        total_coins = self.redis.add_coins(user_id=user_id, coins=self.COINS_PER_VALID_REPORT)

        # 3) Verificar y asignar insignias
        new_badges = self._check_and_assign_badges(user_id, total_xp)

        logger.info(
            "Procesado reporte_validado para user_id=%s, xp_total=%s, coins_total=%s, nuevas_insignias=%s",
            user_id,
            total_xp,
            total_coins,
            new_badges,
        )

        return {
            "user_id": user_id,
            "total_xp": total_xp,
            "total_coins": total_coins,
            "xp_awarded": self.XP_PER_VALID_REPORT,
            "coins_awarded": self.COINS_PER_VALID_REPORT,
            "new_badges": new_badges,
            "all_badges": self.redis.get_badges(user_id),
        }

    def _check_and_assign_badges(self, user_id: int, total_xp: int) -> List[str]:
        """
        Revisa los umbrales de XP y asigna nuevas insignias
        que el usuario aún no tenga.
        """
        existing_badges = set(self.redis.get_badges(user_id))
        new_badges: List[str] = []

        for threshold, badge_name in self.BADGE_THRESHOLDS:
            if total_xp >= threshold and badge_name not in existing_badges:
                self.redis.add_badge(user_id, badge_name)
                new_badges.append(badge_name)

        return new_badges

