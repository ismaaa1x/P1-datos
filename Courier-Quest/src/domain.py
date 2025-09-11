from dataclasses import dataclass
from typing import List, Dict, Tuple, Any

@dataclass
class WeatherBurst:
    condition: str
    intensity: float
    duration_sec: float

@dataclass
class MapData:
    tiles: List[List[str]]
    legend: Dict[str, Dict[str, Any]]
    width: int
    height: int

@dataclass
class Job:
    id: str
    pickup: Tuple[int, int]
    dropoff: Tuple[int, int]
    weight: float
    payout: float
    priority: float
    deadline_s: float
    release_time: float
