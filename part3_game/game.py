"""Part C entry point: play the route-economy game in a pygame GUI window.

Backend logic (models.py/levels.py/engine.py) is untouched -- this module
only turns already-computed game state into an interactive 2D window and
translates mouse/keyboard input back into engine calls. Sorting always runs
in the C library via engine.sort_routes(); nothing here reimplements it.

The whole layout is authored in a fixed BASE_WIDTH x BASE_HEIGHT "design
space" and uniformly scaled + letterboxed to whatever the actual window size
is (resizable, and toggleable to fullscreen with F11) -- see _recompute_scale
and the _s*/_font helpers below. minigames.py reuses those same helpers so
the station tasks stay visually consistent when the window is resized.
"""

import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import pygame  # noqa: E402

from engine import board_route, can_board, is_stuck, sort_routes, tick  # noqa: E402
from levels import LEVELS  # noqa: E402
from minigames import run_task  # noqa: E402
from models import GameState  # noqa: E402

STARTING_MONEY = 30
STARTING_TIME = 22.0

# The clock never waits for the player to decide -- it counts down in real
# time regardless of input, on top of whatever duration boarding a line costs.
# 1/60 means 60 real seconds = 1 game-minute, i.e. the clock runs at the same
# pace as a real clock (time_remaining is in minutes; the display renders it
# as MM:SS).
GAME_MINUTES_PER_REAL_SECOND = 1.0 / 60.0

# Design-space resolution. Every layout constant below is authored in this
# coordinate system; _recompute_scale() maps it onto the actual window.
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
OVERLAY_SUCCESS_COLOR = (120, 230, 140)  # bright green, readable on the dark overlay
OVERLAY_FAIL_COLOR = (235, 100, 100)     # bright red, readable on the dark overlay

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

# Soft background patches suggesting public squares / parks / neighborhoods.
# (x_fraction, y_fraction, radius, RGBA) within MAP_RECT.
MAP_PATCHES = [
    (0.18, 0.28, 70, (255, 244, 214, 70)),
    (0.55, 0.55, 92, (198, 228, 198, 55)),
    (0.82, 0.32, 58, (255, 244, 214, 65)),
    (0.35, 0.78, 62, (198, 228, 198, 55)),
]

