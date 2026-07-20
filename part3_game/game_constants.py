"""Constants for the Part C route-economy game's pygame GUI: colors, layout
rects, and copy text. Pure data -- no pygame.init() required to import this
(pygame.Rect/pygame.K_* work before init, same as before this module split).
Split out of game.py so that file (and every other piece of the GUI) stays a
manageable size; see game.py's module docstring for the full file layout.
"""

import pygame

STARTING_MONEY = 30
STARTING_TIME = 26.0

# The clock never waits for the player to decide -- it counts down in real
# time regardless of input, on top of whatever duration boarding a line costs.
# 1/60 means 60 real seconds = 1 game-minute, i.e. the clock runs at the same
# pace as a real clock (time_remaining is in minutes; the display renders it
# as MM:SS).
GAME_MINUTES_PER_REAL_SECOND = 1.0 / 60.0

# Design-space resolution. Every layout constant below is authored in this
# coordinate system; GameGUI._recompute_scale() maps it onto the actual window.
BASE_WIDTH, BASE_HEIGHT = 800, 600

LETTERBOX_COLOR = (12, 11, 10)     # fills the window outside the scaled content

# -- Jerusalem urban theme palette ------------------------------------------
WINDOW_BG = (214, 205, 190)        # light stone-gray, fills the content area
PANEL_BG = (196, 187, 168)         # slightly darker stone, top/bottom panels
MAP_BG = (230, 217, 188)           # warm Jerusalem-stone beige, map interior
TEXT_COLOR = (45, 40, 35)          # dark warm gray, readable on light stone
DIM_TEXT_COLOR = (110, 102, 90)
AFFORD_COLOR = (20, 120, 55)       # dark green, readable on light panels
DENY_COLOR = (165, 35, 35)         # dark red, readable on light panels

# -- retro amber LCD "electronic sign" palette, for the station display -----
SIGN_BG = (18, 16, 14)
SIGN_BORDER_COLOR = (70, 62, 50)
SIGN_TEXT_COLOR = (255, 176, 40)     # amber
SIGN_TEXT_DIM = (120, 84, 30)        # dimmed amber, line no longer affordable/on-time
SIGN_TEXT_HOVER = (255, 214, 120)    # brighter amber, hovered/selected line

# Unified thick "ink" outline used on every map asset (buildings, roads,
# stations) -- a hallmark of the premium vector/cartoon look: every asset
# shares the same dark stroke color regardless of its own hue.
OUTLINE_COLOR = (32, 28, 24)
SHADOW_COLOR = (150, 140, 120)     # soft ground shadow under buildings/stations

ROAD_OUTLINE = OUTLINE_COLOR       # thick dark outer border of every road bed
ROAD_EDGE = (240, 231, 205)        # light stone-cream trim peeking along the border
ROAD_FILL = (110, 104, 96)         # dark asphalt-gray body
BUILDING_COLORS = [
    (222, 202, 160),   # light cream stone
    (196, 172, 128),   # tan stone
    (232, 214, 178),   # pale beige stone
    (206, 184, 140),   # warm tan stone
]
HOUSE_WALL_COLOR = (236, 214, 182)
HOUSE_ROOF_COLOR = (185, 92, 62)
HOUSE_DOOR_COLOR = (110, 68, 44)
HOUSE_AWNING_COLOR = (72, 132, 92)
UNIVERSITY_BUILDING_COLOR = (206, 196, 176)
WINDOW_GLASS_COLOR = (150, 190, 205)
WINDOW_FRAME_COLOR = (250, 248, 240)

# Old City (Ir Atika) wall-segment icon.
WALL_STONE_COLOR = (176, 140, 96)
WALL_STONE_DARK = (140, 108, 72)

# The Market (Machane Yehuda) stall icon.
MARKET_COUNTER_COLOR = (150, 108, 68)
MARKET_STRIPE_RED = (190, 50, 45)
MARKET_STRIPE_WHITE = (240, 236, 222)

# Soft background patches suggesting public squares / parks / neighborhoods.
# (x_fraction, y_fraction, radius, RGBA) within MAP_RECT.
MAP_PATCHES = [
    (0.18, 0.28, 70, (255, 244, 214, 70)),
    (0.55, 0.55, 92, (198, 228, 198, 55)),
    (0.82, 0.32, 58, (255, 244, 214, 65)),
    (0.35, 0.78, 62, (198, 228, 198, 55)),
]

