from typing import List, Tuple, Literal, Dict, Any
from pydantic import BaseModel, Field

Tile = Literal["C", "B", "P"]

class LegendItem(BaseModel):
    name: str
    surface_weight: float | None = None
    blocked: bool | None = None

class CityMap(BaseModel):
    version: str
    width: int
    height: int
    tiles: List[List[Tile]]
    legend: Dict[str, LegendItem]
    goal: int | None = Field(default=None, alias="goal")
    max_time: int | None = Field(default=None, alias="max_time")

class Job(BaseModel):
    id: str
    pickup: Tuple[int, int]
    dropoff: Tuple[int, int]
    payout: float
    deadline: str
    weight: int
    priority: int
    release_time: int

class WeatherBurst(BaseModel):
    duration_sec: int
    condition: str
    intensity: float

class WeatherReport(BaseModel):
    city: str
    date: str
    bursts: List[WeatherBurst]
    meta: Dict[str, Any] | None = None
