from pathlib import Path

BASE_URL = "https://tigerds-api.kindflower-ccaf48b6.eastus.azurecontainerapps.io" # URL base para la API

DATA_DIR = Path("data") # Directorio para almacenar datos locales
CACHE_DIR = Path("api_cache") # Directorio para almacenar datos en caché
SAVES_DIR = Path("saves") # Directorio para almacenar partidas guardadas

for d in [DATA_DIR, CACHE_DIR, SAVES_DIR]: # Crea los directorios si no existen
    d.mkdir(exist_ok=True) 
