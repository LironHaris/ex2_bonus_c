"""The interactive walkthrough for the Part C route-economy game's GUI:
GameGUI's "tutorial" screen_state, entered from the title screen's TUTORIAL
button (see game_panels.py's draw_title_screen / game.py's handle_event).

The whole thing renders a small, standalone MOCK scene -- 3 sample bus lines
fanning out from a shared HOME to a shared UNIVERSITY, a mock status bar,
electronic sign, Trip Planner tab, and a mock route-metrics table -- built
from hand-authored coordinates in game_constants.py, not the real
self.level/self.state. It reuses several of MapRendererMixin's icon-drawing
methods (_draw_home_icon/_draw_university_icon/_draw_station/
_draw_thick_polyline, all of which only take explicit positions as
arguments, never touching self.level) and PanelsMixin's small building
blocks (_draw_small_button/_draw_menu_button/_wrap_text), so the tutorial's
own code only has to assemble them, not reimplement them.

self.tutorial_step (0-based) drives which of the 7 TUTORIAL_STEPS is shown;
each step dims the whole mock scene except a spotlighted rect (or rects),
drawn via _draw_tutorial_dim, plus a fixed caption bar at the bottom with
the step's instructional text and a NEXT / BEGIN MISSION button (see
game.py's handle_event for how clicking advances tutorial_step or launches
Level 1).
"""

import pygame

from game_constants import (
    ADMIN_MODE_RECT, AFFORD_COLOR, BASE_HEIGHT, BASE_WIDTH, DEBUG_NEXT_RECT, DEBUG_PREV_RECT, DIM_TEXT_COLOR,
    LETTERBOX_COLOR,
    OUTLINE_COLOR, PANEL_BG, ROAD_EDGE, ROAD_FILL, ROAD_OUTLINE, SIGN_BG, SIGN_BORDER_COLOR, SIGN_TEXT_COLOR,
    TEXT_COLOR, TOP_PANEL_HEIGHT, TUTORIAL_BEGIN_BUTTON_RECT, TUTORIAL_CAPTION_RECT, TUTORIAL_HIGHLIGHT_COLOR,
    TUTORIAL_HOME_POS, TUTORIAL_MAP_RECT, TUTORIAL_MOCK_LINES, TUTORIAL_MOCK_STATIONS, TUTORIAL_NEXT_BUTTON_RECT,
    TUTORIAL_SIGN_RECT, TUTORIAL_STEPS, TUTORIAL_TABLE_RECT, TUTORIAL_TRIP_TAB_RECT, TUTORIAL_UNIVERSITY_POS,
    WINDOW_BG,
)

# Static sample rows for the mock electronic sign / Trip Planner table --
# purely illustrative, unrelated to any real level's actual routes.
_MOCK_SIGN_ROWS = [("Red Line", 4, 9, 5), ("Green Line", 7, 12, 6), ("Blue Line", 2, 6, 4)]
_MOCK_TABLE_ROWS = [("Red Line", 9, 5), ("Green Line", 12, 7), ("Blue Line", 6, 3)]


