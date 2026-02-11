from fastapi import FastAPI, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List
import logging

from app.database import get_db, init_db
from app.models import Incidente, EstadoIncidenteEnum, ValidacionIncidente
from app.schemas import (
    IncidenteCreate, 
    IncidenteResponse,
    IncidenteGeoJSONCollection,
    IncidenteGeoJSONFeature,
    PointGeometry,
    ValidacionRequest,
    ValidacionResponse
)
from app.services import clasificar_severidad
from app.geospatial import haversine_distance, calculate_bounding_box
from app.rabbitmq_producer import get_producer, close_producer

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="UrbanDrive Traffic Service",
    description="Servicio para gestionar incidentes de tráfico e integrarse con IA",
    version="1.1.0",
)


@app.on_event("startup")
async def startup_event():
    """Inicializar base de datos y RabbitMQ producer al arrancar la aplicación"""
    logger.info("Inicializando base de datos...")
    init_db()
    logger.info("Base de datos inicializada correctamente")
    
    # Inicializar producer de RabbitMQ
    try:
        producer = await get_producer()
        logger.info("Producer de RabbitMQ inicializado correctamente")
    except Exception as e:
        logger.warning("No se pudo inicializar RabbitMQ producer: %s. El servicio continuará sin publicar eventos.", e)


@app.get("/health")
async def health_check():
    """Endpoint de salud del servicio"""
    return {"status": "ok", "service": "traffic-service"}


@app.get("/info")
async def info():
    """Información del servicio"""
    return {
        "service": "traffic-service",
        "description": "Servicio de tráfico y rutas de UrbanDrive",
        "endpoints": {
            "POST /reportar": "Reportar incidente de tráfico (clasificación IA)",
            "GET /reportes": "Listar incidentes activos",
            "GET /reportes/cercanos": "Obtener incidentes cercanos en formato GeoJSON",
            "POST /reportes/{reporte_id}/validar": "Validar un reporte de incidente (validación social)",
        },
    }


@app.post(
    "/reportar",
    response_model=IncidenteResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Reportar un incidente de tráfico",
    description=(
        "Recibe un incidente, llama al ai-service para clasificar la severidad "
        "y guarda el incidente en la base de datos con estado 'pendiente'."
    ),
)
async def reportar_incidente(
    incidente: IncidenteCreate,
    db: Session = Depends(get_db),
):
    """
    Reporta un nuevo incidente de tráfico.

    Flujo:
    1. Recibe datos del incidente (tipo, descripción, coordenadas, usuario_id).
    2. Llama al ai-service para clasificar la severidad usando la descripción.
    3. Guarda el incidente en la base de datos con estado `pendiente`.
    """
    try:
        # Clasificar severidad usando el ai-service
        logger.info(
            "Clasificando severidad para incidente: tipo=%s, usuario_id=%s",
            incidente.tipo,
            incidente.usuario_id,
        )
        severidad = await clasificar_severidad(
            descripcion=incidente.descripcion,
            tipo_incidente=incidente.tipo,
        )

        # Crear el incidente con la severidad clasificada
        db_incidente = Incidente(
            tipo=incidente.tipo,
            descripcion=incidente.descripcion,
            latitud=incidente.latitud,
            longitud=incidente.longitud,
            severidad=severidad,
            estado=EstadoIncidenteEnum.PENDIENTE,
            usuario_id=incidente.usuario_id,
        )

        db.add(db_incidente)
        db.commit()
        db.refresh(db_incidente)

        logger.info("Incidente creado exitosamente con ID: %s", db_incidente.id)
        
        # Publicar evento en RabbitMQ después de guardar exitosamente
        try:
            producer = await get_producer()
            await producer.publish_event(
                event_type="reporte_creado",
                user_id=incidente.usuario_id,
                puntos_base=10,
                incidente_id=db_incidente.id,
                tipo_incidente=incidente.tipo,
                severidad=severidad.value if hasattr(severidad, 'value') else str(severidad),
            )
        except Exception as e:
            # No fallar la petición si RabbitMQ falla, solo loguear el error
            logger.error(
                "Error publicando evento a RabbitMQ (el incidente fue guardado): %s",
                str(e)
            )
        
        return db_incidente

    except HTTPException:
        # Re-lanzar HTTPExceptions directamente
        raise
    except Exception as e:
        db.rollback()
        logger.error("Error al reportar incidente: %s", str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al reportar el incidente: {str(e)}",
        )


