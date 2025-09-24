import json, requests
from pathlib import Path
from .config import BASE_URL, DATA_DIR, CACHE_DIR
from .models import CityMap, Job, WeatherReport

def _get_cached_json(endpoint: str) -> dict | list:
    try:
        r = requests.get(f"{BASE_URL}{endpoint}", timeout=10)
        r.raise_for_status()
        data = r.json()
        (CACHE_DIR / f"{endpoint.strip('/').replace('/', '_')}.json").write_text(json.dumps(data, indent=2))
        return data
    except:
        try:
            cached = (CACHE_DIR / f"{endpoint.strip('/').replace('/', '_')}.json").read_text()
            return json.loads(cached)
        except:
            local = {
                "/city/map": DATA_DIR / "ciudad.json",
                "/city/jobs": DATA_DIR / "pedidos.json",
                "/city/weather": DATA_DIR / "weather.json"
            }.get(endpoint)
            if local and local.exists():
                return json.loads(local.read_text())
            raise RuntimeError(f"No se pudo obtener {endpoint}")

def get_city_map() -> CityMap:
    data = _get_cached_json("/city/map")

    if "data" in data:
        data = data["data"]
    return CityMap.model_validate(data)


def get_jobs() -> list[Job]:
    return [Job.model_validate(j) for j in _get_cached_json("/city/jobs")]

def get_weather() -> WeatherReport:
    return WeatherReport.model_validate(_get_cached_json("/city/weather"))
