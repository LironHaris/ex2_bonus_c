"""Sort integration + resource gates for the Part C route-economy game.

Sorting always runs in the existing C library (bus_bubble_sort / bus_quick_sort)
via python_bindings_module/bus_module.py -- this module only marshals BusRoute
objects to/from the plain tuples that binding expects, and applies the
afford/time-fit gates. No sorting logic is reimplemented in Python.
"""

import sys
from dataclasses import replace
from pathlib import Path
from typing import List

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "python_bindings_module"))
from bus_module import SortType, bubble_sort, quick_sort  # noqa: E402

from models import BusRoute, GameState, LevelConfig  # noqa: E402

_QUICK_SORT_FIELDS = {
    "distance": SortType.DISTANCE,
    "duration": SortType.DURATION,
    "frequency": SortType.FREQUENCY,
}


def sort_routes(level: LevelConfig, sort_by: str) -> List[BusRoute]:
    """Sort level.bus_routes by name, distance, duration, or frequency, deferring
    the actual sort to the C library. Returns BusRoute objects (with price/path
    reattached), not the raw tuples the C binding works with."""
    by_name = {route.name: route for route in level.bus_routes}
    tuples = [(r.name, r.distance, r.duration, r.frequency) for r in level.bus_routes]

    if sort_by == "name":
        sorted_tuples = bubble_sort(tuples)
    elif sort_by in _QUICK_SORT_FIELDS:
        sorted_tuples = quick_sort(tuples, _QUICK_SORT_FIELDS[sort_by])
    else:
        raise ValueError(f"unknown sort_by: {sort_by!r}")

    return [by_name[t[0]] for t in sorted_tuples]


def tick(state: GameState, elapsed_minutes: float) -> GameState:
    """Advance the continuous game clock by elapsed_minutes -- the clock keeps
    running in real time regardless of whether the player has boarded
    anything yet, independent of the discrete duration deduction board_route()
    applies once a line is actually boarded."""
    return replace(state, time_remaining=max(0.0, state.time_remaining - elapsed_minutes))


def can_board(state: GameState, route: BusRoute) -> bool:
    return state.money >= route.price and state.time_remaining >= route.duration


def is_stuck(state: GameState, level: LevelConfig) -> bool:
    """True if no route in the level is currently affordable and on-time."""
    return not any(can_board(state, route) for route in level.bus_routes)


def board_route(state: GameState, level: LevelConfig, route: BusRoute) -> GameState:
    """Board `route` to clear `level`: deduct its cost, apply the level's
    reward, and advance to the next level. Raises ValueError if the gates
    (money/time) aren't met -- callers should check can_board() first."""
    if not can_board(state, route):
        raise ValueError(f"cannot board {route.name!r}: fails money/time gate")
    return replace(
        state,
        money=state.money - route.price + level.reward_money,
        time_remaining=state.time_remaining - route.duration + level.reward_time,
        level_index=state.level_index + 1,
    )
