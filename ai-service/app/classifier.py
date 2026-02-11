"""
Clasificador de incidentes usando NLP básico con scikit-learn
"""
import re
from typing import Literal
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import Pipeline
import logging

logger = logging.getLogger(__name__)


class IncidentClassifier:
    """Clasificador de tipos de incidentes usando NLP"""
    
    # Palabras clave para cada tipo de incidente
    KEYWORDS = {
        "Accidente Grave": [
            "choque", "colisión", "accidente", "impacto", "golpe", "chocó", "chocaron",
            "heridos", "lesionados", "ambulancia", "emergencia", "grave", "serio",
            "vehículo", "auto", "carro", "moto", "camión", "volcado", "incendio"
        ],
        "Tráfico Ligero": [
            "lento", "congestionado", "tráfico", "embotellamiento", "colas", "espera",
            "denso", "muchos vehículos", "circulación lenta", "retención", "atascado"
        ],
        "Peligro en Vía": [
            "obstáculo", "objeto", "bache", "hueco", "derrumbe", "deslizamiento",
            "semáforo", "dañado", "roto", "falta", "peligro", "riesgo", "precaución",
            "animal", "persona", "peatón", "trabajos", "construcción", "zona peligrosa"
        ]
    }
    
    def __init__(self):
        """Inicializa el clasificador con datos de entrenamiento básicos"""
        self.vectorizer = None
        self.classifier = None
        self._train_classifier()
    
    def _preprocess_text(self, text: str) -> str:
        """Preprocesa el texto para mejor clasificación"""
        # Convertir a minúsculas
        text = text.lower()
        # Remover caracteres especiales excepto espacios
        text = re.sub(r'[^a-záéíóúñü\s]', ' ', text)
        # Remover espacios múltiples
        text = re.sub(r'\s+', ' ', text).strip()
        return text
    
    def _create_training_data(self):
        """Crea datos de entrenamiento basados en palabras clave"""
        training_texts = []
        training_labels = []
        
        # Generar ejemplos de entrenamiento para cada categoría
        for tipo, keywords in self.KEYWORDS.items():
            # Crear múltiples combinaciones de palabras clave
            for keyword in keywords:
                # Ejemplos simples
                training_texts.append(f"{keyword}")
                training_labels.append(tipo)
                
                # Ejemplos con contexto
                training_texts.append(f"hay {keyword} en la vía")
                training_labels.append(tipo)
                
                training_texts.append(f"se reporta {keyword} en la zona")
                training_labels.append(tipo)
        
        # Agregar ejemplos negativos/combinados
        training_texts.extend([
            "choque frontal entre dos autos",
            "tráfico muy lento en la avenida",
            "bache grande en el camino",
            "accidente con heridos graves",
            "mucho tráfico y espera",
            "obstáculo peligroso en la carretera"
        ])
        training_labels.extend([
            "Accidente Grave",
            "Tráfico Ligero",
            "Peligro en Vía",
            "Accidente Grave",
            "Tráfico Ligero",
            "Peligro en Vía"
        ])
        
        return training_texts, training_labels
    
    def _train_classifier(self):
        """Entrena el clasificador con datos básicos"""
        try:
            training_texts, training_labels = self._create_training_data()
            
            # Preprocesar textos
            processed_texts = [self._preprocess_text(text) for text in training_texts]
            
            # Crear pipeline con TF-IDF y Naive Bayes
            self.classifier = Pipeline([
                ('tfidf', TfidfVectorizer(max_features=100, ngram_range=(1, 2))),
                ('clf', MultinomialNB(alpha=1.0))
            ])
            
            # Entrenar
            self.classifier.fit(processed_texts, training_labels)
            logger.info("Clasificador de incidentes entrenado exitosamente")
            
        except Exception as e:
            logger.error(f"Error al entrenar clasificador: {str(e)}")
            self.classifier = None
    
    def classify(self, descripcion: str) -> tuple[Literal["Accidente Grave", "Tráfico Ligero", "Peligro en Vía"], float, list[str]]:
        """
        Clasifica un incidente basándose en su descripción
        
        Args:
            descripcion: Descripción del incidente
            
        Returns:
            Tupla con (tipo_incidente, confianza, palabras_clave_detectadas)
        """
        if not self.classifier:
            # Fallback a clasificación por palabras clave
            return self._keyword_based_classify(descripcion)
        
        try:
            # Preprocesar texto
            processed_text = self._preprocess_text(descripcion)
            
            # Clasificar con el modelo
            prediction = self.classifier.predict([processed_text])[0]
            
            # Obtener probabilidades
            probabilities = self.classifier.predict_proba([processed_text])[0]
            class_index = list(self.classifier.classes_).index(prediction)
            confidence = float(probabilities[class_index])
            
            # Detectar palabras clave encontradas
            detected_keywords = self._detect_keywords(descripcion)
            
            return prediction, confidence, detected_keywords
            
        except Exception as e:
            logger.error(f"Error en clasificación: {str(e)}")
            return self._keyword_based_classify(descripcion)
    
    def _keyword_based_classify(self, descripcion: str) -> tuple[Literal["Accidente Grave", "Tráfico Ligero", "Peligro en Vía"], float, list[str]]:
        """Clasificación basada en palabras clave como fallback"""
        desc_lower = descripcion.lower()
        scores = {}
        detected_keywords = []
        
        for tipo, keywords in self.KEYWORDS.items():
            score = 0
            found_keywords = []
            for keyword in keywords:
                if keyword.lower() in desc_lower:
                    score += 1
                    found_keywords.append(keyword)
            scores[tipo] = score
            if found_keywords:
                detected_keywords.extend(found_keywords)
        
        # Determinar el tipo con mayor score
        if not scores or max(scores.values()) == 0:
            # Si no hay coincidencias, usar "Peligro en Vía" como default
            return "Peligro en Vía", 0.5, []
        
        best_type = max(scores, key=scores.get)
        total_matches = sum(scores.values())
        confidence = min(scores[best_type] / max(total_matches, 1), 1.0)
        
        return best_type, confidence, detected_keywords
    
    def _detect_keywords(self, descripcion: str) -> list[str]:
        """Detecta palabras clave en la descripción"""
        desc_lower = descripcion.lower()
        detected = []
        
        for tipo, keywords in self.KEYWORDS.items():
            for keyword in keywords:
                if keyword.lower() in desc_lower and keyword not in detected:
                    detected.append(keyword)
        
        return detected


