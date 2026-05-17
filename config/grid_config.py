"""
Geographic grid configuration.
Currently set for India — change bounds for other regions.
"""

# ── Region Profiles ──
REGIONS = {
    "india": {
        "name": "India",
        "lat_min": 8.0,
        "lat_max": 37.0,
        "lon_min": 68.0,
        "lon_max": 97.5,
        "grid_spacing": 0.5,       # degrees (~55 km)
        "crs": "EPSG:4326",
        "boundary_file": "india_boundary.geojson",
    },
    "global": {
        "name": "Global",
        "lat_min": -60.0,
        "lat_max": 70.0,
        "lon_min": -180.0,
        "lon_max": 180.0,
        "grid_spacing": 1.0,       # degrees (~111 km)
        "crs": "EPSG:4326",
        "boundary_file": None,
    },
}

# ── Active Region (change this ONE line to switch) ──
ACTIVE_REGION = "india"

def get_active_region() -> dict:
    """Return the currently active region configuration."""
    return REGIONS[ACTIVE_REGION]