from typing import List, Tuple, Literal, Dict, Any 
from pydantic import BaseModel, Field  

Tile = Literal["C", "B", "P"] # Tipos de celdas: Calle, Edificio, Parque

class LegendItem(BaseModel): 
    name: str # Nombre descriptivo del tipo de celda
    surface_weight: float | None = None #afecta la velocidad del jugador
    blocked: bool | None = None #indica si la celda es transitable

class CityMap(BaseModel): # Modelo para el mapa de la ciudad
    version: str
    width: int
    height: int
    tiles: List[List[Tile]]
    legend: Dict[str, LegendItem]
    goal: int | None = Field(default=None, alias="goal")
    max_time: int | None = Field(default=None, alias="max_time")

class Job(BaseModel): # Modelo para un trabajo de entrega
    id: str
    pickup: Tuple[int, int]
    dropoff: Tuple[int, int]
    payout: float
    deadline: str
    weight: int
    priority: int
    release_time: int

class WeatherBurst(BaseModel): # Modelo para un evento climático
    duration_sec: int
    condition: str
    intensity: float

class WeatherReport(BaseModel): # Modelo para el reporte del clima
    city: str
    date: str
    bursts: List[WeatherBurst]
    meta: Dict[str, Any] | None = None
