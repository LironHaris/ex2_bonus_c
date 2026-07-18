"""Hardcoded level data for the Part C route-economy game.

Bus line fields must satisfy the same constraints main.c's validate_bus_line
enforces (reused as-is by bus_module._to_c_array): name is lowercase a-z/0-9
only (max 20 chars), distance in [0, 1000], duration in [10, 100], frequency
in [1, 50].
"""

from models import BusRoute, LevelConfig

HOME = (0, 0)
UNIVERSITY = (0, 20)

LEVEL_1 = LevelConfig(
    start=HOME,
    end=UNIVERSITY,
    # Each route's single intermediate station is the first interior point on
    # its path; task_type cycles through the 3 mini-games across the 5 lines.
    bus_routes=[
        BusRoute("line210", distance=80, duration=15, frequency=10, price=20,
                 path=[HOME, (0, 10), UNIVERSITY], station=(0, 10), task_type="agility"),
        BusRoute("express40", distance=120, duration=12, frequency=5, price=45,
                 path=[HOME, (2, 8), UNIVERSITY], station=(2, 8), task_type="memory"),
        BusRoute("local5", distance=60, duration=25, frequency=20, price=10,
                 path=[HOME, (-1, 5), (1, 12), UNIVERSITY], station=(-1, 5), task_type="thinking"),
        BusRoute("nightride", distance=150, duration=20, frequency=30, price=35,
                 path=[HOME, (3, 6), (3, 15), UNIVERSITY], station=(3, 6), task_type="agility"),
        BusRoute("campushopper", distance=90, duration=18, frequency=8, price=25,
                 path=[HOME, (1, 4), (0, 14), UNIVERSITY], station=(1, 4), task_type="memory"),
    ],
    reward_money=40,
    reward_time=15,
)

LEVELS = [LEVEL_1]
