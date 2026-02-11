"""
Utilidades geoespaciales para calcular distancias entre coordenadas
"""
import math
from typing import Tuple


def haversine_distance(
    lat1: float,
    lon1: float,
    lat2: float,
    lon2: float
) -> float:
    """
    Calcula la distancia entre dos puntos geográficos usando la fórmula de Haversine.
    
    Args:
        lat1: Latitud del primer punto en grados
        lon1: Longitud del primer punto en grados
        lat2: Latitud del segundo punto en grados
        lon2: Longitud del segundo punto en grados
        
    Returns:
        float: Distancia en kilómetros entre los dos puntos
    """
    # Radio de la Tierra en kilómetros
    R = 6371.0
    
    # Convertir grados a radianes
    lat1_rad = math.radians(lat1)
    lon1_rad = math.radians(lon1)
    lat2_rad = math.radians(lat2)
    lon2_rad = math.radians(lon2)
    
    # Diferencia de latitud y longitud
    dlat = lat2_rad - lat1_rad
    dlon = lon2_rad - lon1_rad
    
    # Fórmula de Haversine
    a = math.sin(dlat / 2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2)**2
    c = 2 * math.asin(math.sqrt(a))
    
    # Distancia en kilómetros
    distance = R * c
    
    return distance


def is_within_radius(
    center_lat: float,
    center_lon: float,
    point_lat: float,
    point_lon: float,
    radius_km: float
) -> bool:
    """
    Verifica si un punto está dentro de un radio determinado desde un punto central.
    
    Args:
        center_lat: Latitud del punto central
        center_lon: Longitud del punto central
        point_lat: Latitud del punto a verificar
        point_lon: Longitud del punto a verificar
        radius_km: Radio en kilómetros
        
    Returns:
        bool: True si el punto está dentro del radio, False en caso contrario
    """
    distance = haversine_distance(center_lat, center_lon, point_lat, point_lon)
    return distance <= radius_km


def calculate_bounding_box(
    center_lat: float,
    center_lon: float,
    radius_km: float
) -> Tuple[float, float, float, float]:
    """
    Calcula un bounding box (caja delimitadora) aproximada para optimizar consultas.
    Esto permite filtrar primero por un rectángulo antes de calcular la distancia exacta.
    
    Args:
        center_lat: Latitud del punto central
        center_lon: Longitud del punto central
        radius_km: Radio en kilómetros
        
    Returns:
        Tuple: (min_lat, max_lat, min_lon, max_lon)
    """
    # Radio de la Tierra en kilómetros
    R = 6371.0
    
    # Convertir radio a grados (aproximación)
    # 1 grado de latitud ≈ 111 km
    lat_delta = radius_km / 111.0
    
    # 1 grado de longitud ≈ 111 km * cos(latitud)
    lon_delta = radius_km / (111.0 * math.cos(math.radians(center_lat)))
    
    min_lat = center_lat - lat_delta
    max_lat = center_lat + lat_delta
    min_lon = center_lon - lon_delta
    max_lon = center_lon + lon_delta
    
    return (min_lat, max_lat, min_lon, max_lon)
