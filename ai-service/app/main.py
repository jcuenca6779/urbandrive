from fastapi import FastAPI, HTTPException, status
from datetime import datetime
import logging

from app.schemas import (
    ClasificacionSeveridadRequest,
    ClasificacionSeveridadResponse,
    ClasificacionIncidenteRequest,
    ClasificacionIncidenteResponse,
    DeteccionAnomaliaRequest,
    DeteccionAnomaliaResponse,
    TrainingRequest,
    TrainingResponse,
    TrainingExampleRequest,
    DeteccionFalsoPositivoRequest,
    DeteccionFalsoPositivoResponse
)
from app.classifier import IncidentClassifier, SeverityClassifier
from app.anomaly_detector import AnomalyDetector
from app.sentiment_analyzer import SentimentSeverityAnalyzer
from app.false_positive_detector import FalsePositiveDetector
from app.training_data import training_data_manager

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="UrbanDrive AI Service",
    description="Servicio de inteligencia artificial para clasificación de incidentes y detección de anomalías",
    version="1.0.0"
)

# Inicializar clasificadores y detector de anomalías
incident_classifier = IncidentClassifier()
severity_classifier = SeverityClassifier()
anomaly_detector = AnomalyDetector()

# Inicializar modelos mejorados de ML
sentiment_analyzer = SentimentSeverityAnalyzer()
false_positive_detector = FalsePositiveDetector()


@app.get("/health")
async def health_check():
    """Endpoint de salud del servicio"""
    return {"status": "ok", "service": "ai-service"}


@app.get("/info")
async def info():
    """Información del servicio"""
    return {
        "service": "ai-service",
        "description": "Servicio de inteligencia artificial de UrbanDrive",
        "capabilities": [
            "Clasificación de severidad de incidentes (análisis de sentimiento con TextBlob)",
            "Clasificación de tipo de incidente (NLP con scikit-learn)",
            "Detección de anomalías estadística",
            "Detección de falsos positivos (Random Forest)",
            "Re-entrenamiento de modelos con datos etiquetados"
        ],
        "endpoints": {
            "POST /clasificar-severidad": "Clasificar severidad usando análisis de sentimiento",
            "POST /clasificar-incidente": "Clasificar tipo de incidente usando NLP",
            "POST /detectar-anomalia": "Detectar anomalías estadísticas",
            "POST /detectar-falso-positivo": "Detectar falsos positivos usando Random Forest",
            "POST /train": "Re-entrenar modelos con ejemplos etiquetados",
            "GET /estadisticas/{ubicacion}": "Obtener estadísticas históricas"
        }
    }


@app.post(
    "/clasificar-severidad",
    response_model=ClasificacionSeveridadResponse,
    summary="Clasificar severidad de un incidente",
    description="Clasifica la severidad (baja, media, alta, critica) de un incidente basándose en tipo y descripción"
)
async def clasificar_severidad(request: ClasificacionSeveridadRequest):
    """
    Clasifica la severidad de un incidente de tráfico.
    
    Este endpoint es usado por el traffic-service para determinar la severidad
    antes de guardar un reporte en la base de datos.
    
    - **tipo_incidente**: Tipo de incidente reportado
    - **descripcion**: Descripción detallada del incidente
    """
    try:
        # Usar el analizador de sentimiento mejorado si está disponible
        try:
            severidad, confianza = sentiment_analyzer.analyze(
                descripcion=request.descripcion,
                tipo_incidente=request.tipo_incidente
            )
        except Exception as e:
            logger.warning(f"Error en analizador de sentimiento, usando clasificador básico: {str(e)}")
            # Fallback al clasificador básico
            severidad, confianza = severity_classifier.classify(
                tipo_incidente=request.tipo_incidente,
                descripcion=request.descripcion
            )
        
        logger.info(
            f"Severidad clasificada: {severidad} "
            f"(confianza: {confianza:.2f}) para tipo: {request.tipo_incidente}"
        )
        
        return ClasificacionSeveridadResponse(
            severidad=severidad,
            confianza=confianza
        )
        
    except Exception as e:
        logger.error(f"Error al clasificar severidad: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al clasificar severidad: {str(e)}"
        )


@app.post(
    "/clasificar-incidente",
    response_model=ClasificacionIncidenteResponse,
    summary="Clasificar tipo de incidente usando NLP",
    description="Clasifica el tipo de incidente (Accidente Grave, Tráfico Ligero, Peligro en Vía) usando NLP básico"
)
async def clasificar_incidente(request: ClasificacionIncidenteRequest):
    """
    Clasifica el tipo de incidente usando técnicas de NLP básico.
    
    Utiliza scikit-learn con TF-IDF y Naive Bayes para clasificar el incidente
    en una de las categorías: 'Accidente Grave', 'Tráfico Ligero', o 'Peligro en Vía'.
    
    - **descripcion**: Descripción del incidente a clasificar
    """
    try:
        tipo_incidente, confianza, palabras_clave = incident_classifier.classify(
            descripcion=request.descripcion
        )
        
        logger.info(
            f"Incidente clasificado: {tipo_incidente} "
            f"(confianza: {confianza:.2f}) - Palabras clave: {palabras_clave}"
        )
        
        return ClasificacionIncidenteResponse(
            tipo_incidente=tipo_incidente,
            confianza=confianza,
            palabras_clave=palabras_clave
        )
        
    except Exception as e:
        logger.error(f"Error al clasificar incidente: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al clasificar incidente: {str(e)}"
        )


