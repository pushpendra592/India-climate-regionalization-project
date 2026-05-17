"""
Geographic utility functions.
"""

import numpy as np


def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate the great-circle distance between two points on Earth.
    
    Args:
        lat1, lon1: Coordinates of point 1 (degrees)
        lat2, lon2: Coordinates of point 2 (degrees)
    
    Returns:
        Distance in kilometers
    """
    R = 6371  # Earth's radius in km

    lat1, lon1, lat2, lon2 = map(np.radians, [lat1, lon1, lat2, lon2])

    dlat = lat2 - lat1
    dlon = lon2 - lon1

    a = np.sin(dlat / 2) ** 2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon / 2) ** 2
    c = 2 * np.arctan2(np.sqrt(a), np.sqrt(1 - a))

    return R * c


def create_grid(lat_min, lat_max, lon_min, lon_max, spacing):
    """
    Create a regular lat/lon grid.
    
    Returns:
        List of (lat, lon) tuples
    """
    lats = np.arange(lat_min, lat_max + spacing, spacing)
    lons = np.arange(lon_min, lon_max + spacing, spacing)

    grid_points = [(round(lat, 4), round(lon, 4)) for lat in lats for lon in lons]

    return grid_points


def point_in_polygon(lat: float, lon: float, polygon) -> bool:
    """
    Check if a point is inside a polygon using shapely.
    
    Args:
        lat, lon: Point coordinates
        polygon: Shapely Polygon or MultiPolygon
    
    Returns:
        True if point is inside polygon
    """
    from shapely.geometry import Point
    return polygon.contains(Point(lon, lat))