class SeverityClassifier:
    """Clasificador de severidad basado en tipo de incidente y descripción"""
    
    def classify(self, tipo_incidente: str, descripcion: str) -> tuple[Literal["baja", "media", "alta", "critica"], float]:
        """
        Clasifica la severidad basándose en el tipo de incidente y descripción
        
        Args:
            tipo_incidente: Tipo de incidente
            descripcion: Descripción del incidente
            
        Returns:
            Tupla con (severidad, confianza)
        """
        desc_lower = descripcion.lower()
        tipo_lower = tipo_incidente.lower()
        
        # Palabras clave de alta severidad
        high_severity_keywords = [
            "grave", "crítico", "heridos", "lesionados", "muerto", "fallecido",
            "ambulancia", "hospital", "emergencia", "urgente", "sangre", "incendio"
        ]
        
        # Palabras clave de severidad crítica
        critical_keywords = [
            "muerto", "fallecido", "múltiples heridos", "incendio", "explosión"
        ]
        
        # Verificar severidad crítica
        if any(keyword in desc_lower for keyword in critical_keywords):
            return "critica", 0.95
        
        # Verificar alta severidad
        if any(keyword in desc_lower for keyword in high_severity_keywords):
            return "alta", 0.85
        
        # Clasificar según tipo de incidente
        if "accidente grave" in tipo_lower or "accidente" in tipo_lower:
            return "alta", 0.75
        elif "peligro" in tipo_lower:
            return "media", 0.65
        elif "tráfico ligero" in tipo_lower or "tráfico" in tipo_lower:
            return "baja", 0.70
        
        # Default
        return "media", 0.60
