from pathlib import Path

BASE_URL = "https://tigerds-api.kindflower-ccaf48b6.eastus.azurecontainerapps.io"

DATA_DIR = Path("data")
CACHE_DIR = Path("api_cache")
SAVES_DIR = Path("saves")

for d in [DATA_DIR, CACHE_DIR, SAVES_DIR]:
    d.mkdir(exist_ok=True)
