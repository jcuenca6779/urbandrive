"""
Detección de falsos positivos usando Random Forest
"""
import logging
import numpy as np
import pandas as pd
from datetime import datetime
from typing import Tuple, Optional
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report
import joblib
import os

logger = logging.getLogger(__name__)


class FalsePositiveDetector:
    """
    Detector de falsos positivos usando Random Forest.
    
    Analiza características espaciotemporales (hora, latitud, longitud, tipo_incidente)
    para determinar la probabilidad de que un reporte sea un falso positivo.
    """
    
    def __init__(self, model_path: str = "models/false_positive_model.pkl"):
        """Inicializa el detector de falsos positivos"""
        self.model_path = model_path
        self.model = None
        self.scaler = None
        self.label_encoder = None
        self._initialize_model()
    
    def _initialize_model(self):
        """Inicializa o carga el modelo"""
        try:
            # Crear directorio si no existe
            os.makedirs(os.path.dirname(self.model_path), exist_ok=True)
            
            if os.path.exists(self.model_path):
                # Cargar modelo existente
                loaded = joblib.load(self.model_path)
                self.model = loaded['model']
                self.scaler = loaded['scaler']
                self.label_encoder = loaded['label_encoder']
                logger.info(f"Modelo de falsos positivos cargado desde {self.model_path}")
            else:
                # Crear modelo inicial con datos sintéticos
                self._train_initial_model()
                logger.info("Modelo inicial de falsos positivos creado")
        except Exception as e:
            logger.error(f"Error al inicializar modelo de falsos positivos: {str(e)}")
            self.model = None
            self.scaler = None
            self.label_encoder = None
    
    def _extract_features(self, hora: datetime, latitud: float, longitud: float, tipo_incidente: str) -> np.ndarray:
        """
        Extrae características del reporte para el modelo
        
        Args:
            hora: Hora del reporte
            latitud: Latitud del reporte
            longitud: Longitud del reporte
            tipo_incidente: Tipo de incidente
            
        Returns:
            Array numpy con características extraídas
        """
        # Hora del día (0-23)
        hour_of_day = hora.hour
        
        # Día de la semana (0=Lunes, 6=Domingo)
        day_of_week = hora.weekday()
        
        # Es fin de semana (0 o 1)
        is_weekend = 1 if day_of_week >= 5 else 0
        
        # Hora pico (mañana 7-9, tarde 17-19)
        is_rush_hour = 1 if (7 <= hour_of_day <= 9) or (17 <= hour_of_day <= 19) else 0
        
        # Hora inusual (muy temprano o muy tarde)
        is_unusual_hour = 1 if hour_of_day < 5 or hour_of_day > 23 else 0
        
        # Codificar tipo de incidente
        tipo_encoded = self.label_encoder.transform([tipo_incidente])[0] if self.label_encoder else 0
        
        # Normalizar coordenadas (asumiendo rango aproximado de Lima, Perú)
        # Ajustar según la región geográfica real
        lat_normalized = (latitud + 12.5) / 0.5  # Normalizar alrededor de -12.0
        lon_normalized = (longitud + 77.0) / 0.5  # Normalizar alrededor de -77.0
        
        features = np.array([
            hour_of_day,
            day_of_week,
            is_weekend,
            is_rush_hour,
            is_unusual_hour,
            lat_normalized,
            lon_normalized,
            tipo_encoded
        ])
        
        return features.reshape(1, -1)
    
    def _create_synthetic_training_data(self):
        """Crea datos de entrenamiento sintéticos iniciales"""
        np.random.seed(42)
        
        data = []
        labels = []
        
        tipos_incidentes = ["choque", "bache", "tráfico", "accidente", "obstáculo"]
        
        # Generar ejemplos de reportes válidos (label=0)
        for _ in range(200):
            hour = np.random.randint(6, 22)  # Horas normales
            day = np.random.randint(0, 5)  # Días laborables
            lat = -12.0 + np.random.uniform(-0.3, 0.3)
            lon = -77.0 + np.random.uniform(-0.3, 0.3)
            tipo = np.random.choice(tipos_incidentes)
            
            data.append({
                'hour': hour,
                'day_of_week': day,
                'is_weekend': 0,
                'is_rush_hour': 1 if (7 <= hour <= 9) or (17 <= hour <= 19) else 0,
                'is_unusual_hour': 0,
                'lat': lat,
                'lon': lon,
                'tipo': tipo
            })
            labels.append(0)  # Válido
        
        # Generar ejemplos de falsos positivos (label=1)
        for _ in range(100):
            # Falsos positivos tienden a ser en horas inusuales o ubicaciones raras
            hour = np.random.choice([np.random.randint(0, 5), np.random.randint(22, 24)])
            day = np.random.randint(0, 7)
            lat = -12.0 + np.random.uniform(-1.0, 1.0)  # Ubicaciones más dispersas
            lon = -77.0 + np.random.uniform(-1.0, 1.0)
            tipo = np.random.choice(tipos_incidentes)
            
            data.append({
                'hour': hour,
                'day_of_week': day,
                'is_weekend': 1 if day >= 5 else 0,
                'is_rush_hour': 0,
                'is_unusual_hour': 1,
                'lat': lat,
                'lon': lon,
                'tipo': tipo
            })
            labels.append(1)  # Falso positivo
        
        return pd.DataFrame(data), np.array(labels)
    
    def _train_initial_model(self):
        """Entrena el modelo inicial con datos sintéticos"""
        try:
            # Crear datos de entrenamiento
            df, labels = self._create_synthetic_training_data()
            
            # Codificar tipo de incidente
            self.label_encoder = LabelEncoder()
            df['tipo_encoded'] = self.label_encoder.fit_transform(df['tipo'])
            
            # Preparar características
            feature_cols = ['hour', 'day_of_week', 'is_weekend', 'is_rush_hour', 
                           'is_unusual_hour', 'lat', 'lon', 'tipo_encoded']
            X = df[feature_cols].values
            
            # Normalizar características
            self.scaler = StandardScaler()
            X_scaled = self.scaler.fit_transform(X)
            
            # Entrenar modelo Random Forest
            self.model = RandomForestClassifier(
                n_estimators=100,
                max_depth=10,
                random_state=42,
                n_jobs=-1
            )
            self.model.fit(X_scaled, labels)
            
            # Guardar modelo
            self._save_model()
            
            logger.info("Modelo inicial de falsos positivos entrenado exitosamente")
        except Exception as e:
            logger.error(f"Error al entrenar modelo inicial: {str(e)}")
            self.model = None
    
    def _save_model(self):
        """Guarda el modelo en disco"""
        try:
            if self.model and self.scaler and self.label_encoder:
                model_data = {
                    'model': self.model,
                    'scaler': self.scaler,
                    'label_encoder': self.label_encoder
                }
                joblib.dump(model_data, self.model_path)
                logger.info(f"Modelo guardado en {self.model_path}")
        except Exception as e:
            logger.error(f"Error al guardar modelo: {str(e)}")
    
    def predict(self, hora: datetime, latitud: float, longitud: float, tipo_incidente: str) -> Tuple[bool, float]:
        """
        Predice si un reporte es un falso positivo
        
        Args:
            hora: Hora del reporte
            latitud: Latitud del reporte
            longitud: Longitud del reporte
            tipo_incidente: Tipo de incidente
            
        Returns:
            Tupla con (es_falso_positivo, probabilidad)
        """
        try:
            if not self.model or not self.scaler or not self.label_encoder:
                # Fallback: usar heurística simple
                return self._fallback_predict(hora, latitud, longitud, tipo_incidente)
            
            # Extraer características
            features = self._extract_features(hora, latitud, longitud, tipo_incidente)
            
            # Normalizar
            features_scaled = self.scaler.transform(features)
            
            # Predecir
            prediction = self.model.predict(features_scaled)[0]
            probabilities = self.model.predict_proba(features_scaled)[0]
            
            is_false_positive = bool(prediction == 1)
            probability = float(probabilities[1])  # Probabilidad de ser falso positivo
            
            return is_false_positive, probability
            
        except Exception as e:
            logger.error(f"Error al predecir falso positivo: {str(e)}")
            return self._fallback_predict(hora, latitud, longitud, tipo_incidente)
    
    def _fallback_predict(self, hora: datetime, latitud: float, longitud: float, tipo_incidente: str) -> Tuple[bool, float]:
        """Predicción de fallback usando heurísticas simples"""
        hour = hora.hour
        
        # Horas muy inusuales aumentan probabilidad de falso positivo
        if hour < 5 or hour > 23:
            return True, 0.6
        
        # Ubicaciones muy alejadas del centro pueden ser falsos positivos
        # (ajustar según región geográfica real)
        if abs(latitud + 12.0) > 0.5 or abs(longitud + 77.0) > 0.5:
            return True, 0.5
        
        return False, 0.3
    
    def retrain(self, data: list[dict], labels: list[int]):
        """
        Re-entrena el modelo con nuevos datos
        
        Args:
            data: Lista de diccionarios con características (hora, latitud, longitud, tipo_incidente)
            labels: Lista de etiquetas (0=válido, 1=falso positivo)
        """
        try:
            if not self.model:
                self._train_initial_model()
            
            # Convertir a DataFrame
            df = pd.DataFrame(data)
            
            # Asegurar que el label_encoder tenga todos los tipos
            if 'tipo_incidente' in df.columns:
                all_tipos = df['tipo_incidente'].unique().tolist()
                if self.label_encoder:
                    existing_classes = list(self.label_encoder.classes_)
                    new_classes = [t for t in all_tipos if t not in existing_classes]
                    if new_classes:
                        # Extender el encoder
                        self.label_encoder.classes_ = np.concatenate([self.label_encoder.classes_, new_classes])
                else:
                    self.label_encoder = LabelEncoder()
                    self.label_encoder.fit(all_tipos)
                
                df['tipo_encoded'] = self.label_encoder.transform(df['tipo_incidente'])
            
            # Extraer características
            feature_cols = ['hour', 'day_of_week', 'is_weekend', 'is_rush_hour', 
                           'is_unusual_hour', 'lat', 'lon', 'tipo_encoded']
            
            # Asegurar que todas las columnas existan
            for col in feature_cols:
                if col not in df.columns:
                    # Calcular desde datos disponibles
                    if col == 'hour':
                        df['hour'] = pd.to_datetime(df['hora']).dt.hour
                    elif col == 'day_of_week':
                        df['day_of_week'] = pd.to_datetime(df['hora']).dt.weekday
                    elif col == 'is_weekend':
                        df['is_weekend'] = (pd.to_datetime(df['hora']).dt.weekday >= 5).astype(int)
                    elif col == 'is_rush_hour':
                        df['is_rush_hour'] = ((df['hour'] >= 7) & (df['hour'] <= 9) | 
                                             ((df['hour'] >= 17) & (df['hour'] <= 19))).astype(int)
                    elif col == 'is_unusual_hour':
                        df['is_unusual_hour'] = ((df['hour'] < 5) | (df['hour'] > 23)).astype(int)
            
            X = df[feature_cols].values
            y = np.array(labels)
            
            # Normalizar
            if self.scaler:
                X_scaled = self.scaler.fit_transform(X)  # Re-fit scaler con nuevos datos
            else:
                self.scaler = StandardScaler()
                X_scaled = self.scaler.fit_transform(X)
            
            # Re-entrenar modelo
            self.model.fit(X_scaled, y)
            
            # Guardar modelo actualizado
            self._save_model()
            
            logger.info(f"Modelo re-entrenado con {len(data)} ejemplos nuevos")
        except Exception as e:
            logger.error(f"Error al re-entrenar modelo: {str(e)}")
            raise
