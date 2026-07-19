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

The GUI itself is split across several files to keep any single one a
manageable size:
  - game_constants.py  -- colors, layout rects, copy text.
  - game_geometry.py   -- stateless math/formatting helpers.
  - game_logic.py       -- GameLogicMixin: sorting, the clock, boarding a
                            line (incl. the random delay system), win/loss,
                            debug level-jump, map-hover tracking.
  - game_animation.py   -- AnimationMixin: the bus-driving animation and the
                            traffic-delay popup (both blocking sub-loops).
  - game_map_render.py  -- MapRendererMixin: buildings, roads, and every
                            node icon.
  - game_panels.py      -- PanelsMixin: status bar, electronic sign, Trip
                            Planner, title/end screens.
This file assembles GameGUI from those mixins and owns window setup, the
responsive-scaling helpers, and the top-level event/render loop.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import pygame  # noqa: E402

from engine import routes_from, sort_routes  # noqa: E402
from levels import LEVELS  # noqa: E402
from models import GameState  # noqa: E402

from game_animation import AnimationMixin  # noqa: E402
from game_constants import (  # noqa: E402
    BASE_HEIGHT, BASE_WIDTH, DEBUG_NEXT_RECT, DEBUG_PREV_RECT, LETTERBOX_COLOR, RETURN_BUTTON_RECT, SORT_KEYS,
    STARTING_MONEY, STARTING_TIME, START_BUTTON_RECT, TRIP_PLANNER_MODAL_RECT, TRIP_PLANNER_TAB_RECT, WINDOW_BG,
)
from game_logic import GameLogicMixin  # noqa: E402
from game_map_render import MapRendererMixin  # noqa: E402
from game_panels import PanelsMixin  # noqa: E402


class GameGUI(GameLogicMixin, AnimationMixin, MapRendererMixin, PanelsMixin):
    def __init__(self):
        pygame.init()
        self.fullscreen = False
        self._windowed_size = (BASE_WIDTH, BASE_HEIGHT)
        self.screen = pygame.display.set_mode(self._windowed_size, pygame.RESIZABLE)
        pygame.display.set_caption("Bus Route Economy Game")
        self._font_cache = {}
        self.clock = pygame.time.Clock()
        self._recompute_scale()

        self.route_rows = []  # [(rect, BusRoute), ...] for click handling (real screen space)
        self.trip_planner_tab_rect = self._srect(TRIP_PLANNER_TAB_RECT)
        self.start_button_rect = self._srect(START_BUTTON_RECT)
        self.return_button_rect = self._srect(RETURN_BUTTON_RECT)
        self.debug_prev_rect = self._srect(DEBUG_PREV_RECT)
        self.debug_next_rect = self._srect(DEBUG_NEXT_RECT)

        self._start_new_game()
        self.screen_state = "title"  # "title" | "playing" | "over" -- title overrides the "playing" _start_new_game() sets

    def _start_new_game(self):
        """(Re)initialize a fresh run: starting money/time, Level 1, and all
        transient UI state. Called once from __init__ and again whenever the
        player returns to the main menu, so a new game always starts clean."""
        self.level = LEVELS[0]
        self.state = GameState(money=STARTING_MONEY, time_remaining=STARTING_TIME, current_node=self.level.start)
        self.sort_by = "name"
        self.routes = sort_routes(routes_from(self.level, self.state.current_node), self.sort_by)
        # Every line in the level, not just the ones boardable right now --
        # feeds the Trip Planner modal so the player can see (and plan
        # around) connecting lines before they've transferred to reach them.
        self.all_routes_sorted = sort_routes(self.level.bus_routes, self.sort_by)
        self.message = ""
        self.run_result = None  # "win" | "lose", set once screen_state == "over"

        self.route_rows = []
        self.hovered_route = None  # synchronized between the map and the list
        self.trip_planner_open = False
        self.screen_state = "playing"

        self._check_stuck()

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

    def _font(self, base_size, bold=False, mono=False):
        px = max(8, round(base_size * self.scale))
        key = (px, bold, mono)
        font = self._font_cache.get(key)
        if font is None:
            family = "couriernew" if mono else "arial"
            font = pygame.font.SysFont(family, px, bold=bold)
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

    # -- events ------------------------------------------------------------
    def handle_event(self, event):
        if self.handle_window_event(event):
            return

        if self.screen_state == "title":
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 \
                    and self.start_button_rect.collidepoint(event.pos):
                self.screen_state = "playing"
            return

        if self.screen_state == "over":
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 \
                    and self.return_button_rect.collidepoint(event.pos):
                self._start_new_game()
                self.screen_state = "title"
            return

        # screen_state == "playing" from here on. Debug level-jump buttons
        # work regardless of any other overlay state (Trip Planner, etc.).
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.debug_next_rect.collidepoint(event.pos):
                self._debug_change_level(1)
                return
            if self.debug_prev_rect.collidepoint(event.pos):
                self._debug_change_level(-1)
                return

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 \
                and self.trip_planner_tab_rect.collidepoint(event.pos):
            self.trip_planner_open = not self.trip_planner_open
            return

        if self.trip_planner_open:
            # Sorting (the real C bubble/quick sort) can only be triggered
            # from inside the Trip Planner; everything else is ignored while
            # it's open except closing it.
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.trip_planner_open = False
                elif event.key in SORT_KEYS:
                    self.apply_sort(SORT_KEYS[event.key])
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if not self._srect(TRIP_PLANNER_MODAL_RECT).collidepoint(event.pos):
                    self.trip_planner_open = False
            return

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for rect, route in self.route_rows:
                if rect.collidepoint(event.pos):
                    self.attempt_board(route)
                    return

    def run(self):
        while True:
            dt_ms = self.clock.tick(30)

            for event in pygame.event.get():
                self.handle_event(event)

            if self.screen_state == "playing":
                self.advance_clock(dt_ms / 1000.0)
                self._update_hover()

            if self.screen_state == "title":
                self.draw_title_screen()
            elif self.screen_state == "over":
                self.draw_end_screen()
            else:
                self.screen.fill(LETTERBOX_COLOR)
                pygame.draw.rect(self.screen, WINDOW_BG, self._srect(pygame.Rect(0, 0, BASE_WIDTH, BASE_HEIGHT)))
                self.draw_status_bar()
                self.draw_map()
                self.draw_trip_planner_tab()
                self.draw_bottom_panel()
                if self.trip_planner_open:
                    self.draw_trip_planner_modal()

            pygame.display.flip()


def main():
    GameGUI().run()


if __name__ == "__main__":
    main()