# One color per bus line, in level order -- up to 8 lines (Level 5's max).
# Darkened slightly from pure primaries so they stay legible on light stone.
ROUTE_COLORS = [
    (200, 30, 30),
    (30, 150, 65),
    (30, 95, 205),
    (205, 165, 20),
    (150, 55, 165),
    (215, 120, 30),
    (30, 150, 150),
    (210, 80, 150),
]

# Display labels, aligned by index with ROUTE_COLORS/level.bus_routes -- each
# line's on-screen name is just its color (levels.py's route.name fields are
# lowercase tags like "redline" for the C validator; this is the human label).
LINE_LABELS = [
    "Red Line", "Green Line", "Blue Line", "Yellow Line",
    "Purple Line", "Orange Line", "Teal Line", "Pink Line",
]

# Scattered city blocks: (x_fraction, y_fraction, width, height, has_roof_unit)
# within MAP_RECT. Kept clear of the far left/right edges, where the
# HOME/UNIVERSITY icons sit.
BUILDING_LAYOUT = [
    (0.16, 0.14, 40, 26, True), (0.22, 0.72, 34, 30, False), (0.32, 0.20, 30, 22, False),
    (0.44, 0.78, 44, 28, True), (0.55, 0.22, 26, 34, False), (0.63, 0.70, 38, 24, False),
    (0.72, 0.16, 30, 30, False), (0.78, 0.75, 26, 26, True),
]

TOP_PANEL_HEIGHT = 50
MAP_RECT = pygame.Rect(20, TOP_PANEL_HEIGHT + 10, 760, 300)
MAP_CONTENT_RECT = MAP_RECT.inflate(-100, -40)
BOTTOM_PANEL_RECT = pygame.Rect(20, TOP_PANEL_HEIGHT + 320, 760, 220)

# A tab flush with the right edge of the map, and the modal it opens.
TRIP_PLANNER_TAB_RECT = pygame.Rect(778, 150, 22, 160)
TRIP_PLANNER_MODAL_RECT = pygame.Rect(90, 60, 620, 460)

# Small developer-only buttons, top-right corner of the status bar -- jump
# levels directly for testing routing without playing through everything
# before it. Bypasses win/loss checks entirely (see GameLogicMixin._debug_change_level).
DEBUG_PREV_RECT = pygame.Rect(BASE_WIDTH - 180, 4, 82, 20)
DEBUG_NEXT_RECT = pygame.Rect(BASE_WIDTH - 92, 4, 82, 20)

# Toggle button just to the left of the level-jump buttons -- while active,
# attempt_board() skips the money/time affordability gate entirely, so any
# route (including multi-transfer chains) can be boarded freely for testing
# (see GameLogicMixin._toggle_admin_mode/attempt_board).
ADMIN_MODE_RECT = pygame.Rect(BASE_WIDTH - 288, 4, 100, 20)

# -- Random Bus Delay System (Jerusalem traffic theme) -----------------------
# Undocumented on purpose -- not mentioned anywhere in the UI/tutorial. Only
# active in levels 4-5 (LEVELS[3]/LEVELS[4]); see GameLogicMixin._maybe_trigger_delay.
DELAY_EVENTS = [
    ("Protest in the city center!", 3),
    ("Traffic Accident ahead!", 7),
    ("Roadworks on the route!", 5),
]
POPUP_BG = (232, 196, 60)
POPUP_BORDER = (32, 28, 24)
POPUP_TEXT_COLOR = (45, 34, 10)

