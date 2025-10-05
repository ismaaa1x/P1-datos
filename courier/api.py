import json 
import requests  
from pathlib import Path 
from .config import BASE_URL, DATA_DIR, CACHE_DIR 
from .models import CityMap, Job, WeatherReport

def _get_cached_json(endpoint: str) -> dict | list: # funcion para obtener json desde cache o url
    try: 
        r = requests.get(f"{BASE_URL}{endpoint}", timeout=10) # Realiza la solicitud HTTP
        r.raise_for_status() # Lanza un error si la solicitud no fue exitosa
        data = r.json() # Parsea la respuesta JSON
        (CACHE_DIR / f"{endpoint.strip('/').replace('/', '_')}.json").write_text(json.dumps(data, indent=2)) # Guarda en cache
        return data # Devuelve los datos obtenidos
    except: 
        try: # Si falla, intenta leer desde cache
            cached = (CACHE_DIR / f"{endpoint.strip('/').replace('/', '_')}.json").read_text() # Intenta leer desde cache
            return json.loads(cached) # Devuelve los datos cacheados
        except: # Si no hay cache, lee desde archivos locales
            local = { 
                "/city/map": DATA_DIR / "ciudad.json", # Archivo local para el mapa de la ciudad
                "/city/jobs": DATA_DIR / "pedidos.json", # Archivo local para los trabajos 
                "/city/weather": DATA_DIR / "weather.json" # Archivo local para el clima
            }.get(endpoint) # Mapea endpoint a archivo local
            if local and local.exists(): # Si el archivo existe, lo lee
                return json.loads(local.read_text()) # Devuelve los datos del archivo local
            raise RuntimeError(f"No se pudo obtener {endpoint}") # Si todo falla, lanza un error

def get_city_map() -> CityMap: # Obtiene y valida el mapa de la ciudad
    data = _get_cached_json("/city/map") # Obtiene los datos del endpoint
    if "data" in data: #
        data = data["data"] # Extrae la sección 'data' si existe
    return CityMap.model_validate(data) 

def get_jobs() -> list[Job]: # Obtiene y valida la lista de trabajos
    data = _get_cached_json("/city/jobs") # Obtiene los datos del endpoint
    if isinstance(data, dict) and "data" in data: 
        data = data["data"] 
    jobs = [Job.model_validate(j) for j in data] # Valida cada trabajo

    
    for i, job in enumerate(jobs): # Asigna tiempos de liberación escalonados
        job.release_time = i * 15 # Cada trabajo se libera 15 segundos después del anterior
    return jobs # Devuelve la lista de trabajos


def get_weather() -> WeatherReport: # Obtiene y valida el reporte del clima
    try:
        data = _get_cached_json("/city/weather") # Obtiene los datos del endpoint
        if "date" not in data or "bursts" not in data: # Verifica que los datos sean válidos
            local = (DATA_DIR / "weather.json").read_text() # Si no son válidos, lee desde el archivo local
            data = json.loads(local) # Parsea los datos del archivo local
    except: # Si falla, lee desde el archivo local
        local = (DATA_DIR / "weather.json").read_text() # Lee el archivo local
        data = json.loads(local) 
    return WeatherReport.model_validate(data) # Valida y devuelve el reporte del clima