@app.get(
    "/reportes",
    response_model=List[IncidenteResponse],
    summary="Listar incidentes activos",
    description=(
        "Obtiene una lista de todos los incidentes activos "
        "(estado pendiente, validado o verificado)."
    ),
)
async def listar_incidentes_activos(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
):
    """
    Lista todos los incidentes activos (pendiente, validado o verificado) con paginación.

    - **skip**: Número de registros a saltar (default: 0)
    - **limit**: Número máximo de registros a retornar (default: 100)
    """
    incidentes = (
        db.query(Incidente)
        .filter(Incidente.estado.in_(
            [
                EstadoIncidenteEnum.PENDIENTE,
                EstadoIncidenteEnum.VALIDADO,
                EstadoIncidenteEnum.VERIFICADO
            ]
        ))
        .offset(skip)
        .limit(limit)
        .all()
    )
    return incidentes


@app.get(
    "/reportes/cercanos",
    response_model=IncidenteGeoJSONCollection,
    summary="Obtener incidentes cercanos",
    description="Obtiene incidentes activos dentro de un radio específico en formato GeoJSON"
)
async def obtener_incidentes_cercanos(
    lat: float = Query(..., ge=-90, le=90, description="Latitud del punto central"),
    lng: float = Query(..., ge=-180, le=180, description="Longitud del punto central"),
    radio: float = Query(5.0, ge=0.1, le=100.0, description="Radio en kilómetros (default: 5, máximo: 100)"),
    db: Session = Depends(get_db)
):
    """
    Obtiene incidentes activos dentro de un radio específico desde una ubicación.
    
    Retorna los datos en formato GeoJSON para facilitar la integración con mapas.
    Utiliza la fórmula de Haversine para calcular distancias precisas.
    
    - **lat**: Latitud del punto central (requerido, rango: -90 a 90)
    - **lng**: Longitud del punto central (requerido, rango: -180 a 180)
    - **radio**: Radio en kilómetros (default: 5, máximo: 100)
    
    El formato GeoJSON permite que el frontend integre fácilmente los datos en mapas
    usando librerías como Leaflet, Mapbox, etc.
    
    Ejemplo de respuesta:
    ```json
    {
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
            "estado": "pendiente",
            "distancia_km": 2.5
          }
        }
      ]
    }
    ```
    """
    try:
        # Calcular bounding box para optimizar la consulta
        min_lat, max_lat, min_lon, max_lon = calculate_bounding_box(lat, lng, radio)
        
        # Primero filtrar por bounding box (optimización)
        # Solo incidentes activos dentro del rectángulo aproximado
        incidentes_candidatos = db.query(Incidente).filter(
            Incidente.estado.in_([
                EstadoIncidenteEnum.PENDIENTE,
                EstadoIncidenteEnum.VALIDADO,
                EstadoIncidenteEnum.VERIFICADO
            ]),
            Incidente.latitud >= min_lat,
            Incidente.latitud <= max_lat,
            Incidente.longitud >= min_lon,
            Incidente.longitud <= max_lon
        ).all()
        
        # Filtrar por distancia exacta usando Haversine
        features = []
        for incidente in incidentes_candidatos:
            distancia = haversine_distance(lat, lng, incidente.latitud, incidente.longitud)
            
            if distancia <= radio:
                # Crear feature GeoJSON
                feature = IncidenteGeoJSONFeature(
                    type="Feature",
                    geometry=PointGeometry(
                        type="Point",
                        coordinates=[incidente.longitud, incidente.latitud]  # GeoJSON usa [lon, lat]
                    ),
                    properties={
                        "id": incidente.id,
                        "tipo": incidente.tipo,
                        "descripcion": incidente.descripcion,
                        "severidad": incidente.severidad.value,
                        "estado": incidente.estado.value,
                        "usuario_id": incidente.usuario_id,
                        "validaciones_count": incidente.validaciones_count,
                        "distancia_km": round(distancia, 2),
                        "created_at": incidente.created_at.isoformat() if incidente.created_at else None,
                        "updated_at": incidente.updated_at.isoformat() if incidente.updated_at else None
                    }
                )
                features.append(feature)
        
        # Ordenar por distancia (más cercanos primero)
        features.sort(key=lambda f: f.properties["distancia_km"])
        
        logger.info(
            "Encontrados %d incidentes dentro de %.2fkm desde (%.6f, %.6f)",
            len(features), radio, lat, lng
        )
        
        return IncidenteGeoJSONCollection(
            type="FeatureCollection",
            features=features
        )
        
    except Exception as e:
        logger.error("Error al obtener incidentes cercanos: %s", str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener incidentes cercanos: {str(e)}"
        )