class TutorialMixin:
    # -- the standalone mock scene ------------------------------------------
    def _draw_tutorial_status_bar(self):
        bar_rect = pygame.Rect(0, 0, BASE_WIDTH, TOP_PANEL_HEIGHT)
        pygame.draw.rect(self.screen, PANEL_BG, self._srect(bar_rect))
        text = "CASH: 30 NIS  |  TIME: 26:00  |  AT: HOME"
        self.screen.blit(self._font(19, bold=True).render(text, True, TEXT_COLOR), self._spt((20, 12)))
        self._draw_small_button(ADMIN_MODE_RECT, "ADMIN MODE: OFF", active=False)
        self._draw_small_button(DEBUG_PREV_RECT, "PREV LVL", enabled=False)
        self._draw_small_button(DEBUG_NEXT_RECT, "NEXT LVL", enabled=False)

    def _draw_tutorial_map(self):
        pygame.draw.rect(self.screen, WINDOW_BG, self._srect(TUTORIAL_MAP_RECT), border_radius=self._slen(6))

        for _, path in TUTORIAL_MOCK_LINES:
            points = [self._spt(p) for p in path]
            self._draw_thick_polyline(points, ROAD_OUTLINE, self._slen(15))
        for _, path in TUTORIAL_MOCK_LINES:
            points = [self._spt(p) for p in path]
            self._draw_thick_polyline(points, ROAD_EDGE, self._slen(12))
        for _, path in TUTORIAL_MOCK_LINES:
            points = [self._spt(p) for p in path]
            self._draw_thick_polyline(points, ROAD_FILL, self._slen(8))
        for color, path in TUTORIAL_MOCK_LINES:
            points = [self._spt(p) for p in path]
            self._draw_thick_polyline(points, color, self._slen(3))

        self._draw_home_icon(TUTORIAL_HOME_POS)
        self._draw_university_icon(TUTORIAL_UNIVERSITY_POS)
        for pos, color, task_type in TUTORIAL_MOCK_STATIONS:
            self._draw_station(pos, color, task_type)

    def _draw_tutorial_sign(self):
        pygame.draw.rect(self.screen, PANEL_BG, self._srect(TUTORIAL_SIGN_RECT), border_radius=self._slen(6))
        x, y = TUTORIAL_SIGN_RECT.x + 15, TUTORIAL_SIGN_RECT.y + 10
        header = self._font(17, bold=True).render("STATION DISPLAY - HOME - LIVE DEPARTURES", True, TEXT_COLOR)
        self.screen.blit(header, self._spt((x, y)))
        y += 24

        sign_rect = pygame.Rect(x, y, TUTORIAL_SIGN_RECT.width - 30, TUTORIAL_SIGN_RECT.bottom - 12 - y)
        pygame.draw.rect(self.screen, SIGN_BG, self._srect(sign_rect), border_radius=self._slen(4))
        pygame.draw.rect(self.screen, SIGN_BORDER_COLOR, self._srect(sign_rect), max(1, self._slen(2)),
                          border_radius=self._slen(4))

        row_h = sign_rect.height / len(_MOCK_SIGN_ROWS)
        for i, (label, next_bus, duration, price) in enumerate(_MOCK_SIGN_ROWS):
            row_y = sign_rect.y + i * row_h
            text = (f"{label:<11} NEXT BUS: {next_bus:>2} MIN   "
                    f"DURATION: {duration:>2} MIN   PRICE: {price:>2} NIS")
            surf = self._font(14, bold=True, mono=True).render(text, True, SIGN_TEXT_COLOR)
            self.screen.blit(surf, self._spt((sign_rect.x + 14, row_y + row_h / 2 - 8)))

    def _draw_tutorial_trip_tab(self):
        rect = self._srect(TUTORIAL_TRIP_TAB_RECT)
        pygame.draw.rect(self.screen, PANEL_BG, rect,
                          border_top_left_radius=self._slen(8), border_bottom_left_radius=self._slen(8))
        pygame.draw.rect(self.screen, OUTLINE_COLOR, rect, max(1, self._slen(2)),
                          border_top_left_radius=self._slen(8), border_bottom_left_radius=self._slen(8))
        label = pygame.transform.rotate(self._font(14, bold=True).render("TRIP PLANNER", True, TEXT_COLOR), 90)
        self.screen.blit(label, label.get_rect(center=rect.center))

    def _draw_tutorial_trip_table(self):
        """Simulated Trip Planner mockup table -- only shown during step 4
        (Trip Planner), on top of the mock map underneath it."""
        rect = TUTORIAL_TABLE_RECT
        pygame.draw.rect(self.screen, PANEL_BG, self._srect(rect), border_radius=self._slen(8))
        pygame.draw.rect(self.screen, OUTLINE_COLOR, self._srect(rect), max(1, self._slen(2)),
                          border_radius=self._slen(8))
        x, y = rect.x + 14, rect.y + 12
        title = self._font(15, bold=True).render("TRIP PLANNER - Full Route Metrics", True, TEXT_COLOR)
        self.screen.blit(title, self._spt((x, y)))
        y += 24

        header = f"{'LINE':<13}{'DUR':>6}{'DIST':>7}"
        self.screen.blit(self._font(13, bold=True, mono=True).render(header, True, DIM_TEXT_COLOR),
                          self._spt((x, y)))
        y += 18
        pygame.draw.line(self.screen, DIM_TEXT_COLOR, self._spt((x, y)), self._spt((rect.right - 14, y)),
                          max(1, self._slen(1)))
        y += 8

        for label, duration, distance in _MOCK_TABLE_ROWS:
            row = f"{label:<13}{duration:>6}{distance:>7}"
            self.screen.blit(self._font(13, mono=True).render(row, True, TEXT_COLOR), self._spt((x, y)))
            y += 18

        hint = self._font(11).render("Click column headers above to sort.", True, DIM_TEXT_COLOR)
        self.screen.blit(hint, self._spt((x, y + 6)))

    # -- the spotlight dim effect --------------------------------------------
    def _draw_tutorial_dim(self, highlight_rects):
        """Dim the whole screen except the given highlight rects (base/design
        space): each one is snapshotted before the dim overlay is applied,
        then blitted back on top at full brightness with a bright bounding-
        box border -- the walkthrough's "dim everything except X / highlight
        Y" effect. An empty list dims nothing (the final step, once every
        prior element has already been individually introduced)."""
        if not highlight_rects:
            return

        screen_bounds = self.screen.get_rect()
        saved = []
        for rect in highlight_rects:
            screen_rect = self._srect(rect).clip(screen_bounds)
            if screen_rect.width > 0 and screen_rect.height > 0:
                saved.append((screen_rect, self.screen.subsurface(screen_rect).copy()))

        overlay = pygame.Surface((self.window_width, self.window_height), pygame.SRCALPHA)
        overlay.fill((8, 7, 6, 210))
        self.screen.blit(overlay, (0, 0))

        for screen_rect, snapshot in saved:
            self.screen.blit(snapshot, screen_rect)
            pygame.draw.rect(self.screen, TUTORIAL_HIGHLIGHT_COLOR, screen_rect, max(2, self._slen(3)),
                              border_radius=self._slen(6))

    def _tutorial_highlight_rects(self):
        """Which base/design-space rect(s) stay lit for the current
        self.tutorial_step -- see TUTORIAL_STEPS for the matching text."""
        step = self.tutorial_step
        if step == 0:  # Goal -- the Status Bar metrics
            return [pygame.Rect(0, 0, BASE_WIDTH, TOP_PANEL_HEIGHT)]
        if step == 1:  # Map Navigation -- the 3 sample bus lines
            return [TUTORIAL_MAP_RECT]
        if step == 2:  # Dashboard -- the Electronic Bus Sign
            return [TUTORIAL_SIGN_RECT]
        if step == 3:  # Trip Planner -- its tab and the mockup table
            return [TUTORIAL_TRIP_TAB_RECT, TUTORIAL_TABLE_RECT]
        if step == 4:  # Tasks -- each mini-game node icon on the mock paths
            return [pygame.Rect(pos[0] - 26, pos[1] - 26, 52, 52) for pos, _, _ in TUTORIAL_MOCK_STATIONS]
        if step == 5:  # Admin Mode -- the switch
            return [ADMIN_MODE_RECT]
        return []  # step 6: Call to Action -- clear highlights, full brightness

    # -- caption + navigation -------------------------------------------------
    def _draw_tutorial_caption(self):
        rect = TUTORIAL_CAPTION_RECT
        pygame.draw.rect(self.screen, PANEL_BG, self._srect(rect), border_radius=self._slen(8))
        pygame.draw.rect(self.screen, OUTLINE_COLOR, self._srect(rect), max(1, self._slen(2)),
                          border_radius=self._slen(8))

        step = self.tutorial_step
        progress = self._font(12, bold=True).render(f"STEP {step + 1} OF {len(TUTORIAL_STEPS)}", True,
                                                      DIM_TEXT_COLOR)
        self.screen.blit(progress, self._spt((rect.x + 16, rect.y + 10)))

        body_font = self._font(15)
        max_width = (rect.width - 32) * self.scale
        lines = self._wrap_text(TUTORIAL_STEPS[step]["text"], body_font, max_width)
        ly = rect.y + 32
        for line in lines:
            surf = body_font.render(line, True, TEXT_COLOR)
            self.screen.blit(surf, self._spt((rect.x + 16, ly)))
            ly += body_font.get_linesize()

        skip_surf = self._font(12).render("ESC / Skip Tutorial", True, DIM_TEXT_COLOR)
        skip_rect = skip_surf.get_rect()
        skip_rect.bottomleft = self._spt((rect.x + 16, rect.bottom - 10))
        self.screen.blit(skip_surf, skip_rect)
        self.tutorial_skip_rect = skip_rect

        if step == len(TUTORIAL_STEPS) - 1:
            self.tutorial_next_rect = self._draw_menu_button(TUTORIAL_BEGIN_BUTTON_RECT, "BEGIN MISSION",
                                                               AFFORD_COLOR)
        else:
            self.tutorial_next_rect = self._draw_menu_button(TUTORIAL_NEXT_BUTTON_RECT, "NEXT", AFFORD_COLOR)

    # -- top-level entry point -------------------------------------------------
    def draw_tutorial_screen(self):
        self.screen.fill(LETTERBOX_COLOR)
        pygame.draw.rect(self.screen, WINDOW_BG, self._srect(pygame.Rect(0, 0, BASE_WIDTH, BASE_HEIGHT)))

        self._draw_tutorial_status_bar()
        self._draw_tutorial_map()
        self._draw_tutorial_sign()
        self._draw_tutorial_trip_tab()
        if self.tutorial_step == 3:
            self._draw_tutorial_trip_table()

        self._draw_tutorial_dim(self._tutorial_highlight_rects())

        self._draw_tutorial_caption()
