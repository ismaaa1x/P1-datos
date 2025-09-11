import json
import time
import requests
from .config import (
    BASE_API, ENDPOINTS,
    RUTA_MAPA, RUTA_PEDIDOS, RUTA_WEATHER,
    CACHE_DIR, DATOS_DIR
)

CACHE_DIR.mkdir(parents=True, exist_ok=True)
DATOS_DIR.mkdir(parents=True, exist_ok=True)

def _read_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def _write_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def _cache_path(name: str):
    return CACHE_DIR / f"{name}.json"

def _fetch(endpoint: str):
    url = f"{BASE_API}{endpoint}"
    r = requests.get(url, timeout=8)
    r.raise_for_status()
    return r.json()

def _get_with_cache(name: str, endpoint: str, offline_path):
    try:
        data = _fetch(endpoint)
        _write_json(_cache_path(name), {"ts": time.time(), "data": data})
        _write_json(offline_path, data)
        return data
    except Exception:
        cpath = _cache_path(name)
        if cpath.exists():
            return _read_json(cpath)["data"]
        if offline_path.exists():
            return _read_json(offline_path)
        raise

def get_map():
    return _get_with_cache("map", ENDPOINTS["map"], RUTA_MAPA)

def get_jobs():
    return _get_with_cache("jobs", ENDPOINTS["jobs"], RUTA_PEDIDOS)

def get_weather():
    return _get_with_cache("weather", ENDPOINTS["weather"], RUTA_WEATHER)
