"""
Análisis de sentimiento y severidad usando TextBlob y scikit-learn
"""
import re
import logging
from typing import Tuple, Literal
import numpy as np
from textblob import TextBlob
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
import joblib
import os

logger = logging.getLogger(__name__)


class SentimentSeverityAnalyzer:
    """
    Analizador de sentimiento y severidad usando TextBlob y Regresión Logística.
    
    Combina análisis de sentimiento con características de texto para determinar
    la severidad de un incidente.
    """
    
    SEVERITY_LABELS = ["baja", "media", "alta", "critica"]
    
    def __init__(self, model_path: str = "models/sentiment_severity_model.pkl"):
        """Inicializa el analizador de sentimiento"""
        self.model_path = model_path
        self.model = None
        self.vectorizer = None
        self._initialize_model()
    
    def _initialize_model(self):
        """Inicializa o carga el modelo de severidad"""
        try:
            # Crear directorio si no existe
            os.makedirs(os.path.dirname(self.model_path), exist_ok=True)
            
            if os.path.exists(self.model_path):
                # Cargar modelo existente
                self.model = joblib.load(self.model_path)
                logger.info(f"Modelo de sentimiento cargado desde {self.model_path}")
            else:
                # Crear modelo inicial con datos de entrenamiento básicos
                self._train_initial_model()
                logger.info("Modelo inicial de sentimiento creado")
        except Exception as e:
            logger.error(f"Error al inicializar modelo de sentimiento: {str(e)}")
            self.model = None
    
    def _preprocess_text(self, text: str) -> str:
        """Preprocesa el texto para análisis"""
        # Convertir a minúsculas
        text = text.lower()
        # Remover caracteres especiales excepto espacios y acentos
        text = re.sub(r'[^a-záéíóúñü\s]', ' ', text)
        # Remover espacios múltiples
        text = re.sub(r'\s+', ' ', text).strip()
        return text
    
    def _extract_sentiment_features(self, text: str) -> dict:
        """
        Extrae características de sentimiento usando TextBlob
        
        Returns:
            Diccionario con características de sentimiento
        """
        blob = TextBlob(text)
        
        # Análisis de polaridad (-1 a 1, negativo a positivo)
        polarity = blob.sentiment.polarity
        
        # Análisis de subjetividad (0 a 1, objetivo a subjetivo)
        subjectivity = blob.sentiment.subjectivity
        
        # Contar palabras de emergencia/urgencia
        emergency_words = [
            "urgente", "emergencia", "grave", "crítico", "herido", "lesionado",
            "muerto", "fallecido", "sangre", "incendio", "explosión", "peligro",
            "riesgo", "inmediato", "rápido", "ahora"
        ]
        emergency_count = sum(1 for word in emergency_words if word in text.lower())
        
        # Contar palabras negativas intensas
        negative_intense = [
            "terrible", "horrible", "devastador", "catastrófico", "grave",
            "crítico", "mortal", "letal"
        ]
        negative_intense_count = sum(1 for word in negative_intense if word in text.lower())
        
        # Longitud del texto (textos más largos pueden indicar más detalle/severidad)
        text_length = len(text.split())
        
        return {
            "polarity": polarity,
            "subjectivity": subjectivity,
            "emergency_words": emergency_count,
            "negative_intense": negative_intense_count,
            "text_length": text_length
        }
    
    def _create_training_data(self):
        """Crea datos de entrenamiento iniciales basados en patrones conocidos"""
        training_texts = []
        training_labels = []
        
        # Ejemplos de severidad BAJA
        baja_examples = [
            "tráfico lento en la avenida",
            "ligera congestión vehicular",
            "muchos autos circulando",
            "espera moderada en el semáforo",
            "circulación un poco lenta",
            "tráfico normal con retraso mínimo"
        ]
        training_texts.extend(baja_examples)
        training_labels.extend(["baja"] * len(baja_examples))
        
        # Ejemplos de severidad MEDIA
        media_examples = [
            "bache en la carretera",
            "semáforo dañado",
            "obstáculo en la vía",
            "tráfico congestionado",
            "retención vehicular",
            "objeto en el camino",
            "zona de construcción"
        ]
        training_texts.extend(media_examples)
        training_labels.extend(["media"] * len(media_examples))
        
        # Ejemplos de severidad ALTA
        alta_examples = [
            "choque entre dos vehículos",
            "accidente con heridos",
            "colisión frontal",
            "vehículo volcado",
            "emergencia médica",
            "accidente grave en la intersección",
            "múltiples vehículos involucrados"
        ]
        training_texts.extend(alta_examples)
        training_labels.extend(["alta"] * len(alta_examples))
        
        # Ejemplos de severidad CRÍTICA
        critica_examples = [
            "accidente con muertos",
            "múltiples heridos graves",
            "incendio en vehículo",
            "explosión en la carretera",
            "accidente fatal",
            "personas fallecidas",
            "emergencia crítica con ambulancias"
        ]
        training_texts.extend(critica_examples)
        training_labels.extend(["critica"] * len(critica_examples))
        
        return training_texts, training_labels
    
    def _train_initial_model(self):
        """Entrena el modelo inicial con datos básicos"""
        try:
            training_texts, training_labels = self._create_training_data()
            
            # Preprocesar textos
            processed_texts = [self._preprocess_text(text) for text in training_texts]
            
            # Crear pipeline con TF-IDF y Regresión Logística
            self.model = Pipeline([
                ('tfidf', TfidfVectorizer(max_features=500, ngram_range=(1, 2))),
                ('clf', LogisticRegression(max_iter=1000, random_state=42))
            ])
            
            # Entrenar
            self.model.fit(processed_texts, training_labels)
            
            # Guardar modelo
            self._save_model()
            
            logger.info("Modelo inicial de sentimiento entrenado exitosamente")
        except Exception as e:
            logger.error(f"Error al entrenar modelo inicial: {str(e)}")
            self.model = None
    
    def _save_model(self):
        """Guarda el modelo en disco"""
        try:
            if self.model:
                joblib.dump(self.model, self.model_path)
                logger.info(f"Modelo guardado en {self.model_path}")
        except Exception as e:
            logger.error(f"Error al guardar modelo: {str(e)}")
    
    def analyze(self, descripcion: str, tipo_incidente: str = None) -> Tuple[Literal["baja", "media", "alta", "critica"], float]:
        """
        Analiza el sentimiento y determina la severidad de un incidente
        
        Args:
            descripcion: Descripción del incidente
            tipo_incidente: Tipo de incidente (opcional, para contexto adicional)
            
        Returns:
            Tupla con (severidad, confianza)
        """
        try:
            # Extraer características de sentimiento
            sentiment_features = self._extract_sentiment_features(descripcion)
            
            # Preprocesar texto
            processed_text = self._preprocess_text(descripcion)
            
            # Si hay modelo entrenado, usarlo
            if self.model:
                # Predecir con el modelo
                prediction = self.model.predict([processed_text])[0]
                probabilities = self.model.predict_proba([processed_text])[0]
                class_index = list(self.model.classes_).index(prediction)
                confidence = float(probabilities[class_index])
                
                # Ajustar confianza basado en características de sentimiento
                # Si hay palabras de emergencia, aumentar confianza hacia severidad alta
                if sentiment_features["emergency_words"] > 2:
                    if prediction in ["alta", "critica"]:
                        confidence = min(1.0, confidence + 0.1)
                    elif prediction == "media":
                        # Re-evaluar hacia alta
                        if "alta" in self.model.classes_:
                            alta_idx = list(self.model.classes_).index("alta")
                            alta_prob = probabilities[alta_idx]
                            if alta_prob > 0.3:
                                prediction = "alta"
                                confidence = alta_prob + 0.1
                
                # Verificar palabras críticas que siempre indican severidad crítica
                if sentiment_features["negative_intense"] > 0:
                    critica_keywords = ["muerto", "fallecido", "múltiples heridos", "incendio", "explosión"]
                    if any(keyword in descripcion.lower() for keyword in critica_keywords):
                        return "critica", 0.95
                
                return prediction, min(confidence, 0.95)
            else:
                # Fallback a análisis basado en características
                return self._fallback_classify(sentiment_features, descripcion)
                
        except Exception as e:
            logger.error(f"Error en análisis de sentimiento: {str(e)}")
            return self._fallback_classify(sentiment_features, descripcion)
    
    def _fallback_classify(self, sentiment_features: dict, descripcion: str) -> Tuple[Literal["baja", "media", "alta", "critica"], float]:
        """Clasificación de fallback basada en características de sentimiento"""
        # Palabras críticas siempre indican severidad crítica
        critica_keywords = ["muerto", "fallecido", "múltiples heridos", "incendio", "explosión"]
        if any(keyword in descripcion.lower() for keyword in critica_keywords):
            return "critica", 0.95
        
        # Alta severidad basada en características
        if sentiment_features["emergency_words"] >= 3 or sentiment_features["negative_intense"] > 0:
            return "alta", 0.85
        
        # Media severidad
        if sentiment_features["emergency_words"] >= 1 or sentiment_features["polarity"] < -0.3:
            return "media", 0.70
        
        # Baja severidad por defecto
        return "baja", 0.60
    
    def retrain(self, texts: list[str], labels: list[str]):
        """
        Re-entrena el modelo con nuevos datos
        
        Args:
            texts: Lista de textos de entrenamiento
            labels: Lista de etiquetas correspondientes (baja, media, alta, critica)
        """
        try:
            if not self.model:
                self._train_initial_model()
            
            # Preprocesar textos
            processed_texts = [self._preprocess_text(text) for text in texts]
            
            # Re-entrenar el modelo con los nuevos datos
            # Combinar con datos existentes si es posible
            self.model.fit(processed_texts, labels)
            
            # Guardar modelo actualizado
            self._save_model()
            
            logger.info(f"Modelo re-entrenado con {len(texts)} ejemplos nuevos")
        except Exception as e:
            logger.error(f"Error al re-entrenar modelo: {str(e)}")
            raise
