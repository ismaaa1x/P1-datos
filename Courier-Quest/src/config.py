import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

BASE_API = os.getenv(
    "COURIER_API_BASE",
    "https://tigerds-api.kindflower-ccaf48b6.eastus.azurecontainerapps.io"
)

ENDPOINTS = {
    "map": "/city/map",
    "jobs": "/city/jobs",
    "weather": "/city/weather",
}

DATOS_DIR = BASE_DIR / "datos"
CACHE_DIR = BASE_DIR / "api_cache"

RUTA_MAPA = DATOS_DIR / "ciudad.json"
RUTA_PEDIDOS = DATOS_DIR / "pedidos.json"
RUTA_WEATHER = DATOS_DIR / "weather.json"