# Red, Green, Blue, Yellow, Purple -- one per bus line, in level order.
# Darkened slightly from pure primaries so they stay legible on light stone.
ROUTE_COLORS = [
    (200, 30, 30),
    (30, 150, 65),
    (30, 95, 205),
    (205, 165, 20),
    (150, 55, 165),
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

SORT_FIELDS = ["name", "distance", "duration"]
SORT_KEYS = {pygame.K_1: "name", pygame.K_2: "distance", pygame.K_3: "duration"}
SORT_LABELS = [
    "Press 1: Sort by Name (Bubble Sort)",
    "Press 2: Sort by Distance (Quick Sort)",
    "Press 3: Sort by Duration (Quick Sort)",
]


def _lighten(color, amount):
    return tuple(min(255, c + amount) for c in color)


def _darken(color, amount):
    return tuple(max(0, c - amount) for c in color)


def _blend(color_a, color_b, t):
    return tuple(round(a + (b - a) * t) for a, b in zip(color_a, color_b))


def _map_point(row, col, row_range, col_range, rect):
    r0, r1 = row_range
    c0, c1 = col_range
    rr = 0.5 if r1 == r0 else (row - r0) / (r1 - r0)
    cc = 0.5 if c1 == c0 else (col - c0) / (c1 - c0)
    return rect.x + cc * rect.width, rect.y + rr * rect.height


def _route_bounds(level):
    rows = [p[0] for r in level.bus_routes for p in r.path] + [level.start[0], level.end[0]]
    cols = [p[1] for r in level.bus_routes for p in r.path] + [level.start[1], level.end[1]]
    return (min(rows), max(rows)), (min(cols), max(cols))


def _point_segment_distance(p, a, b):
    """Perpendicular distance from point p to the segment a-b (all real
    screen-space (x, y) pairs), used for map hover-detection."""
    px, py = p
    ax, ay = a
    bx, by = b
    dx, dy = bx - ax, by - ay
    if dx == 0 and dy == 0:
        return math.hypot(px - ax, py - ay)
    t = max(0, min(1, ((px - ax) * dx + (py - ay) * dy) / (dx * dx + dy * dy)))
    return math.hypot(px - (ax + t * dx), py - (ay + t * dy))


def _interpolate_path(points, t):
    """Arc-length-parameterized position at fraction t (0..1) along a
    polyline. points/return value are in the same coordinate space (BASE or
    screen, caller's choice) -- used to animate the bus at a constant speed
    regardless of how uneven the path's segment lengths are."""
    if len(points) == 1:
        return points[0]
    seg_lengths = [math.hypot(b[0] - a[0], b[1] - a[1]) for a, b in zip(points, points[1:])]
    total = sum(seg_lengths)
    if total == 0:
        return points[0]
    target = max(0.0, min(1.0, t)) * total
    acc = 0.0
    for (a, b), seg_len in zip(zip(points, points[1:]), seg_lengths):
        if seg_len == 0:
            continue
        if acc + seg_len >= target:
            local_t = (target - acc) / seg_len
            return (a[0] + (b[0] - a[0]) * local_t, a[1] + (b[1] - a[1]) * local_t)
        acc += seg_len
    return points[-1]


class GameGUI:
    def __init__(self):
        pygame.init()
        self.fullscreen = False
        self._windowed_size = (BASE_WIDTH, BASE_HEIGHT)
        self.screen = pygame.display.set_mode(self._windowed_size, pygame.RESIZABLE)
        pygame.display.set_caption("Bus Route Economy Game")
        self._font_cache = {}
        self.clock = pygame.time.Clock()
        self._recompute_scale()

        self.state = GameState(money=STARTING_MONEY, time_remaining=STARTING_TIME)
        self.level = LEVELS[self.state.level_index]
        self.sort_by = "name"
        self.routes = sort_routes(self.level, self.sort_by)
        self.message = ""
        self.game_over_text = None  # (text, color) once the run ends

        self.route_rows = []  # [(rect, BusRoute), ...] for click handling (real screen space)
        self.button_rows = []  # [(rect, sort_field), ...] for click handling (real screen space)
        self.hovered_route = None  # synchronized between the map and the list

        self._check_stuck()

    def _route_color(self, route):
        """Each route's color is tied to its position in level.bus_routes
        (its identity), not its position in the currently-sorted self.routes
        list, so a line's color stays the same no matter how it's sorted."""
        idx = self.level.bus_routes.index(route)
        return ROUTE_COLORS[idx % len(ROUTE_COLORS)]

    # -- responsive scaling ---------------------------------------------------
    def _recompute_scale(self):
        w, h = self.screen.get_size()
        self.window_width, self.window_height = w, h
        self.scale = min(w / BASE_WIDTH, h / BASE_HEIGHT)
        self.offset_x = (w - BASE_WIDTH * self.scale) / 2
        self.offset_y = (h - BASE_HEIGHT * self.scale) / 2

    def _spt(self, point):
        x, y = point
        return (self.offset_x + x * self.scale, self.offset_y + y * self.scale)

    def _slen(self, value):
        return max(1, round(value * self.scale))

    def _srect(self, rect):
        x, y = self._spt((rect.x, rect.y))
        return pygame.Rect(x, y, rect.width * self.scale, rect.height * self.scale)

    def _font(self, base_size, bold=False):
        px = max(8, round(base_size * self.scale))
        key = (px, bold)
        font = self._font_cache.get(key)
        if font is None:
            font = pygame.font.SysFont("arial", px, bold=bold)
            self._font_cache[key] = font
        return font

    def toggle_fullscreen(self):
        self.fullscreen = not self.fullscreen
        if self.fullscreen:
            self._windowed_size = self.screen.get_size()
            self.screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
        else:
            self.screen = pygame.display.set_mode(self._windowed_size, pygame.RESIZABLE)
        self._recompute_scale()

    def handle_window_event(self, event):
        """Handle QUIT/resize/fullscreen-toggle. Shared by the main loop and
        by the mini-game sub-loops so window handling stays consistent
        everywhere. Returns True if the event was a window-management event."""
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit(0)
        if event.type == pygame.VIDEORESIZE and not self.fullscreen:
            self.screen = pygame.display.set_mode((event.w, event.h), pygame.RESIZABLE)
            self._recompute_scale()
            return True
        if event.type == pygame.KEYDOWN and event.key == pygame.K_F11:
            self.toggle_fullscreen()
            return True
        return False

    # -- state transitions ---------------------------------------------------
    def apply_sort(self, sort_by):
        self.sort_by = sort_by
        self.routes = sort_routes(self.level, sort_by)
        self.message = ""

    def attempt_board(self, route):
        if not can_board(self.state, route):
            self.message = f"Can't board {route.name}: check money/time."
            return

        # Highlight the boarding route on the map/list for the whole sequence.
        self.hovered_route = route
        color = self._route_color(route)
        station_idx = route.path.index(route.station)

        # Phase 1: drive from HOME to the station, then the station's mini-game
        # gates boarding -- money/time affordability alone isn't enough, the
        # player must also clear the cognitive task tied to that stop.
        self._animate_bus(route.path[:station_idx + 1], color)
        if not run_task(route.task_type, self):
            self.game_over_text = (
                f"GAME OVER! Failed the station task on {route.name}.",
                OVERLAY_FAIL_COLOR,
            )
            return

        # Phase 2: drive from the station on to UNIVERSITY.
        self._animate_bus(route.path[station_idx:], color)

        self.state = board_route(self.state, self.level, route)
        self.message = (
            f"Boarded {route.name}! Level cleared. "
            f"+{self.level.reward_money} NIS, +{self.level.reward_time} time."
        )

        if self.state.level_index >= len(LEVELS):
            self.game_over_text = ("SUCCESS! Target Reached", OVERLAY_SUCCESS_COLOR)
            return

        self.level = LEVELS[self.state.level_index]
        self.routes = sort_routes(self.level, self.sort_by)
        self._check_stuck()

    def _check_stuck(self):
        if self.game_over_text is None and is_stuck(self.state, self.level):
            self.game_over_text = (
                "GAME OVER! No remaining bus line is both affordable and on time.",
                OVERLAY_FAIL_COLOR,
            )

    def _update_hover(self):
        """Recompute which route (if any) the mouse is over -- either its row
        in the bottom panel or its road on the map -- so draw_map() and
        draw_bottom_panel() can render a synchronized highlight this frame.
        Uses route_rows from the previous frame, which is fine since the
        list layout is stable across frames."""
        mouse_pos = pygame.mouse.get_pos()

        for rect, route in self.route_rows:
            if rect.collidepoint(mouse_pos):
                self.hovered_route = route
                return

        row_range, col_range = _route_bounds(self.level)
        threshold = self._slen(9)
        for route in self.level.bus_routes:
            points = [self._spt(_map_point(r, c, row_range, col_range, MAP_CONTENT_RECT)) for r, c in route.path]
            for a, b in zip(points, points[1:]):
                if _point_segment_distance(mouse_pos, a, b) <= threshold:
                    self.hovered_route = route
                    return

        self.hovered_route = None

    # -- bus driving animation ------------------------------------------------
    def _draw_bus_icon(self, cx, cy, color):
        w, h = self._slen(15), self._slen(9)
        body = pygame.Rect(cx - w / 2, cy - h / 2, w, h)
        pygame.draw.rect(self.screen, (245, 245, 240), body, border_radius=self._slen(2))
        pygame.draw.rect(self.screen, OUTLINE_COLOR, body, max(1, self._slen(1.5)), border_radius=self._slen(2))
        stripe = pygame.Rect(body.x, body.y + body.height * 0.55, body.width, body.height * 0.3)
        pygame.draw.rect(self.screen, color, stripe)
        wheel_r = max(1, self._slen(1.8))
        pygame.draw.circle(self.screen, OUTLINE_COLOR, (body.x + w * 0.22, body.bottom), wheel_r)
        pygame.draw.circle(self.screen, OUTLINE_COLOR, (body.x + w * 0.78, body.bottom), wheel_r)

    def _animate_bus(self, base_path, color, duration=1.1):
        """Blocking sub-loop (same pattern as the mini-games) that drives a
        bus icon smoothly along base_path (BASE-space route.path points) in
        real time, redrawing the full frame every tick. Does not touch
        GameState -- the clock is effectively paused during this, exactly
        like it already is during a station mini-game."""
        if len(base_path) < 2:
            return
        row_range, col_range = _route_bounds(self.level)
        base_points = [_map_point(r, c, row_range, col_range, MAP_CONTENT_RECT) for r, c in base_path]

        elapsed = 0.0
        while elapsed < duration:
            dt = self.clock.tick(60) / 1000.0
            elapsed += dt

            for event in pygame.event.get():
                self.handle_window_event(event)

            pos = _interpolate_path(base_points, elapsed / duration)

            self.screen.fill(LETTERBOX_COLOR)
            pygame.draw.rect(self.screen, WINDOW_BG, self._srect(pygame.Rect(0, 0, BASE_WIDTH, BASE_HEIGHT)))
            self.draw_status_bar()
            self.draw_map()
            self.draw_bottom_panel()
            self._draw_bus_icon(*self._spt(pos), color)
            pygame.display.flip()

    # -- drawing: pseudo-3D primitives ---------------------------------------
    def _draw_ground_shadow(self, x, y, w, h):
        pts = [self._spt(p) for p in [
            (x - 2, y + h), (x + w + 4, y + h), (x + w + 8, y + h + 5), (x - 6, y + h + 5),
        ]]
        pygame.draw.polygon(self.screen, SHADOW_COLOR, pts)

    def _draw_window(self, x, y, size):
        pts = [self._spt(p) for p in [(x, y), (x + size, y), (x + size, y + size), (x, y + size)]]
        pygame.draw.polygon(self.screen, WINDOW_GLASS_COLOR, pts)
        pygame.draw.polygon(self.screen, WINDOW_FRAME_COLOR, pts, max(1, self._slen(1.5)))
        mullion_w = max(1, self._slen(1))
        pygame.draw.line(self.screen, WINDOW_FRAME_COLOR,
                          self._spt((x + size / 2, y)), self._spt((x + size / 2, y + size)), mullion_w)
        pygame.draw.line(self.screen, WINDOW_FRAME_COLOR,
                          self._spt((x, y + size / 2)), self._spt((x + size, y + size / 2)), mullion_w)
        pygame.draw.polygon(self.screen, OUTLINE_COLOR, pts, max(1, self._slen(1)))

    def _draw_block_3d(self, base_rect, base_color, depth=6, windows=0, roof_unit=False):
        """A simple pseudo-isometric block: front face + lighter roof face +
        darker side face, all outlined in a shared ink color, with a ground
        shadow, optional framed windows, and a roof-mounted cooling unit.
        base_rect/depth are in BASE coordinates."""
        x, y, w, h = base_rect.x, base_rect.y, base_rect.width, base_rect.height
        dx = dy = depth

        self._draw_ground_shadow(x, y, w, h)

        front = [(x, y), (x + w, y), (x + w, y + h), (x, y + h)]
        roof = [(x, y), (x + w, y), (x + w + dx, y - dy), (x + dx, y - dy)]
        side = [(x + w, y), (x + w + dx, y - dy), (x + w + dx, y - dy + h), (x + w, y + h)]

        front_pts = [self._spt(p) for p in front]
        roof_pts = [self._spt(p) for p in roof]
        side_pts = [self._spt(p) for p in side]
        line_w = self._slen(2.5)

        pygame.draw.polygon(self.screen, _darken(base_color, 60), side_pts)
        pygame.draw.polygon(self.screen, _lighten(base_color, 55), roof_pts)
        pygame.draw.polygon(self.screen, base_color, front_pts)
        pygame.draw.polygon(self.screen, OUTLINE_COLOR, side_pts, line_w)
        pygame.draw.polygon(self.screen, OUTLINE_COLOR, roof_pts, line_w)
        pygame.draw.polygon(self.screen, OUTLINE_COLOR, front_pts, line_w)

        if windows:
            wsize = min(w, h) * 0.22
            margin = wsize * 0.9
            usable = w - 2 * margin
            step = usable / windows if windows > 1 else 0
            wy = y + h * 0.30
            for i in range(windows):
                self._draw_window(x + margin + i * step, wy, wsize)

        if roof_unit:
            ux, uy = x + w * 0.55, y - dy * 0.65
            usize = w * 0.22
            unit_pts = [self._spt(p) for p in [
                (ux, uy), (ux + usize, uy), (ux + usize, uy + usize * 0.55), (ux, uy + usize * 0.55),
            ]]
            pygame.draw.polygon(self.screen, _darken(base_color, 70), unit_pts)
            pygame.draw.polygon(self.screen, OUTLINE_COLOR, unit_pts, max(1, self._slen(1.5)))
            grille = self._spt((ux + usize * 0.5, uy + usize * 0.28))
            pygame.draw.circle(self.screen, OUTLINE_COLOR, grille, max(1, self._slen(1.6)))

    # -- drawing: map -----------------------------------------------------------
    def _draw_map_texture(self):
        map_screen_rect = self._srect(MAP_RECT)
        overlay = pygame.Surface((max(1, round(map_screen_rect.width)),
                                   max(1, round(map_screen_rect.height))), pygame.SRCALPHA)
        for xf, yf, radius, color in MAP_PATCHES:
            cx = xf * MAP_RECT.width * self.scale
            cy = yf * MAP_RECT.height * self.scale
            pygame.draw.circle(overlay, color, (cx, cy), radius * self.scale)
        self.screen.blit(overlay, (map_screen_rect.x, map_screen_rect.y))

    def _draw_city_blocks(self):
        for i, (xf, yf, w, h, roof_unit) in enumerate(BUILDING_LAYOUT):
            cx = MAP_RECT.x + xf * MAP_RECT.width
            cy = MAP_RECT.y + yf * MAP_RECT.height
            base_rect = pygame.Rect(cx - w / 2, cy - h / 2, w, h)
            color = BUILDING_COLORS[i % len(BUILDING_COLORS)]
            self._draw_block_3d(base_rect, color, depth=5, windows=1, roof_unit=roof_unit)

    def _draw_home_icon(self, pos):
        x, y = pos
        base_w, base_h, depth = 26, 18, 5
        base_rect = pygame.Rect(x - base_w / 2, y - base_h / 2, base_w, base_h)
        self._draw_block_3d(base_rect, HOUSE_WALL_COLOR, depth=depth, windows=1)

        # door with a small green awning above it
        door_w, door_h = base_w * 0.22, base_h * 0.55
        door_x, door_y = x - door_w / 2, y + base_h / 2 - door_h
        door_pts = [self._spt(p) for p in [
            (door_x, door_y), (door_x + door_w, door_y),
            (door_x + door_w, door_y + door_h), (door_x, door_y + door_h),
        ]]
        pygame.draw.polygon(self.screen, HOUSE_DOOR_COLOR, door_pts)
        pygame.draw.polygon(self.screen, OUTLINE_COLOR, door_pts, max(1, self._slen(1.2)))

        awning_pts = [self._spt(p) for p in [
            (door_x - 2, door_y - 3), (door_x + door_w + 2, door_y - 3),
            (door_x + door_w, door_y), (door_x, door_y),
        ]]
        pygame.draw.polygon(self.screen, HOUSE_AWNING_COLOR, awning_pts)
        pygame.draw.polygon(self.screen, OUTLINE_COLOR, awning_pts, max(1, self._slen(1)))

        roof_points = [
            (x - base_w / 2 - depth - 4, y - base_h / 2),
            (x + base_w / 2 + depth + 4, y - base_h / 2),
            (x + base_w / 2, y - base_h / 2 - 18),
            (x - base_w / 2, y - base_h / 2 - 18),
        ]
        roof_pts = [self._spt(p) for p in roof_points]
        pygame.draw.polygon(self.screen, HOUSE_ROOF_COLOR, roof_pts)
        pygame.draw.polygon(self.screen, OUTLINE_COLOR, roof_pts, self._slen(2.5))

        label = self._font(14, bold=True).render("HOME", True, TEXT_COLOR)
        lx, ly = self._spt((x, y + base_h / 2 + depth + 14))
        self.screen.blit(label, label.get_rect(center=(lx, ly)))

    def _draw_university_icon(self, pos):
        x, y = pos
        widths = [22, 34, 22]
        heights = [34, 50, 30]
        total_w = sum(widths) + 8
        cx = x - total_w / 2
        for i, (w, h) in enumerate(zip(widths, heights)):
            base_rect = pygame.Rect(cx, y - h, w, h)
            self._draw_block_3d(base_rect, UNIVERSITY_BUILDING_COLOR, depth=6, windows=3 if i == 1 else 2)
            cx += w + 4

        label = self._font(14, bold=True).render("UNIVERSITY", True, TEXT_COLOR)
        lx, ly = self._spt((x, y + 14))
        self.screen.blit(label, label.get_rect(center=(lx, ly)))

    def _draw_station_icon(self, cx, cy, r, task_type):
        """A tiny task-specific glyph drawn inside the station's colored
        core, in a bright contrasting color: a lightning bolt (agility),
        a 2x2 grid (memory), or a gear (thinking)."""
        icon_color = (250, 250, 248)
        if task_type == "agility":
            s = r * 0.9
            pts = [
                (cx - 0.10 * s, cy - s), (cx + 0.45 * s, cy - 0.05 * s), (cx + 0.05 * s, cy - 0.05 * s),
                (cx + 0.20 * s, cy + s), (cx - 0.45 * s, cy + 0.15 * s), (cx - 0.05 * s, cy + 0.15 * s),
            ]
            pygame.draw.polygon(self.screen, icon_color, pts)
            pygame.draw.polygon(self.screen, OUTLINE_COLOR, pts, max(1, round(self._slen(1) * 0.6)))
        elif task_type == "memory":
            size = r * 1.1
            rect = pygame.Rect(cx - size / 2, cy - size / 2, size, size)
            line_w = max(1, self._slen(1.6))
            pygame.draw.rect(self.screen, icon_color, rect, line_w, border_radius=max(1, round(line_w * 0.4)))
            pygame.draw.line(self.screen, icon_color, (cx, rect.top + line_w), (cx, rect.bottom - line_w), line_w)
            pygame.draw.line(self.screen, icon_color, (rect.left + line_w, cy), (rect.right - line_w, cy), line_w)
        elif task_type == "thinking":
            gear_r = r * 0.72
            line_w = max(1, self._slen(1.4))
            for i in range(8):
                angle = math.radians(i * 45)
                x1 = cx + gear_r * 0.75 * math.cos(angle)
                y1 = cy + gear_r * 0.75 * math.sin(angle)
                x2 = cx + gear_r * 1.3 * math.cos(angle)
                y2 = cy + gear_r * 1.3 * math.sin(angle)
                pygame.draw.line(self.screen, icon_color, (x1, y1), (x2, y2), line_w)
            pygame.draw.circle(self.screen, icon_color, (cx, cy), gear_r, line_w)
            pygame.draw.circle(self.screen, icon_color, (cx, cy), gear_r * 0.35, line_w)

    def _draw_station(self, pos, color, task_type):
        """A layered "puck" button, matching the level-select node style:
        ground shadow -> thick dark outline -> metallic stone rim (with a
        light/dark crescent for a curved-edge look) -> recessed dish ->
        light inner face -> colored core (this route's identity) -> a
        task-specific glyph identifying the mini-game waiting at this stop."""
        cx, cy = self._spt(pos)
        r_shadow = self._slen(13.5)
        r_outline = self._slen(13)
        r_rim = self._slen(11.5)
        r_dish = self._slen(8.5)
        r_face = self._slen(6.5)
        r_core = self._slen(5)
        shadow_off = self._slen(2.5)

        pygame.draw.circle(self.screen, SHADOW_COLOR, (cx + shadow_off, cy + shadow_off * 1.4), r_shadow)
        pygame.draw.circle(self.screen, OUTLINE_COLOR, (cx, cy), r_outline)
        pygame.draw.circle(self.screen, (198, 196, 190), (cx, cy), r_rim)
        pygame.draw.circle(self.screen, (150, 148, 142), (cx + r_rim * 0.28, cy + r_rim * 0.28), r_rim * 0.85)
        pygame.draw.circle(self.screen, (228, 226, 220), (cx - r_rim * 0.22, cy - r_rim * 0.22), r_rim * 0.78)
        pygame.draw.circle(self.screen, (118, 116, 112), (cx, cy), r_dish)
        pygame.draw.circle(self.screen, (240, 238, 232), (cx, cy), r_face)
        pygame.draw.circle(self.screen, color, (cx, cy), r_core)
        pygame.draw.circle(self.screen, OUTLINE_COLOR, (cx, cy), r_core, max(1, self._slen(1)))
        self._draw_station_icon(cx, cy, r_core, task_type)

    def _draw_thick_polyline(self, points, color, width):
        """pygame.draw.lines leaves gaps at sharp joints for thick strokes;
        stamp a circle at every vertex to keep corners looking solid."""
        if len(points) < 2:
            return
        pygame.draw.lines(self.screen, color, False, points, width)
        for p in points:
            pygame.draw.circle(self.screen, color, p, width / 2)

    def draw_map(self):
        pygame.draw.rect(self.screen, MAP_BG, self._srect(MAP_RECT), border_radius=self._slen(6))
        self._draw_map_texture()

        row_range, col_range = _route_bounds(self.level)
        route_points = [
            [self._spt(_map_point(r, c, row_range, col_range, MAP_CONTENT_RECT)) for r, c in route.path]
            for route in self.level.bus_routes
        ]

        # Roads: thick dark outline, a light stone-cream edge trim, a dark
        # asphalt body, then the colored transit line on top of each --
        # a bordered street bed with a crisp highlighted edge, not one flat line.
        outline_w = self._slen(15)
        edge_w = self._slen(12)
        fill_w = self._slen(8)
        route_w = self._slen(3)
        route_w_hover = self._slen(6)
        for points in route_points:
            self._draw_thick_polyline(points, ROAD_OUTLINE, outline_w)
        for points in route_points:
            self._draw_thick_polyline(points, ROAD_EDGE, edge_w)
        for points in route_points:
            self._draw_thick_polyline(points, ROAD_FILL, fill_w)

        # The hovered/selected line is drawn thicker and brighter; the other
        # 4 fade toward the road color so the highlighted one stands out.
        for i, (points, route) in enumerate(zip(route_points, self.level.bus_routes)):
            base_color = ROUTE_COLORS[i % len(ROUTE_COLORS)]
            if self.hovered_route is None:
                color, width = base_color, route_w
            elif route is self.hovered_route:
                color, width = _lighten(base_color, 50), route_w_hover
            else:
                color, width = _blend(base_color, ROAD_FILL, 0.55), route_w
            self._draw_thick_polyline(points, color, width)

        self._draw_city_blocks()

        # Station signposts, one per route, colored + iconed to match that route.
        for i, route in enumerate(self.level.bus_routes):
            station_pos = _map_point(*route.station, row_range, col_range, MAP_CONTENT_RECT)
            self._draw_station(station_pos, ROUTE_COLORS[i % len(ROUTE_COLORS)], route.task_type)

        home_pos = _map_point(*self.level.start, row_range, col_range, MAP_CONTENT_RECT)
        uni_pos = _map_point(*self.level.end, row_range, col_range, MAP_CONTENT_RECT)
        self._draw_home_icon(home_pos)
        self._draw_university_icon(uni_pos)

    # -- drawing: panels ----------------------------------------------------
    def draw_status_bar(self):
        bar_rect = pygame.Rect(0, 0, BASE_WIDTH, TOP_PANEL_HEIGHT)
        pygame.draw.rect(self.screen, PANEL_BG, self._srect(bar_rect))
        total_seconds = max(0, round(self.state.time_remaining * 60))
        minutes, seconds = divmod(total_seconds, 60)
        text = f"CASH: {self.state.money} NIS  |  TIME: {minutes:02d}:{seconds:02d}"
        pos = self._spt((20, 12))
        self.screen.blit(self._font(22, bold=True).render(text, True, TEXT_COLOR), pos)

        hint = self._font(13).render("F11: toggle fullscreen", True, DIM_TEXT_COLOR)
        hpos = self._spt((BASE_WIDTH - 160, 18))
        self.screen.blit(hint, hpos)

    def draw_bottom_panel(self):
        pygame.draw.rect(self.screen, PANEL_BG, self._srect(BOTTOM_PANEL_RECT), border_radius=self._slen(6))
        x = BOTTOM_PANEL_RECT.x + 15
        y = BOTTOM_PANEL_RECT.y + 10

        self.button_rows = []
        for label, field in zip(SORT_LABELS, SORT_FIELDS):
            color = AFFORD_COLOR if self.sort_by == field else TEXT_COLOR
            surf = self._font(18).render(label, True, color)
            pos = self._spt((x, y))
            rect = pygame.Rect(pos[0], pos[1], surf.get_width(), surf.get_height())
            self.button_rows.append((rect, field))
            self.screen.blit(surf, pos)
            y += 24

        y += 10
        self.screen.blit(self._font(22, bold=True).render("--- AVAILABLE BUS LINES ---", True, TEXT_COLOR),
                          self._spt((x, y)))
        y += 22
        note = self._font(18).render("(Boarding triggers that line's station task -- fail it and it's game over.)",
                                      True, DIM_TEXT_COLOR)
        self.screen.blit(note, self._spt((x, y)))
        y += 26

        self.route_rows = []
        row_height = 22
        for i, r in enumerate(self.routes, start=1):
            fits = self.state.money >= r.price and self.state.time_remaining >= r.duration
            is_hovered = r is self.hovered_route
            # Only flag lines that can no longer be taken -- no hint for which
            # one is "best", the player has to weigh cost/duration themselves.
            color = TEXT_COLOR if fits else DENY_COLOR

            # Fixed-size click zone (independent of text/bold width) kept in
            # sync with the map: hovering this row or that line's road both
            # set self.hovered_route the same way.
            row_rect = pygame.Rect(BOTTOM_PANEL_RECT.x + 8, y - 2, BOTTOM_PANEL_RECT.width - 16, row_height)
            self.route_rows.append((self._srect(row_rect), r))

            if is_hovered:
                pygame.draw.rect(self.screen, _lighten(PANEL_BG, 18), self._srect(row_rect),
                                  border_radius=self._slen(4))
                tri = [self._spt(p) for p in [(x, y + 1), (x, y + 15), (x + 9, y + 8)]]
                pygame.draw.polygon(self.screen, self._route_color(r), tri)

            text = (f"[{i}] {r.name} (Dist: {r.distance}km, Dur: {r.duration}min, "
                    f"Freq: {r.frequency}/day, Price: {r.price} NIS)")
            surf = self._font(18, bold=is_hovered).render(text, True, color)
            self.screen.blit(surf, self._spt((x + 16, y)))
            y += row_height

        if self.message:
            surf = self._font(18).render(self.message, True, DIM_TEXT_COLOR)
            self.screen.blit(surf, self._spt((x, BOTTOM_PANEL_RECT.bottom - 26)))

    @staticmethod
    def _wrap_text(text, font, max_width):
        words = text.split(" ")
        lines = []
        current = ""
        for word in words:
            candidate = f"{current} {word}".strip()
            if font.size(candidate)[0] <= max_width or not current:
                current = candidate
            else:
                lines.append(current)
                current = word
        if current:
            lines.append(current)
        return lines

    def draw_overlay(self):
        if not self.game_over_text:
            return
        text, color = self.game_over_text

        overlay = pygame.Surface((self.window_width, self.window_height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 190))
        self.screen.blit(overlay, (0, 0))

        font_big = self._font(34, bold=True)
        max_width = (BASE_WIDTH - 80) * self.scale
        lines = self._wrap_text(text, font_big, max_width)
        line_height = font_big.get_linesize()
        cx, cy = self.window_width // 2, self.window_height // 2
        top = cy - (len(lines) * line_height) // 2

        for i, line in enumerate(lines):
            surf = font_big.render(line, True, color)
            self.screen.blit(surf, surf.get_rect(center=(cx, top + i * line_height)))

        hint = self._font(18).render("Close the window to exit.", True, (230, 230, 230))
        hint_y = top + len(lines) * line_height + 20
        self.screen.blit(hint, hint.get_rect(center=(cx, hint_y)))

    # -- events ------------------------------------------------------------
    def handle_event(self, event):
        if self.handle_window_event(event):
            return
        if self.game_over_text is not None:
            return
        if event.type == pygame.KEYDOWN and event.key in SORT_KEYS:
            self.apply_sort(SORT_KEYS[event.key])
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for rect, field in self.button_rows:
                if rect.collidepoint(event.pos):
                    self.apply_sort(field)
                    return
            for rect, route in self.route_rows:
                if rect.collidepoint(event.pos):
                    self.attempt_board(route)
                    return

    def run(self):
        while True:
            dt_ms = self.clock.tick(30)

            for event in pygame.event.get():
                self.handle_event(event)

            if self.game_over_text is None:
                elapsed_minutes = (dt_ms / 1000.0) * GAME_MINUTES_PER_REAL_SECOND
                self.state = tick(self.state, elapsed_minutes)
                self._check_stuck()

            self._update_hover()

            self.screen.fill(LETTERBOX_COLOR)
            pygame.draw.rect(self.screen, WINDOW_BG, self._srect(pygame.Rect(0, 0, BASE_WIDTH, BASE_HEIGHT)))
            self.draw_status_bar()
            self.draw_map()
            self.draw_bottom_panel()
            self.draw_overlay()
            pygame.display.flip()


def main():
    GameGUI().run()


if __name__ == "__main__":
    main()
