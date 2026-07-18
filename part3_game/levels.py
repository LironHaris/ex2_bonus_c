"""Hardcoded level data for the Part C route-economy game.

Bus line fields must satisfy the same constraints main.c's validate_bus_line
enforces (reused as-is by bus_module._to_c_array): name is lowercase a-z/0-9
only (max 20 chars), distance in [0, 1000], duration in [10, 100], frequency
in [1, 50]. frequency now doubles as a route's headway in minutes (see
engine.next_bus_minutes) rather than a "times per day" flavor number, so it
stays deliberately small.

Names are just lowercase color tags -- game.py maps each one to a display
label ("Red Line", etc.) and color via its index in level.bus_routes (see
game.py's ROUTE_COLORS/LINE_LABELS). Re-used across levels since each
level's bus_routes list is its own namespace.

Levels 1-2 are single-hop: every line goes straight from HOME to UNIVERSITY.
Levels 3-5 (Advanced Grid Expansion) introduce transfer hubs -- nodes other
than HOME/UNIVERSITY that some lines only depart from, so the player has to
chain multiple lines together to cross the whole level. No mini-games in
levels 3-5; station/task_type stay None throughout.
"""

from models import BusRoute, LevelConfig

HOME = (0, 0)
UNIVERSITY = (0, 20)

LEVEL_1_INTRO = LevelConfig(
    start="HOME",
    end="UNIVERSITY",
    nodes={"HOME": HOME, "UNIVERSITY": UNIVERSITY},
    # Introductory level: every line drives straight from HOME to UNIVERSITY
    # with no intermediate station and no mini-game -- station/task_type are
    # both None, and game.py's attempt_board()/draw_map() special-case that
    # to skip the station-task sequence entirely.
    bus_routes=[
        BusRoute("redline", distance=50, duration=10, frequency=3, price=15,
                 origin="HOME", destination="UNIVERSITY",
                 path=[HOME, UNIVERSITY], station=None, task_type=None),
        BusRoute("greenline", distance=70, duration=14, frequency=4, price=25,
                 origin="HOME", destination="UNIVERSITY",
                 path=[HOME, UNIVERSITY], station=None, task_type=None),
        BusRoute("blueline", distance=40, duration=12, frequency=2, price=5,
                 origin="HOME", destination="UNIVERSITY",
                 path=[HOME, UNIVERSITY], station=None, task_type=None),
    ],
    reward_money=20,
    reward_time=14,
)

LEVEL_2_ADVANCED = LevelConfig(
    start="HOME",
    end="UNIVERSITY",
    nodes={"HOME": HOME, "UNIVERSITY": UNIVERSITY},
    # Each route's single intermediate station is the first interior point on
    # its path; task_type cycles through the 3 mini-games across the 5 lines.
    bus_routes=[
        BusRoute("redline", distance=80, duration=15, frequency=3, price=20,
                 origin="HOME", destination="UNIVERSITY",
                 path=[HOME, (0, 10), UNIVERSITY], station=(0, 10), task_type="agility"),
        BusRoute("greenline", distance=120, duration=12, frequency=5, price=45,
                 origin="HOME", destination="UNIVERSITY",
                 path=[HOME, (2, 8), UNIVERSITY], station=(2, 8), task_type="memory"),
        BusRoute("blueline", distance=60, duration=25, frequency=2, price=10,
                 origin="HOME", destination="UNIVERSITY",
                 path=[HOME, (-1, 5), (1, 12), UNIVERSITY], station=(-1, 5), task_type="thinking"),
        BusRoute("yellowline", distance=150, duration=20, frequency=4, price=35,
                 origin="HOME", destination="UNIVERSITY",
                 path=[HOME, (3, 6), (3, 15), UNIVERSITY], station=(3, 6), task_type="agility"),
        BusRoute("purpleline", distance=90, duration=18, frequency=3, price=25,
                 origin="HOME", destination="UNIVERSITY",
                 path=[HOME, (1, 4), (0, 14), UNIVERSITY], station=(1, 4), task_type="memory"),
    ],
    reward_money=40,
    reward_time=20,
)

# -- Advanced Grid Expansion (levels 3-5): transfer hubs, no mini-games -----

_L3_HOME = (0, 0)
_L3_CENTRAL = (0, 10)
_L3_UNI = (0, 20)

LEVEL_3_JUNCTION = LevelConfig(
    start="HOME",
    end="UNIVERSITY",
    nodes={"HOME": _L3_HOME, "CENTRAL_STATION": _L3_CENTRAL, "UNIVERSITY": _L3_UNI},
    bus_routes=[
        BusRoute("redline", distance=45, duration=10, frequency=3, price=12,
                 origin="HOME", destination="CENTRAL_STATION",
                 path=[_L3_HOME, (0, 5), _L3_CENTRAL], station=None, task_type=None),
        BusRoute("greenline", distance=55, duration=11, frequency=2, price=18,
                 origin="HOME", destination="CENTRAL_STATION",
                 path=[_L3_HOME, (-2, 5), _L3_CENTRAL], station=None, task_type=None),
        BusRoute("blueline", distance=50, duration=10, frequency=3, price=14,
                 origin="CENTRAL_STATION", destination="UNIVERSITY",
                 path=[_L3_CENTRAL, (0, 15), _L3_UNI], station=None, task_type=None),
        BusRoute("yellowline", distance=60, duration=13, frequency=4, price=20,
                 origin="CENTRAL_STATION", destination="UNIVERSITY",
                 path=[_L3_CENTRAL, (2, 15), _L3_UNI], station=None, task_type=None),
        BusRoute("purpleline", distance=140, duration=24, frequency=5, price=48,
                 origin="HOME", destination="UNIVERSITY",
                 path=[_L3_HOME, (3, 10), _L3_UNI], station=None, task_type=None),
        BusRoute("orangeline", distance=130, duration=28, frequency=2, price=30,
                 origin="HOME", destination="UNIVERSITY",
                 path=[_L3_HOME, (-3, 10), _L3_UNI], station=None, task_type=None),
    ],
    reward_money=45,
    reward_time=32,
)

