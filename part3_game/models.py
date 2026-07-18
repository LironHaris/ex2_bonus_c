"""Data model for the Part C route-economy game."""

from dataclasses import dataclass
from typing import List, Tuple

Stop = Tuple[int, int]


@dataclass
class BusRoute:
    name: str
    distance: int
    duration: int
    frequency: int
    price: int
    path: List[Stop]
    station: Stop           # intermediate stop where the boarding mini-game triggers
    task_type: str          # "agility", "memory", or "thinking" -- see minigames.py


@dataclass
class LevelConfig:
    start: Stop
    end: Stop
    bus_routes: List[BusRoute]
    reward_money: int
    reward_time: int


@dataclass
class GameState:
    money: int
    time_remaining: float
    level_index: int = 0
