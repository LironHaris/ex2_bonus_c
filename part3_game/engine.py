"""Sort integration + resource gates for the Part C route-economy game.

Sorting always runs in the existing C library (bus_bubble_sort / bus_quick_sort)
via python_bindings_module/bus_module.py -- this module only marshals BusRoute
objects to/from the plain tuples that binding expects, and applies the
afford/time-fit gates. No sorting logic is reimplemented in Python.

Levels 3+ introduce transfer hubs: not every route starts at HOME, so the
player's current position (GameState.current_node) determines which routes
are actually boardable (routes_from()), and boarding a route only clears the
level once it lands on the level's end node -- see board_route().
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


def sort_routes(routes: List[BusRoute], sort_by: str) -> List[BusRoute]:
    """Sort the given routes by name, distance, duration, or frequency,
    deferring the actual sort to the C library. Returns BusRoute objects
    (with price/path/origin/destination reattached), not the raw tuples the
    C binding works with. Callers pass in whatever subset is currently
    relevant (routes_from(level, state.current_node)), so the real C sort
    always runs on the player's current active choices."""
    by_name = {route.name: route for route in routes}
    tuples = [(r.name, r.distance, r.duration, r.frequency) for r in routes]

    if sort_by == "name":
        sorted_tuples = bubble_sort(tuples)
    elif sort_by in _QUICK_SORT_FIELDS:
        sorted_tuples = quick_sort(tuples, _QUICK_SORT_FIELDS[sort_by])
    else:
        raise ValueError(f"unknown sort_by: {sort_by!r}")

    return [by_name[t[0]] for t in sorted_tuples]


def routes_from(level: LevelConfig, node: str) -> List[BusRoute]:
    """Routes boardable from `node` (HOME, UNIVERSITY, or a transfer hub)."""
    return [route for route in level.bus_routes if route.origin == node]


def next_bus_minutes(state: GameState, route: BusRoute) -> int:
    """Deterministic "next departure" countdown, in minutes, for route's
    headway (route.frequency). Driven by the monotonic elapsed_minutes clock
    (see tick()) rather than wall-clock time, so the electronic sign, the
    Trip Planner, and the actual wait-time cost deducted on boarding always
    agree on the same number for the same instant. Each route gets a fixed
    phase offset (derived from its name) so same-headway lines don't all
    depart in lockstep; counts down to 1 and then wraps back to the full
    headway, matching a real departure "resetting" the cycle."""
    headway = max(1, route.frequency)
    phase = sum(ord(c) for c in route.name) % headway
    elapsed_whole_minutes = int(state.elapsed_minutes)
    cycle_position = (elapsed_whole_minutes + phase) % headway
    return headway - cycle_position


def tick(state: GameState, elapsed_minutes: float) -> GameState:
    """Advance the continuous game clock by elapsed_minutes -- the clock keeps
    running in real time regardless of whether the player has boarded
    anything yet, independent of the discrete duration+wait deduction
    board_route() applies once a line is actually boarded. elapsed_minutes
    also accumulates into elapsed_minutes, which drives next_bus_minutes()."""
    return replace(
        state,
        time_remaining=max(0.0, state.time_remaining - elapsed_minutes),
        elapsed_minutes=state.elapsed_minutes + elapsed_minutes,
    )


def can_board(state: GameState, route: BusRoute) -> bool:
    """A line is boardable if its price is affordable and there's enough time
    left for both the wait for its next departure and the ride itself."""
    wait = next_bus_minutes(state, route)
    return state.money >= route.price and state.time_remaining >= route.duration + wait


def is_stuck(state: GameState, level: LevelConfig) -> bool:
    """True if no route departing the player's current node is currently
    affordable and reachable in time."""
    return not any(can_board(state, route) for route in routes_from(level, state.current_node))


def enter_level(state: GameState, level: LevelConfig) -> GameState:
    """Place the player at a (new) level's starting node -- called once when
    advancing into a level, so a multi-hop level always begins fresh at its
    start node regardless of where the previous level ended."""
    return replace(state, current_node=level.start)


def board_route(state: GameState, level: LevelConfig, route: BusRoute, bypass_checks: bool = False) -> GameState:
    """Board `route`: deduct its price plus (wait-for-next-departure + travel
    duration) in time, and move the player to route.destination. Only once
    that destination is the level's end node does this also apply the
    level's reward and advance level_index -- intermediate hops in a
    multi-transfer level are otherwise "free" of level-clear side effects.
    Raises ValueError if the gates (money/time) aren't met -- callers should
    check can_board() first. bypass_checks=True skips that gate entirely
    (money/time_remaining may go negative) -- used only by the GUI's
    developer-only Admin Mode, never by normal play."""
    if not bypass_checks and not can_board(state, route):
        raise ValueError(f"cannot board {route.name!r}: fails money/time gate")
    wait = next_bus_minutes(state, route)
    reached_end = route.destination == level.end
    return replace(
        state,
        money=state.money - route.price + (level.reward_money if reached_end else 0),
        time_remaining=state.time_remaining - route.duration - wait + (level.reward_time if reached_end else 0),
        current_node=route.destination,
        level_index=state.level_index + 1 if reached_end else state.level_index,
    )