@app.post(
    "/detectar-anomalia",
    response_model=DeteccionAnomaliaResponse,
    summary="Detectar anomalías estadísticas",
    description="Detecta si un reporte es estadísticamente inusual basándose en hora y ubicación históricas"
)
async def detectar_anomalia(request: DeteccionAnomaliaRequest):
    """
    Detecta si un reporte es una anomalía estadística.
    
    Analiza patrones históricos de reportes en la misma ubicación y hora
    para determinar si el reporte actual es inusual. Utiliza Redis para
    almacenar estadísticas históricas.
    
    - **ubicacion**: Ubicación del reporte
    - **hora**: Hora del reporte (datetime)
    - **tipo_incidente**: Tipo de incidente (opcional)
    """
    try:
        # Registrar el reporte para estadísticas futuras
        anomaly_detector.record_report(
            ubicacion=request.ubicacion,
            hora=request.hora,
            tipo_incidente=request.tipo_incidente
        )
        
        # Detectar anomalía
        es_anomalia, score, razon, estadisticas = anomaly_detector.detect_anomaly(
            ubicacion=request.ubicacion,
            hora=request.hora,
            tipo_incidente=request.tipo_incidente
        )
        
        logger.info(
            f"Anomalía detectada: {es_anomalia} "
            f"(score: {score:.2f}) en {request.ubicacion} a las {request.hora}"
        )
        
        return DeteccionAnomaliaResponse(
            es_anomalia=es_anomalia,
            score_anomalia=score,
            razon=razon,
            estadisticas=estadisticas
        )
        
    except Exception as e:
        logger.error(f"Error al detectar anomalía: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al detectar anomalía: {str(e)}"
        )


@app.get(
    "/estadisticas/{ubicacion}",
    summary="Obtener estadísticas de una ubicación",
    description="Obtiene estadísticas históricas de reportes para una ubicación específica"
)
async def obtener_estadisticas(ubicacion: str, hora: datetime = None):
    """
    Obtiene estadísticas históricas de reportes para una ubicación.
    
    - **ubicacion**: Ubicación a analizar
    - **hora**: Hora específica a analizar (opcional, usa hora actual si no se proporciona)
    """
    try:
        if hora is None:
            hora = datetime.now()
        
        estadisticas = anomaly_detector.get_statistics(
            ubicacion=ubicacion,
            hora=hora
        )
        
        return {
            "ubicacion": ubicacion,
            "hora_analizada": hora.isoformat(),
            "estadisticas": estadisticas
        }
        
    except Exception as e:
        logger.error(f"Error al obtener estadísticas: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener estadísticas: {str(e)}"
        )