_L4_HOME = (0, 0)
_L4_CENTRAL = (0, 8)
_L4_OLDCITY = (0, 15)
_L4_UNI = (0, 22)

LEVEL_4_CROSSTOWN = LevelConfig(
    start="HOME",
    end="UNIVERSITY",
    nodes={"HOME": _L4_HOME, "CENTRAL_STATION": _L4_CENTRAL, "OLD_CITY": _L4_OLDCITY, "UNIVERSITY": _L4_UNI},
    bus_routes=[
        BusRoute("redline", distance=40, duration=10, frequency=2, price=10,
                 origin="HOME", destination="CENTRAL_STATION",
                 path=[_L4_HOME, (0, 4), _L4_CENTRAL], station=None, task_type=None),
        BusRoute("greenline", distance=55, duration=11, frequency=3, price=16,
                 origin="HOME", destination="CENTRAL_STATION",
                 path=[_L4_HOME, (-2, 4), _L4_CENTRAL], station=None, task_type=None),
        BusRoute("blueline", distance=42, duration=10, frequency=3, price=12,
                 origin="CENTRAL_STATION", destination="OLD_CITY",
                 path=[_L4_CENTRAL, (0, 11), _L4_OLDCITY], station=None, task_type=None),
        BusRoute("yellowline", distance=58, duration=13, frequency=2, price=18,
                 origin="CENTRAL_STATION", destination="OLD_CITY",
                 path=[_L4_CENTRAL, (2, 11), _L4_OLDCITY], station=None, task_type=None),
        BusRoute("purpleline", distance=38, duration=10, frequency=3, price=10,
                 origin="OLD_CITY", destination="UNIVERSITY",
                 path=[_L4_OLDCITY, (0, 18), _L4_UNI], station=None, task_type=None),
        BusRoute("orangeline", distance=50, duration=12, frequency=4, price=16,
                 origin="OLD_CITY", destination="UNIVERSITY",
                 path=[_L4_OLDCITY, (-2, 18), _L4_UNI], station=None, task_type=None),
        BusRoute("tealline", distance=110, duration=22, frequency=4, price=35,
                 origin="HOME", destination="OLD_CITY",
                 path=[_L4_HOME, (3, 8), _L4_OLDCITY], station=None, task_type=None),
    ],
    reward_money=50,
    reward_time=48,
)

_L5_HOME = (0, 0)
_L5_CENTRAL = (0, 6)
_L5_MARKET = (0, 12)
_L5_OLDCITY = (0, 17)
_L5_UNI = (0, 24)

LEVEL_5_METRO = LevelConfig(
    start="HOME",
    end="UNIVERSITY",
    nodes={
        "HOME": _L5_HOME, "CENTRAL_STATION": _L5_CENTRAL, "MARKET_JCT": _L5_MARKET,
        "OLD_CITY": _L5_OLDCITY, "UNIVERSITY": _L5_UNI,
    },
    bus_routes=[
        BusRoute("redline", distance=35, duration=10, frequency=2, price=10,
                 origin="HOME", destination="CENTRAL_STATION",
                 path=[_L5_HOME, (0, 3), _L5_CENTRAL], station=None, task_type=None),
        BusRoute("greenline", distance=50, duration=10, frequency=3, price=16,
                 origin="HOME", destination="CENTRAL_STATION",
                 path=[_L5_HOME, (-2, 3), _L5_CENTRAL], station=None, task_type=None),
        BusRoute("blueline", distance=32, duration=10, frequency=2, price=10,
                 origin="CENTRAL_STATION", destination="MARKET_JCT",
                 path=[_L5_CENTRAL, (0, 9), _L5_MARKET], station=None, task_type=None),
        BusRoute("yellowline", distance=30, duration=10, frequency=2, price=10,
                 origin="MARKET_JCT", destination="OLD_CITY",
                 path=[_L5_MARKET, (0, 15), _L5_OLDCITY], station=None, task_type=None),
        BusRoute("purpleline", distance=36, duration=10, frequency=2, price=12,
                 origin="OLD_CITY", destination="UNIVERSITY",
                 path=[_L5_OLDCITY, (0, 20), _L5_UNI], station=None, task_type=None),
        BusRoute("orangeline", distance=48, duration=11, frequency=3, price=18,
                 origin="OLD_CITY", destination="UNIVERSITY",
                 path=[_L5_OLDCITY, (-2, 20), _L5_UNI], station=None, task_type=None),
        BusRoute("tealline", distance=120, duration=22, frequency=4, price=40,
                 origin="CENTRAL_STATION", destination="UNIVERSITY",
                 path=[_L5_CENTRAL, (3, 15), _L5_UNI], station=None, task_type=None),
        BusRoute("pinkline", distance=80, duration=15, frequency=3, price=28,
                 origin="HOME", destination="MARKET_JCT",
                 path=[_L5_HOME, (3, 6), _L5_MARKET], station=None, task_type=None),
    ],
    reward_money=0,
    reward_time=0,
)

LEVELS = [LEVEL_1_INTRO, LEVEL_2_ADVANCED, LEVEL_3_JUNCTION, LEVEL_4_CROSSTOWN, LEVEL_5_METRO]
