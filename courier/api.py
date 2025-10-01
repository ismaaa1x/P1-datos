import json, requests
from .config import BASE_URL, DATA_DIR, CACHE_DIR
from .models import CityMap, Job, WeatherReport

def _cache_path(endpoint: str):
    return CACHE_DIR / f"{endpoint.strip('/').replace('/', '_')}.json"

def _get_cached_json(endpoint: str):
    try:
        r = requests.get(f"{BASE_URL}{endpoint}", timeout=10)
        r.raise_for_status()
        data = r.json()
        _cache_path(endpoint).write_text(json.dumps(data, indent=2), encoding="utf-8")
        return data
    except:
        if _cache_path(endpoint).exists():
            return json.loads(_cache_path(endpoint).read_text(encoding="utf-8"))
        local = {
            "/city/map": DATA_DIR / "ciudad.json",
            "/city/jobs": DATA_DIR / "pedidos.json",
            "/city/weather": DATA_DIR / "weather.json"
        }.get(endpoint)
        if local and local.exists():
            return json.loads(local.read_text(encoding="utf-8"))
        raise RuntimeError(f"No se pudo obtener {endpoint}")

def get_city_map() -> CityMap:
    data = _get_cached_json("/city/map")
    if isinstance(data, dict) and "data" in data:
        data = data["data"]
    return CityMap.model_validate(data)

def get_jobs() -> list[Job]:
    data = _get_cached_json("/city/jobs")
    if isinstance(data, dict) and "data" in data:
        data = data["data"]
    return [Job.model_validate(j) for j in data]

def get_weather() -> WeatherReport:
    data = _get_cached_json("/city/weather")
    return WeatherReport.model_validate(data)
