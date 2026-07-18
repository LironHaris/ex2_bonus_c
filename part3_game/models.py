"""Data model for the Part C route-economy game."""

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

Stop = Tuple[int, int]


@dataclass
class BusRoute:
    name: str
    distance: int
    duration: int
    frequency: int                # headway in minutes: how often this line departs its origin
    price: int
    origin: str                   # node name (key into LevelConfig.nodes) where this line can be boarded
    destination: str              # node name this line arrives at
    path: List[Stop]              # rendering polyline, path[0]/path[-1] are the origin/destination coords
    station: Optional[Stop]       # intermediate stop where the boarding mini-game triggers, or None
    task_type: Optional[str]      # "agility"/"memory"/"thinking" (see minigames.py), or None if station is None


@dataclass
class LevelConfig:
    start: str                    # node name the player begins this level at (usually "HOME")
    end: str                      # node name that clears the level once reached (usually "UNIVERSITY")
    nodes: Dict[str, Stop]        # node name -> rendering coordinate; HOME/UNIVERSITY plus any transfer hubs
    bus_routes: List[BusRoute]
    reward_money: int
    reward_time: int


@dataclass
class GameState:
    money: int
    time_remaining: float
    level_index: int = 0
    current_node: str = "HOME"    # node the player is currently standing at within the active level
    elapsed_minutes: float = 0.0  # monotonic session clock -- drives bus headway scheduling, see engine.next_bus_minutes
