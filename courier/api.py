import json
import random
import requests
from pathlib import Path
from .config import BASE_URL, DATA_DIR, CACHE_DIR
from .models import CityMap, Job, WeatherReport

def _get_cached_json(endpoint: str) -> dict | list:
    """Obtiene JSON desde la API, cache o archivos locales."""
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
    """Obtiene y valida el mapa de la ciudad."""
    data = _get_cached_json("/city/map")
    if "data" in data:
        data = data["data"]
    return CityMap.model_validate(data)

def get_jobs() -> list[Job]:
    """Obtiene y valida la lista de trabajos."""
    data = _get_cached_json("/city/jobs")
    if isinstance(data, dict) and "data" in data:
        data = data["data"]
    jobs = [Job.model_validate(j) for j in data]
    for i, job in enumerate(jobs):
        job.release_time = i * 15
    return jobs

def get_weather() -> WeatherReport:
    """Obtiene y valida el reporte del clima. Si no hay bursts, los genera dinámicamente."""
    try:
        raw = _get_cached_json("/city/weather")
        data = raw.get("data", raw)
        if "bursts" in data and isinstance(data["bursts"], list) and len(data["bursts"]) >= 2:
            return WeatherReport.model_validate(data)
    except:
        pass  # Si falla o no hay bursts, intentamos generar desde transición

    try:
        local = (DATA_DIR / "weather.json").read_text()
        raw = json.loads(local)
        base = raw.get("data", raw)

        # Validar estructura mínima para generar clima dinámico
        if not isinstance(base, dict) or not all(k in base for k in ("conditions", "transition", "initial")):
            raise ValueError("weather.json no tiene estructura válida para generar clima dinámico")

        condiciones = base["conditions"]
        transiciones = base["transition"]
        actual = base["initial"]["condition"]
        ciudad = base.get("city", "CiudadDesconocida")

        bursts = []
        usados = set()

        for _ in range(5):
            duracion = random.randint(60, 90)
            intensidad = round(random.uniform(0.1, 1.0), 2)
            bursts.append({
                "condition": actual,
                "duration_sec": duracion,
                "intensity": intensidad
            })
            usados.add(actual)

            opciones = transiciones.get(actual, {})
            posibles = [c for c in opciones.keys() if c not in usados]
            actual = (
                random.choices(posibles, weights=[opciones[c] for c in posibles])[0]
                if posibles else random.choice(condiciones)
            )

        return WeatherReport.model_validate({
            "date": "2025-10-05",
            "city": ciudad,
            "bursts": bursts
        })

    except Exception:
        # Si todo falla, devolvemos un clima por defecto para evitar que el juego se rompa
        return WeatherReport.model_validate({
            "date": "2025-10-05",
            "city": "CiudadDesconocida",
            "bursts": [
                {"condition": "clear", "duration_sec": 9999, "intensity": 0.1}
            ]
        })

