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
# Undocumented on purpose -- not mentioned in RULES_TEXT. Only active in
# levels 4-5 (LEVELS[3]/LEVELS[4]); see GameLogicMixin._maybe_trigger_delay.
DELAY_EVENTS = [
    ("Protest in the city center!", 3),
    ("Traffic Accident ahead!", 7),
    ("Roadworks on the route!", 5),
]
POPUP_BG = (232, 196, 60)
POPUP_BORDER = (32, 28, 24)
POPUP_TEXT_COLOR = (45, 34, 10)

# -- title screen & end screen -----------------------------------------------
TITLE = "BUS ROUTE ECONOMY"
RULES_TEXT = (
    "Sort the bus lines with the real C bubble/quick sort algorithms in the Trip Planner, "
    "then board lines to travel from HOME to UNIVERSITY. Every line costs money, and costs "
    "time equal to its wait for the next departure plus its travel duration, so you can only "
    "board a line you can afford and reach on time. Some lines have a station task -- Agility, "
    "Memory, or Thinking -- you must pass along the way. In later levels not every line starts "
    "at HOME -- you'll need to transfer between connecting lines at hub stations to cross the "
    "whole network. Clear all 5 levels to win, but fail a task or run out of time or money and "
    "it's game over."
)
START_BUTTON_RECT = pygame.Rect(BASE_WIDTH // 2 - 110, 440, 220, 56)
RETURN_BUTTON_RECT = pygame.Rect(BASE_WIDTH // 2 - 130, 380, 260, 54)

SORT_FIELDS = ["name", "distance", "duration"]
SORT_LABELS = [
    "Sort by Name (Bubble Sort)",
    "Sort by Distance (Quick Sort)",
    "Sort by Duration (Quick Sort)",
]