@app.post(
    "/reportes/{reporte_id}/validar",
    response_model=ValidacionResponse,
    status_code=status.HTTP_200_OK,
    summary="Validar un reporte de incidente",
    description=(
        "Permite a un usuario validar un reporte de incidente. "
        "Si el reporte llega a 3 validaciones, se marca como 'verificado' "
        "y se dispara un evento para otorgar XP al creador original."
    ),
)
async def validar_reporte(
    reporte_id: int,
    validacion: ValidacionRequest,
    db: Session = Depends(get_db),
):
    """
    Valida un reporte de incidente.
    
    Reglas de validación:
    - Un usuario no puede validar su propio reporte
    - Un usuario solo puede validar un reporte una vez
    - Cuando un reporte llega a 3 validaciones, se marca como 'verificado'
    - Al verificarse, se publica un evento en RabbitMQ para otorgar XP al creador
    
    Args:
        reporte_id: ID del reporte a validar
        validacion: Datos de la validación (usuario_id)
        db: Sesión de base de datos
        
    Returns:
        ValidacionResponse con el estado actualizado del reporte
    """
    try:
        # Buscar el incidente
        incidente = db.query(Incidente).filter(Incidente.id == reporte_id).first()
        
        if not incidente:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Reporte con ID {reporte_id} no encontrado"
            )
        
        # Verificar que el usuario no sea el creador del reporte
        if incidente.usuario_id == validacion.usuario_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No puedes validar tu propio reporte"
            )
        
        # Verificar que el usuario no haya validado antes
        validacion_existente = db.query(ValidacionIncidente).filter(
            ValidacionIncidente.incidente_id == reporte_id,
            ValidacionIncidente.usuario_id == validacion.usuario_id
        ).first()
        
        if validacion_existente:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Ya has validado este reporte anteriormente"
            )
        
        # Verificar que el reporte no esté ya verificado
        if incidente.estado == EstadoIncidenteEnum.VERIFICADO:
            return ValidacionResponse(
                incidente_id=incidente.id,
                usuario_id=validacion.usuario_id,
                validaciones_count=incidente.validaciones_count,
                estado=incidente.estado,
                verificado=True,
                mensaje=f"El reporte ya está verificado con {incidente.validaciones_count} validaciones"
            )
        
        # Crear la validación
        nueva_validacion = ValidacionIncidente(
            incidente_id=reporte_id,
            usuario_id=validacion.usuario_id
        )
        db.add(nueva_validacion)
        
        # Incrementar contador de validaciones
        incidente.validaciones_count += 1
        
        # Verificar si llegó a 3 validaciones
        verificado = False
        if incidente.validaciones_count >= 3:
            incidente.estado = EstadoIncidenteEnum.VERIFICADO
            verificado = True
            
            logger.info(
                "Reporte %d verificado con %d validaciones. Usuario creador: %d",
                reporte_id,
                incidente.validaciones_count,
                incidente.usuario_id
            )
            
            # Publicar evento en RabbitMQ para otorgar XP al creador
            try:
                producer = await get_producer()
                await producer.publish_event(
                    event_type="reporte_verificado",
                    user_id=incidente.usuario_id,  # Usuario creador del reporte
                    puntos_base=50,  # Bono de XP por verificación
                    incidente_id=incidente.id,
                    validaciones_count=incidente.validaciones_count,
                    tipo_incidente=incidente.tipo,
                    severidad=incidente.severidad.value if hasattr(incidente.severidad, 'value') else str(incidente.severidad),
                )
                logger.info(
                    "Evento 'reporte_verificado' publicado para usuario %d",
                    incidente.usuario_id
                )
            except Exception as e:
                # No fallar la petición si RabbitMQ falla, solo loguear el error
                logger.error(
                    "Error publicando evento de verificación a RabbitMQ: %s",
                    str(e)
                )
        
        db.commit()
        db.refresh(incidente)
        
        mensaje = (
            f"Reporte verificado con {incidente.validaciones_count} validaciones"
            if verificado
            else f"Validación registrada. Total: {incidente.validaciones_count}/3"
        )
        
        logger.info(
            "Validación registrada: reporte_id=%d, usuario_id=%d, validaciones=%d/%d",
            reporte_id,
            validacion.usuario_id,
            incidente.validaciones_count,
            3
        )
        
        return ValidacionResponse(
            incidente_id=incidente.id,
            usuario_id=validacion.usuario_id,
            validaciones_count=incidente.validaciones_count,
            estado=incidente.estado,
            verificado=verificado,
            mensaje=mensaje
        )
        
    except HTTPException:
        # Re-lanzar HTTPExceptions directamente
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        logger.error("Error al validar reporte: %s", str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al validar el reporte: {str(e)}"
        )


@app.on_event("shutdown")
async def shutdown_event():
    """Cerrar conexiones al apagar la aplicación"""
    logger.info("Cerrando conexiones...")
    await close_producer()
    logger.info("Conexiones cerradas correctamente")

