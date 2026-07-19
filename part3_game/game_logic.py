"""State-transition logic for the Part C route-economy game's GUI: sorting,
the real-time clock, boarding a line (including the Random Bus Delay System),
win/loss detection, the debug level-jump buttons, Admin Mode (bypasses the
money/time boarding gate for testing), and map-hover tracking.

GameLogicMixin is combined with the other *Mixin classes into game.py's
GameGUI; every method here still just uses `self` as if it were defined
directly on GameGUI -- Python resolves `self.<anything>` against the whole
composed instance regardless of which file a method was defined in.
"""

import random
from dataclasses import replace

import pygame

from engine import (
    board_route, can_board, enter_level, is_stuck, next_bus_minutes, routes_from, sort_routes, tick,
)
from levels import LEVELS
from minigames import run_task, show_level_summary

from game_constants import DELAY_EVENTS, GAME_MINUTES_PER_REAL_SECOND, LINE_LABELS, MAP_CONTENT_RECT, ROUTE_COLORS
from game_geometry import map_point, node_label, point_segment_distance, route_bounds


class GameLogicMixin:
    def _route_color(self, route):
        """Each route's color is tied to its position in level.bus_routes
        (its identity), not its position in the currently-sorted self.routes
        list, so a line's color stays the same no matter how it's sorted."""
        idx = self.level.bus_routes.index(route)
        return ROUTE_COLORS[idx % len(ROUTE_COLORS)]

    def _route_label(self, route):
        """Display label ("Red Line", ...) for a route, aligned with its
        color via the same level.bus_routes index."""
        idx = self.level.bus_routes.index(route)
        return LINE_LABELS[idx % len(LINE_LABELS)]

    # -- state transitions ---------------------------------------------------
    def apply_sort(self, sort_by):
        self.sort_by = sort_by
        self.routes = sort_routes(routes_from(self.level, self.state.current_node), sort_by)
        self.all_routes_sorted = sort_routes(self.level.bus_routes, sort_by)
        self.message = ""

    def advance_clock(self, dt_seconds):
        """Decay time_remaining by dt_seconds of real time. Called every
        frame from run(), and also from inside the blocking mini-game and
        bus-animation sub-loops (via minigames.py's gui.advance_clock) so the
        clock never pauses just because a task or animation has taken over
        the screen -- only leaving the "playing" state stops it."""
        if self.screen_state == "playing":
            elapsed_minutes = dt_seconds * GAME_MINUTES_PER_REAL_SECOND
            self.state = tick(self.state, elapsed_minutes)
            self._check_stuck()

    def _trigger_game_over(self, result):
        """End the current run: result is "win" or "lose". The end screen is
        deliberately text-free beyond a single word (see draw_end_screen) --
        no per-cause explanation is shown, so callers don't need one either."""
        self.run_result = result
        self.screen_state = "over"

    def attempt_board(self, route):
        if not self.admin_mode and not can_board(self.state, route):
            self.message = f"Can't board {self._route_label(route)}: check money/time."
            return

        # Highlight the boarding route on the map/list for the whole sequence.
        self.hovered_route = route
        color = self._route_color(route)

        if route.station is None:
            # No intermediate station or mini-game on this hop (levels 1 and
            # 3-5) -- drive straight from its origin to its destination.
            self._animate_bus(route.path, color)
            if self.screen_state != "playing":
                return
        else:
            station_idx = route.path.index(route.station)

            # Phase 1: drive from the origin to the station, then the
            # station's mini-game gates boarding -- money/time affordability
            # alone isn't enough, the player must also clear the cognitive
            # task tied to that stop (level 2 only). The clock keeps ticking
            # throughout both phases and the task itself, so a slow player
            # can still run out of time mid-sequence.
            self._animate_bus(route.path[:station_idx + 1], color)
            if self.screen_state != "playing":
                return

            if not run_task(route.task_type, self):
                if self.screen_state == "playing":
                    self._trigger_game_over("lose")
                return

            # Phase 2: drive from the station on to the destination.
            self._animate_bus(route.path[station_idx:], color)
            if self.screen_state != "playing":
                return

        # Re-check right before actually deducting: the wait-for-next-bus
        # component of the cost can grow while the animation/task above was
        # playing out, so a boarding that was valid on click can still fail.
        # Admin Mode skips this gate entirely, same as the initial check above.
        if not self.admin_mode and not can_board(self.state, route):
            self._trigger_game_over("lose")
            return

        reached_end = route.destination == self.level.end
        cleared_level = self.level
        # Captured now, while self.level still is cleared_level -- _route_label
        # looks the route up by position in self.level.bus_routes, which would
        # raise once self.level moves on to the next level below.
        boarded_label = self._route_label(route)
        self.state = board_route(self.state, self.level, route, bypass_checks=self.admin_mode)

        # Random Bus Delay System (Jerusalem traffic theme) -- undocumented
        # mechanic active only in the busier Advanced Grid Expansion levels
        # (4 and 5). A blocking popup, same pattern as the mini-games/bus
        # animation; the clock keeps ticking while it's up.
        if cleared_level in (LEVELS[3], LEVELS[4]):
            self._maybe_trigger_delay(cleared_level, route)
            if self.screen_state != "playing":
                return

        if reached_end:
            if self.state.level_index >= len(LEVELS):
                self._trigger_game_over("win")
                return

            # Advance to the new level/position *before* the summary screen,
            # so its own advance_clock()-driven stuck-check (dawdling on
            # "PROCEED TO NEXT LEVEL" still costs real time) evaluates the
            # level the player is actually about to play, not the one they
            # just left (whose end node has no outgoing routes at all).
            self.level = LEVELS[self.state.level_index]
            self.state = enter_level(self.state, self.level)

            show_level_summary(self, self.state.level_index)
            if self.screen_state != "playing":
                return

            self.message = (
                f"Boarded {boarded_label}! Level cleared. "
                f"+{cleared_level.reward_money} NIS, +{cleared_level.reward_time} time."
            )
        else:
            self.message = (
                f"Boarded {boarded_label}! Now at {node_label(self.state.current_node)} "
                f"-- find a connecting line."
            )

        self.routes = sort_routes(routes_from(self.level, self.state.current_node), self.sort_by)
        self.all_routes_sorted = sort_routes(self.level.bus_routes, self.sort_by)
        self._check_stuck()

    def _maybe_trigger_delay(self, level, route):
        """P(delay) = route.distance / total distance of every line in the
        level -- a longer line boarded has a proportionally higher chance of
        a random city-traffic event tacking extra minutes onto the trip, on
        top of the normal wait+duration cost. Only called for levels 4-5."""
        total_distance = sum(r.distance for r in level.bus_routes)
        probability = route.distance / total_distance if total_distance else 0.0
        if random.random() >= probability:
            return
        event_name, minutes = random.choice(DELAY_EVENTS)
        self.state = replace(self.state, time_remaining=max(0.0, self.state.time_remaining - minutes))
        self._show_popup(f"{event_name} - {minutes} minutes delay")
        self._check_stuck()

    def _check_stuck(self):
        if self.admin_mode:
            return
        if self.screen_state == "playing" and is_stuck(self.state, self.level):
            self._trigger_game_over("lose")

    def _toggle_admin_mode(self):
        """Developer-only: flip the ADMIN MODE flag. While active,
        attempt_board() skips both money/time affordability checks and
        _check_stuck()'s lose-by-stranded detection, so any route --
        including multi-transfer chains -- can be boarded freely regardless
        of remaining time or cash, for testing routing in isolation."""
        self.admin_mode = not self.admin_mode
        state_word = "ENABLED" if self.admin_mode else "DISABLED"
        self.message = f"[DEBUG] Admin Mode {state_word}."

    def _debug_change_level(self, delta):
        """Developer-only: jump straight to the next/previous level and
        reposition at its start node, bypassing every win/loss check (no
        _check_stuck() call) -- lets NEXT LVL/PREV LVL be used to test a
        given level's routing in isolation without playing through (or being
        able to fail) everything before it. Money/time carry over as-is."""
        new_index = max(0, min(len(LEVELS) - 1, self.state.level_index + delta))
        self.level = LEVELS[new_index]
        self.state = replace(self.state, level_index=new_index)
        self.state = enter_level(self.state, self.level)
        self.sort_by = "name"
        self.routes = sort_routes(routes_from(self.level, self.state.current_node), self.sort_by)
        self.all_routes_sorted = sort_routes(self.level.bus_routes, self.sort_by)
        self.message = f"[DEBUG] Jumped to Level {new_index + 1}."
        self.trip_planner_open = False
        self.hovered_route = None

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

        row_range, col_range = route_bounds(self.level)
        threshold = self._slen(13)
        for route in self.level.bus_routes:
            points = [self._spt(map_point(r, c, row_range, col_range, MAP_CONTENT_RECT))
                      for r, c in route.path]
            for a, b in zip(points, points[1:]):
                if point_segment_distance(mouse_pos, a, b) <= threshold:
                    self.hovered_route = route
                    return

        self.hovered_route = None
