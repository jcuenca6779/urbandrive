"""
Detección de anomalías estadística basada en hora y ubicación
"""
import redis
import os
import json
from datetime import datetime, timedelta
from typing import Optional
import logging
from collections import defaultdict

logger = logging.getLogger(__name__)


class AnomalyDetector:
    """Detector de anomalías estadístico para reportes de tráfico"""
    
    def __init__(self):
        """Inicializa el detector con conexión a Redis"""
        redis_url = os.getenv("REDIS_URL", "redis://redis:6379/0")
        try:
            # Parsear URL de Redis
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
            
            self.redis_client = redis.Redis(
                host=host,
                port=port,
                db=db,
                decode_responses=True,
                socket_connect_timeout=5
            )
            # Test connection
            self.redis_client.ping()
            logger.info("Conexión a Redis establecida para detección de anomalías")
        except Exception as e:
            logger.warning(f"No se pudo conectar a Redis: {str(e)}. Usando modo sin persistencia.")
            self.redis_client = None
            self._local_stats = defaultdict(lambda: defaultdict(int))
    
    def _get_location_key(self, ubicacion: str) -> str:
        """Normaliza la clave de ubicación"""
        # Normalizar ubicación (remover espacios extras, convertir a minúsculas)
        return ubicacion.strip().lower()
    
    def _get_hour_key(self, hora: datetime) -> str:
        """Obtiene la clave de hora (formato: HH)"""
        return str(hora.hour).zfill(2)
    
    def _get_date_key(self, hora: datetime) -> str:
        """Obtiene la clave de fecha (formato: YYYY-MM-DD)"""
        return hora.strftime("%Y-%m-%d")
    
    def _get_stats_key(self, ubicacion: str, hora: datetime) -> str:
        """Genera clave para estadísticas de ubicación y hora"""
        location_key = self._get_location_key(ubicacion)
        hour_key = self._get_hour_key(hora)
        return f"stats:location:{location_key}:hour:{hour_key}"
    
    def _get_daily_stats_key(self, ubicacion: str, fecha: str) -> str:
        """Genera clave para estadísticas diarias de ubicación"""
        location_key = self._get_location_key(ubicacion)
        return f"stats:location:{location_key}:date:{fecha}"
    
    def record_report(self, ubicacion: str, hora: datetime, tipo_incidente: Optional[str] = None):
        """
        Registra un reporte para análisis estadístico
        
        Args:
            ubicacion: Ubicación del reporte
            hora: Hora del reporte
            tipo_incidente: Tipo de incidente (opcional)
        """
        try:
            hour_key = self._get_hour_key(hora)
            date_key = self._get_date_key(hora)
            stats_key = self._get_stats_key(ubicacion, hora)
            daily_key = self._get_daily_stats_key(ubicacion, date_key)
            
            if self.redis_client:
                # Incrementar contador por hora
                self.redis_client.incr(stats_key)
                # Incrementar contador diario
                self.redis_client.incr(daily_key)
                # Expirar después de 30 días
                self.redis_client.expire(stats_key, 30 * 24 * 3600)
                self.redis_client.expire(daily_key, 30 * 24 * 3600)
            else:
                # Modo local sin Redis
                self._local_stats[stats_key] += 1
                self._local_stats[daily_key] += 1
                
        except Exception as e:
            logger.error(f"Error al registrar reporte: {str(e)}")
    
    def get_statistics(self, ubicacion: str, hora: datetime) -> dict:
        """
        Obtiene estadísticas históricas para una ubicación y hora
        
        Args:
            ubicacion: Ubicación a analizar
            hora: Hora a analizar
            
        Returns:
            Diccionario con estadísticas
        """
        try:
            location_key = self._get_location_key(ubicacion)
            hour_key = self._get_hour_key(hora)
            
            # Obtener estadísticas de la hora específica
            stats_key = self._get_stats_key(ubicacion, hora)
            
            # Obtener estadísticas de todas las horas del día para esta ubicación
            hourly_counts = {}
            daily_total = 0
            
            if self.redis_client:
                # Contar reportes en esta hora específica
                count_this_hour = int(self.redis_client.get(stats_key) or 0)
                
                # Obtener estadísticas de todas las horas (últimos 7 días)
                for h in range(24):
                    hour_str = str(h).zfill(2)
                    key = f"stats:location:{location_key}:hour:{hour_str}"
                    count = int(self.redis_client.get(key) or 0)
                    hourly_counts[hour_str] = count
                    daily_total += count
            else:
                # Modo local
                count_this_hour = self._local_stats.get(stats_key, 0)
                for h in range(24):
                    hour_str = str(h).zfill(2)
                    key = f"stats:location:{location_key}:hour:{hour_str}"
                    hourly_counts[hour_str] = self._local_stats.get(key, 0)
                    daily_total += hourly_counts[hour_str]
            
            # Calcular promedio por hora
            avg_per_hour = daily_total / 24 if daily_total > 0 else 0
            
            return {
                "count_this_hour": count_this_hour,
                "hourly_average": avg_per_hour,
                "daily_total": daily_total,
                "hourly_distribution": hourly_counts
            }
            
        except Exception as e:
            logger.error(f"Error al obtener estadísticas: {str(e)}")
            return {
                "count_this_hour": 0,
                "hourly_average": 0,
                "daily_total": 0,
                "hourly_distribution": {}
            }
    
    def detect_anomaly(self, ubicacion: str, hora: datetime, tipo_incidente: Optional[str] = None) -> tuple[bool, float, str, dict]:
        """
        Detecta si un reporte es una anomalía estadística
        
        Args:
            ubicacion: Ubicación del reporte
            hora: Hora del reporte
            tipo_incidente: Tipo de incidente (opcional)
            
        Returns:
            Tupla con (es_anomalia, score_anomalia, razon, estadisticas)
        """
        stats = self.get_statistics(ubicacion, hora)
        
        count_this_hour = stats["count_this_hour"]
        hourly_avg = stats["hourly_average"]
        daily_total = stats["daily_total"]
        
        # Si no hay datos históricos suficientes, considerar normal
        if daily_total < 5:
            return (
                False,
                0.2,
                "No hay suficientes datos históricos para determinar anomalía",
                stats
            )
        
        # Calcular desviación estándar aproximada (usando promedio como referencia)
        # Si el conteo actual es mucho mayor que el promedio, es una anomalía
        deviation_ratio = count_this_hour / hourly_avg if hourly_avg > 0 else 0
        
        # Umbrales para detección de anomalías
        # Si hay más de 3 veces el promedio, es una anomalía
        if deviation_ratio > 3.0:
            score = min(0.9, 0.5 + (deviation_ratio - 3.0) * 0.1)
            return (
                True,
                score,
                f"Reporte inusual: {count_this_hour} reportes en esta hora vs promedio de {hourly_avg:.2f}",
                stats
            )
        
        # Si hay más de 2 veces el promedio, es una posible anomalía
        if deviation_ratio > 2.0:
            score = 0.6 + (deviation_ratio - 2.0) * 0.2
            return (
                True,
                min(score, 0.85),
                f"Posible anomalía: {count_this_hour} reportes en esta hora vs promedio de {hourly_avg:.2f}",
                stats
            )
        
        # Verificar si es una hora inusual (muy temprano o muy tarde)
        hour = hora.hour
        if hour < 5 or hour > 23:
            if count_this_hour > 0:
                return (
                    True,
                    0.7,
                    f"Reporte en hora inusual ({hour}:00) con {count_this_hour} reportes",
                    stats
                )
        
        # Si no hay anomalías detectadas
        return (
            False,
            max(0.1, 1.0 - deviation_ratio * 0.2),
            f"Patrón normal: {count_this_hour} reportes en esta hora (promedio: {hourly_avg:.2f})",
            stats
        )