# -- title screen & end screen -----------------------------------------------
# The title screen is deliberately minimal (title + two buttons) -- the rules
# used to live here as a wall of text, but are now taught interactively by
# the TUTORIAL walkthrough instead (see the "-- tutorial --" section below).
TITLE = "BUS ROUTE ECONOMY"
START_BUTTON_RECT = pygame.Rect(BASE_WIDTH // 2 - 110, 380, 220, 56)
TUTORIAL_BUTTON_RECT = pygame.Rect(BASE_WIDTH // 2 - 110, 452, 220, 50)
RETURN_BUTTON_RECT = pygame.Rect(BASE_WIDTH // 2 - 130, 380, 260, 54)

SORT_FIELDS = ["name", "distance", "duration"]
SORT_LABELS = [
    "Sort by Name (Bubble Sort)",
    "Sort by Distance (Quick Sort)",
    "Sort by Duration (Quick Sort)",
]

# -- tutorial -----------------------------------------------------------------
# The interactive walkthrough (GameGUI's "tutorial" screen_state, see
# game_tutorial.py's TutorialMixin) renders its own small, standalone mock
# scene -- NOT the real map/state -- so it can teach the UI before a real run
# has even started. Every rect below is that mock scene's own layout, in the
# same BASE_WIDTH x BASE_HEIGHT design space as the real game.
TUTORIAL_HIGHLIGHT_COLOR = (255, 214, 40)  # bright gold spotlight border

TUTORIAL_MAP_RECT = pygame.Rect(20, TOP_PANEL_HEIGHT + 10, 760, 270)
TUTORIAL_SIGN_RECT = pygame.Rect(20, TOP_PANEL_HEIGHT + 290, 760, 110)
TUTORIAL_CAPTION_RECT = pygame.Rect(20, TOP_PANEL_HEIGHT + 410, 760, 122)
TUTORIAL_TRIP_TAB_RECT = pygame.Rect(778, 150, 22, 120)
TUTORIAL_TABLE_RECT = pygame.Rect(230, 90, 340, 190)
TUTORIAL_NEXT_BUTTON_RECT = pygame.Rect(640, 536, 120, 38)
TUTORIAL_BEGIN_BUTTON_RECT = pygame.Rect(500, 530, 260, 46)

# 3 sample lines fanning out from a shared HOME to a shared UNIVERSITY, each
# via its own station -- enough to demonstrate line boarding (step 2) and all
# 3 task categories (step 5) without needing any real engine/level data.
TUTORIAL_HOME_POS = (120, 195)
TUTORIAL_UNIVERSITY_POS = (680, 195)
_TUTORIAL_STATION_THINKING = (280, 120)
_TUTORIAL_STATION_AGILITY = (400, 280)
_TUTORIAL_STATION_MEMORY = (540, 140)
TUTORIAL_MOCK_LINES = [
    (ROUTE_COLORS[0], [TUTORIAL_HOME_POS, _TUTORIAL_STATION_THINKING, TUTORIAL_UNIVERSITY_POS]),
    (ROUTE_COLORS[1], [TUTORIAL_HOME_POS, _TUTORIAL_STATION_AGILITY, TUTORIAL_UNIVERSITY_POS]),
    (ROUTE_COLORS[2], [TUTORIAL_HOME_POS, _TUTORIAL_STATION_MEMORY, TUTORIAL_UNIVERSITY_POS]),
]
TUTORIAL_MOCK_STATIONS = [
    (_TUTORIAL_STATION_THINKING, ROUTE_COLORS[0], "thinking"),
    (_TUTORIAL_STATION_AGILITY, ROUTE_COLORS[1], "agility"),
    (_TUTORIAL_STATION_MEMORY, ROUTE_COLORS[2], "memory"),
]

# The 7 sequential walkthrough screens, in order -- text is verbatim UI copy,
# always in English. TutorialMixin drives self.tutorial_step (0-based) through
# this list; each entry's highlighted element(s) are decided by
# TutorialMixin._tutorial_highlight_rects(), keyed by the same step index.
TUTORIAL_STEPS = [
    {
        "text": ("Goal: You are a student trying to reach the university on time for a critical exam "
                 "within your limited budget. Pay close attention to your remaining Time and Cash!"),
    },
    {
        "text": ("Map Navigation: Plan your path carefully. To select and board a bus line, you can "
                 "click directly on the route's path vector layout visualised on the map."),
    },
    {
        "text": ("Bus Dashboard: Keep an eye on Arrival Time, Travel Duration, and Ticket Price. Saved "
                 "money and time carry over as crucial metrics to boost your performance in subsequent "
                 "levels!"),
    },
    {
        "text": ("Trip Planner: Clicking here opens a detailed dashboard for all routes. You can click "
                 "column headers to instantly sort lines by name, duration, or distance. Keep in mind: "
                 "Jerusalem traffic is highly unpredictable! Choosing longer, cross-city routes elevates "
                 "the probability of experiencing unexpected delays."),
    },
    {
        "text": ("Station Tasks: During your journey, you will encounter 3 distinct cognitive task types "
                 "at transit hubs: Thinking, Agility, and Memory. You must successfully conquer these "
                 "challenges to proceed along your bus route."),
    },
    {
        "text": ("Admin Mode: Toggling this feature activates full debugging capabilities. It enables "
                 "skipping tasks entirely, jumping freely between levels, and choosing ANY line from any "
                 "station on the map, regardless of cost, time constraints, or position connectivity."),
    },
    {
        "text": "Are you ready to take on the challenge? Click below to begin your first transit mission!",
    },
]