@app.post(
    "/train",
    response_model=TrainingResponse,
    status_code=status.HTTP_200_OK,
    summary="Re-entrenar modelos de ML",
    description=(
        "Permite re-entrenar los modelos de análisis de sentimiento y detección de falsos positivos "
        "usando ejemplos marcados como validados o falsos por administradores."
    )
)
async def train_models(request: TrainingRequest):
    """
    Re-entrena los modelos de ML con nuevos ejemplos de entrenamiento.
    
    Este endpoint permite a administradores o usuarios autorizados mejorar los modelos
    proporcionando ejemplos correctamente etiquetados.
    
    - **model_type**: Tipo de modelo a entrenar ('sentiment', 'false_positive', o 'both')
    - **examples**: Lista de ejemplos de entrenamiento con sus etiquetas correctas
    
    Ejemplos de uso:
    - Para análisis de sentimiento: proporcionar descripciones con severidad_label
    - Para falsos positivos: proporcionar hora, latitud, longitud, tipo_incidente con is_false_positive
    """
    try:
        examples_added = 0
        sentiment_examples = []
        false_positive_examples = []
        
        # Guardar ejemplos en base de datos y preparar datos para entrenamiento
        for example_data in request.examples:
            try:
                # Guardar en base de datos
                training_data_manager.add_example(
                    descripcion=example_data.descripcion,
                    tipo_incidente=example_data.tipo_incidente,
                    hora=example_data.hora,
                    latitud=example_data.latitud,
                    longitud=example_data.longitud,
                    severidad_label=example_data.severidad_label,
                    is_false_positive=example_data.is_false_positive,
                    usuario_id=example_data.usuario_id,
                    incidente_id=example_data.incidente_id
                )
                examples_added += 1
                
                # Preparar para entrenamiento de sentimiento
                if example_data.descripcion and example_data.severidad_label:
                    sentiment_examples.append({
                        'text': example_data.descripcion,
                        'label': example_data.severidad_label
                    })
                
                # Preparar para entrenamiento de falsos positivos
                if (example_data.hora and example_data.latitud and 
                    example_data.longitud and example_data.tipo_incidente is not None and
                    example_data.is_false_positive is not None):
                    
                    # Extraer características
                    hora_dt = example_data.hora
                    hour = hora_dt.hour
                    day_of_week = hora_dt.weekday()
                    is_weekend = 1 if day_of_week >= 5 else 0
                    is_rush_hour = 1 if (7 <= hour <= 9) or (17 <= hour <= 19) else 0
                    is_unusual_hour = 1 if hour < 5 or hour > 23 else 0
                    
                    false_positive_examples.append({
                        'hora': hora_dt,
                        'hour': hour,
                        'day_of_week': day_of_week,
                        'is_weekend': is_weekend,
                        'is_rush_hour': is_rush_hour,
                        'is_unusual_hour': is_unusual_hour,
                        'lat': example_data.latitud,
                        'lon': example_data.longitud,
                        'tipo_incidente': example_data.tipo_incidente
                    })
                    
            except Exception as e:
                logger.error(f"Error al procesar ejemplo: {str(e)}")
                continue
        
        # Re-entrenar modelos según el tipo solicitado
        models_trained = []
        
        if request.model_type in ["sentiment", "both"] and sentiment_examples:
            try:
                texts = [ex['text'] for ex in sentiment_examples]
                labels = [ex['label'] for ex in sentiment_examples]
                sentiment_analyzer.retrain(texts, labels)
                models_trained.append("sentiment")
                logger.info(f"Modelo de sentimiento re-entrenado con {len(texts)} ejemplos")
            except Exception as e:
                logger.error(f"Error al re-entrenar modelo de sentimiento: {str(e)}")
        
        if request.model_type in ["false_positive", "both"] and false_positive_examples:
            try:
                data = false_positive_examples
                labels = [1 if ex.get('is_false_positive', False) else 0 for ex in false_positive_examples]
                
                # Convertir a formato esperado por el detector
                training_data = []
                training_labels = []
                for ex in false_positive_examples:
                    # Buscar el is_false_positive del ejemplo original
                    original_example = next(
                        (e for e in request.examples if 
                         e.hora == ex['hora'] and e.latitud == ex['lat'] and e.longitud == ex['lon']),
                        None
                    )
                    if original_example and original_example.is_false_positive is not None:
                        training_data.append({
                            'hour': ex['hour'],
                            'day_of_week': ex['day_of_week'],
                            'is_weekend': ex['is_weekend'],
                            'is_rush_hour': ex['is_rush_hour'],
                            'is_unusual_hour': ex['is_unusual_hour'],
                            'lat': ex['lat'],
                            'lon': ex['lon'],
                            'tipo_incidente': ex['tipo_incidente']
                        })
                        training_labels.append(1 if original_example.is_false_positive else 0)
                
                if training_data:
                    false_positive_detector.retrain(training_data, training_labels)
                    models_trained.append("false_positive")
                    logger.info(f"Modelo de falsos positivos re-entrenado con {len(training_data)} ejemplos")
            except Exception as e:
                logger.error(f"Error al re-entrenar modelo de falsos positivos: {str(e)}")
        
        if not models_trained:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No se pudo entrenar ningún modelo. Verifique que los ejemplos tengan los campos necesarios."
            )
        
        model_type_str = ", ".join(models_trained) if len(models_trained) > 1 else models_trained[0]
        
        return TrainingResponse(
            success=True,
            model_type=model_type_str,
            examples_used=examples_added,
            message=f"Modelos ({model_type_str}) re-entrenados exitosamente con {examples_added} ejemplos nuevos"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error al entrenar modelos: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al entrenar modelos: {str(e)}"
        )


@app.post(
    "/detectar-falso-positivo",
    response_model=DeteccionFalsoPositivoResponse,
    summary="Detectar si un reporte es falso positivo",
    description="Usa Random Forest para determinar la probabilidad de que un reporte sea un falso positivo"
)
async def detectar_falso_positivo(request: DeteccionFalsoPositivoRequest):
    """
    Detecta si un reporte es probablemente un falso positivo usando Random Forest.
    
    Analiza características espaciotemporales (hora, ubicación, tipo) para determinar
    la probabilidad de que el reporte sea un falso positivo.
    
    - **hora**: Hora del reporte
    - **latitud**: Latitud del reporte
    - **longitud**: Longitud del reporte
    - **tipo_incidente**: Tipo de incidente reportado
    """
    try:
        is_false_positive, probability = false_positive_detector.predict(
            hora=request.hora,
            latitud=request.latitud,
            longitud=request.longitud,
            tipo_incidente=request.tipo_incidente
        )
        
        logger.info(
            f"Falso positivo detectado: {is_false_positive} "
            f"(probabilidad: {probability:.2f}) para tipo: {request.tipo_incidente}"
        )
        
        return DeteccionFalsoPositivoResponse(
            es_falso_positivo=is_false_positive,
            probabilidad=probability,
            hora=request.hora.isoformat(),
            latitud=request.latitud,
            longitud=request.longitud,
            tipo_incidente=request.tipo_incidente
        )
        
    except Exception as e:
        logger.error(f"Error al detectar falso positivo: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al detectar falso positivo: {str(e)}"
        )

