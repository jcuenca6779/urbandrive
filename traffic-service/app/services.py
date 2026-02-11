import httpx
import os
from typing import Optional
from app.schemas import ClasificacionSeveridadRequest, ClasificacionSeveridadResponse
from app.models import SeveridadEnum
import logging

logger = logging.getLogger(__name__)

AI_SERVICE_URL = os.getenv("AI_SERVICE_URL", "http://ai-service:8000")


async def clasificar_severidad(
    descripcion: str,
    tipo_incidente: Optional[str] = None,
) -> SeveridadEnum:
    """
    Realiza una petición HTTP sincrónica al ai-service para clasificar la severidad
    del incidente basándose en la descripción (y opcionalmente el tipo).
    
    Args:
        descripcion: Descripción detallada del incidente
        tipo_incidente: Tipo de incidente reportado (opcional)
        
    Returns:
        SeveridadEnum: Severidad clasificada por el AI service
    """
    try:
        request_data = ClasificacionSeveridadRequest(
            tipo_incidente=tipo_incidente or "incidente",
            descripcion=descripcion,
        )

        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                f"{AI_SERVICE_URL}/clasificar-severidad",
                json=request_data.model_dump(),
            )
            response.raise_for_status()

            result = ClasificacionSeveridadResponse(**response.json())
            logger.info(
                f"Severidad clasificada: {result.severidad.value} "
                f"(confianza: {result.confianza})"
            )
            return result.severidad

    except httpx.TimeoutException:
        logger.warning(
            "Timeout al comunicarse con ai-service, usando severidad MEDIA por defecto"
        )
        return SeveridadEnum.MEDIA
    except httpx.HTTPStatusError as e:
        logger.error(
            f"Error HTTP del ai-service: {e.response.status_code} - {e.response.text}"
        )
        return SeveridadEnum.MEDIA
    except httpx.RequestError as e:
        logger.error(f"Error de conexión con ai-service: {str(e)}")
        return SeveridadEnum.MEDIA
    except Exception as e:
        logger.error(f"Error inesperado al clasificar severidad: {str(e)}")
        return SeveridadEnum.MEDIA
