"""UI panel/screen rendering for the Part C route-economy game's GUI: the
top status bar (incl. the debug level-jump buttons), the electronic
bus-stop sign, the Trip Planner tab + modal, and the title/end screens.
"""

import pygame

from engine import can_board, next_bus_minutes

from game_constants import (
    ADMIN_MODE_RECT, AFFORD_COLOR, BASE_HEIGHT, BASE_WIDTH, BOTTOM_PANEL_RECT, DEBUG_NEXT_RECT, DEBUG_PREV_RECT,
    DENY_COLOR, DIM_TEXT_COLOR, LETTERBOX_COLOR, OUTLINE_COLOR, PANEL_BG, RETURN_BUTTON_RECT, RULES_TEXT, SIGN_BG,
    SIGN_BORDER_COLOR, SIGN_TEXT_COLOR, SIGN_TEXT_DIM, SIGN_TEXT_HOVER, SORT_FIELDS, SORT_LABELS, START_BUTTON_RECT,
    TEXT_COLOR, TITLE, TOP_PANEL_HEIGHT, TRIP_PLANNER_MODAL_RECT, TRIP_PLANNER_TAB_RECT, WINDOW_BG,
)
from game_geometry import darken, lighten, node_label, node_short_label


class PanelsMixin:
    # -- drawing: panels ----------------------------------------------------
    def draw_status_bar(self):
        bar_rect = pygame.Rect(0, 0, BASE_WIDTH, TOP_PANEL_HEIGHT)
        pygame.draw.rect(self.screen, PANEL_BG, self._srect(bar_rect))
        total_seconds = max(0, round(self.state.time_remaining * 60))
        minutes, seconds = divmod(total_seconds, 60)
        text = (f"CASH: {self.state.money} NIS  |  TIME: {minutes:02d}:{seconds:02d}  |  "
                f"AT: {node_label(self.state.current_node)}")
        pos = self._spt((20, 12))
        self.screen.blit(self._font(19, bold=True).render(text, True, TEXT_COLOR), pos)

        self.debug_admin_rect = self._draw_small_button(
            ADMIN_MODE_RECT, f"ADMIN MODE: {'ON' if self.admin_mode else 'OFF'}", active=self.admin_mode)
        # PREV/NEXT LVL are only clickable while Admin Mode is on -- grayed
        # out and inert otherwise (see game.py's handle_event, which guards
        # the actual _debug_change_level() calls behind self.admin_mode too).
        self.debug_prev_rect = self._draw_small_button(DEBUG_PREV_RECT, "PREV LVL", enabled=self.admin_mode)
        self.debug_next_rect = self._draw_small_button(DEBUG_NEXT_RECT, "NEXT LVL", enabled=self.admin_mode)

        hint = self._font(11).render("F11: toggle fullscreen", True, DIM_TEXT_COLOR)
        hpos = self._spt((BASE_WIDTH - 180, 30))
        self.screen.blit(hint, hpos)

    def _draw_small_button(self, base_rect, label, active=False, enabled=True):
        rect = self._srect(base_rect)
        if not enabled:
            bg_color = darken(PANEL_BG, 55)
            border_color = darken(OUTLINE_COLOR, 30)
            text_color = DIM_TEXT_COLOR
        elif active:
            bg_color = AFFORD_COLOR
            border_color = lighten(AFFORD_COLOR, 60)
            text_color = WINDOW_BG
        else:
            bg_color = darken(PANEL_BG, 40)
            border_color = OUTLINE_COLOR
            text_color = TEXT_COLOR
        pygame.draw.rect(self.screen, bg_color, rect, border_radius=self._slen(4))
        pygame.draw.rect(self.screen, border_color, rect, max(1, self._slen(1.5)), border_radius=self._slen(4))
        surf = self._font(11, bold=True).render(label, True, text_color)
        self.screen.blit(surf, surf.get_rect(center=rect.center))
        return rect

    def draw_bottom_panel(self):
        """A retro amber-on-black electronic bus-stop sign: just line name,
        next-departure countdown, and travel duration per line -- the full
        metrics (distance/frequency/price) and the sort controls live in the
        Trip Planner modal instead, see draw_trip_planner_modal()."""
        pygame.draw.rect(self.screen, PANEL_BG, self._srect(BOTTOM_PANEL_RECT), border_radius=self._slen(6))
        x = BOTTOM_PANEL_RECT.x + 15
        y = BOTTOM_PANEL_RECT.y + 12

        header_text = f"STATION DISPLAY - {node_label(self.state.current_node).upper()} - LIVE DEPARTURES"
        header = self._font(20, bold=True).render(header_text, True, TEXT_COLOR)
        self.screen.blit(header, self._spt((x, y)))
        y += 28

        sign_rect = pygame.Rect(x, y, BOTTOM_PANEL_RECT.width - 30,
                                 BOTTOM_PANEL_RECT.bottom - 16 - y)
        pygame.draw.rect(self.screen, SIGN_BG, self._srect(sign_rect), border_radius=self._slen(4))
        pygame.draw.rect(self.screen, SIGN_BORDER_COLOR, self._srect(sign_rect),
                          max(1, self._slen(2)), border_radius=self._slen(4))

        self.route_rows = []
        row_height = sign_rect.height / len(self.routes)
        inner_x = sign_rect.x + 14
        for i, r in enumerate(self.routes):
            row_y = sign_rect.y + i * row_height
            fits = can_board(self.state, r)
            is_hovered = r is self.hovered_route

            # Fixed-size click zone kept in sync with the map: hovering this
            # row or that line's road both set self.hovered_route the same way.
            row_rect = pygame.Rect(sign_rect.x + 4, row_y + 2, sign_rect.width - 8, row_height - 4)
            self.route_rows.append((self._srect(row_rect), r))

            if is_hovered:
                pygame.draw.rect(self.screen, lighten(SIGN_BG, 25), self._srect(row_rect),
                                  border_radius=self._slen(3))

            color = SIGN_TEXT_HOVER if is_hovered else (SIGN_TEXT_COLOR if fits else SIGN_TEXT_DIM)
            next_bus = next_bus_minutes(self.state, r)
            text = (f"{self._route_label(r):<11} NEXT BUS: {next_bus:>2} MIN   "
                    f"DURATION: {r.duration:>2} MIN   PRICE: {r.price:>2} NIS")
            surf = self._font(15, bold=True, mono=True).render(text, True, color)
            text_pos = self._spt((inner_x, row_y + row_height / 2 - 9))
            self.screen.blit(surf, text_pos)

            dot_color = AFFORD_COLOR if fits else DENY_COLOR
            dot_pos = self._spt((sign_rect.x + sign_rect.width - 16, row_y + row_height / 2))
            pygame.draw.circle(self.screen, dot_color, dot_pos, self._slen(4))

        if self.message:
            surf = self._font(15).render(self.message, True, DIM_TEXT_COLOR)
            self.screen.blit(surf, self._spt((x, BOTTOM_PANEL_RECT.bottom - 20)))

    def draw_trip_planner_tab(self):
        rect = self._srect(TRIP_PLANNER_TAB_RECT)
        bg = lighten(PANEL_BG, 15) if self.trip_planner_open else PANEL_BG
        pygame.draw.rect(self.screen, bg, rect,
                          border_top_left_radius=self._slen(8), border_bottom_left_radius=self._slen(8))
        pygame.draw.rect(self.screen, OUTLINE_COLOR, rect, max(1, self._slen(2)),
                          border_top_left_radius=self._slen(8), border_bottom_left_radius=self._slen(8))
        label = pygame.transform.rotate(self._font(16, bold=True).render("TRIP PLANNER", True, TEXT_COLOR), 90)
        self.screen.blit(label, label.get_rect(center=rect.center))
        self.trip_planner_tab_rect = rect

    def draw_trip_planner_modal(self):
        """Full detailed metrics for every line configured in the level --
        including connecting/transfer lines that don't depart from HOME --
        plus the sort controls, the only place sorting can be triggered
        from. Sorting still runs the real C bubble/quick sort via
        engine.sort_routes(); this just decides when to call it. Lines not
        currently reachable from the player's position are dimmed rather
        than colored afford/deny, since "can I afford it" doesn't matter
        until they've actually transferred there."""
        overlay = pygame.Surface((self.window_width, self.window_height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 150))
        self.screen.blit(overlay, (0, 0))

        rect = TRIP_PLANNER_MODAL_RECT
        pygame.draw.rect(self.screen, PANEL_BG, self._srect(rect), border_radius=self._slen(10))
        pygame.draw.rect(self.screen, OUTLINE_COLOR, self._srect(rect), max(1, self._slen(2.5)),
                          border_radius=self._slen(10))

        x = rect.x + 24
        y = rect.y + 20
        title = self._font(24, bold=True).render("TRIP PLANNER - Full Route Metrics", True, TEXT_COLOR)
        self.screen.blit(title, self._spt((x, y)))
        y += 32

        at_line = self._font(15).render(f"Currently at: {node_label(self.state.current_node)}", True, DIM_TEXT_COLOR)
        self.screen.blit(at_line, self._spt((x, y)))
        y += 24

        legend = self._font(13).render(
            "Dimmed lines depart from elsewhere -- transfer there first.", True, DIM_TEXT_COLOR)
        self.screen.blit(legend, self._spt((x, y)))
        y += 22

        header = f"{'LINE':<13}{'FROM':<11}{'TO':<11}{'DIST':>6}{'DUR':>6}{'NEXT':>6}{'PRICE':>7}"
        self.screen.blit(self._font(14, bold=True, mono=True).render(header, True, DIM_TEXT_COLOR),
                          self._spt((x, y)))
        y += 20
        pygame.draw.line(self.screen, DIM_TEXT_COLOR, self._spt((x, y)), self._spt((rect.right - 24, y)),
                          max(1, self._slen(1)))
        y += 8

        for r in self.all_routes_sorted:
            reachable = r.origin == self.state.current_node
            if reachable:
                color = AFFORD_COLOR if can_board(self.state, r) else DENY_COLOR
            else:
                color = DIM_TEXT_COLOR
            row = (f"{self._route_label(r):<13}{node_short_label(r.origin):<11}{node_short_label(r.destination):<11}"
                   f"{r.distance:>6}{r.duration:>6}{next_bus_minutes(self.state, r):>6}{r.price:>7}")
            self.screen.blit(self._font(14, mono=True).render(row, True, color), self._spt((x, y)))
            y += 20

        y += 10
        pygame.draw.line(self.screen, DIM_TEXT_COLOR, self._spt((x, y)), self._spt((rect.right - 24, y)),
                          max(1, self._slen(1)))
        y += 16

        # Clickable "Sort by..." buttons -- the only way to trigger a sort;
        # rects are recorded (real screen space) for handle_event to hit-test
        # against, same pattern as self.route_rows.
        self.sort_button_rects = []
        button_h = 30
        for label, field in zip(SORT_LABELS, SORT_FIELDS):
            active = self.sort_by == field
            base_rect = pygame.Rect(x, y, rect.right - 24 - x, button_h)
            screen_rect = self._srect(base_rect)
            bg_color = AFFORD_COLOR if active else darken(PANEL_BG, 30)
            border_color = lighten(AFFORD_COLOR, 60) if active else OUTLINE_COLOR
            pygame.draw.rect(self.screen, bg_color, screen_rect, border_radius=self._slen(6))
            pygame.draw.rect(self.screen, border_color, screen_rect, max(1, self._slen(1.5)),
                              border_radius=self._slen(6))
            text_color = WINDOW_BG if active else TEXT_COLOR
            label_surf = self._font(16, bold=active).render(label, True, text_color)
            self.screen.blit(label_surf,
                              label_surf.get_rect(midleft=(screen_rect.x + self._slen(12), screen_rect.centery)))
            self.sort_button_rects.append((screen_rect, field))
            y += button_h + 8

        y += 6
        hint = self._font(14).render(
            "Click a Sort by... button above, or ESC / the Trip Planner tab, to close.", True, DIM_TEXT_COLOR)
        self.screen.blit(hint, self._spt((x, y)))

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

    def _draw_menu_button(self, base_rect, label, bg_color):
        rect = self._srect(base_rect)
        pygame.draw.rect(self.screen, bg_color, rect, border_radius=self._slen(10))
        pygame.draw.rect(self.screen, OUTLINE_COLOR, rect, max(1, self._slen(2.5)), border_radius=self._slen(10))
        surf = self._font(20, bold=True).render(label, True, (245, 245, 240))
        self.screen.blit(surf, surf.get_rect(center=rect.center))
        return rect

    def draw_title_screen(self):
        self.screen.fill(LETTERBOX_COLOR)
        pygame.draw.rect(self.screen, WINDOW_BG, self._srect(pygame.Rect(0, 0, BASE_WIDTH, BASE_HEIGHT)))

        title_surf = self._font(46, bold=True).render(TITLE, True, TEXT_COLOR)
        self.screen.blit(title_surf, title_surf.get_rect(center=self._spt((BASE_WIDTH // 2, 130))))

        subtitle = self._font(17).render("A C-Sorting-Powered Bus Route Planning Game", True, DIM_TEXT_COLOR)
        self.screen.blit(subtitle, subtitle.get_rect(center=self._spt((BASE_WIDTH // 2, 172))))

        rules_font = self._font(16)
        max_width = 600 * self.scale
        lines = self._wrap_text(RULES_TEXT, rules_font, max_width)
        line_height = rules_font.get_linesize()
        cx = self._spt((BASE_WIDTH // 2, 0))[0]
        top = self._spt((0, 230))[1]
        for i, line in enumerate(lines):
            surf = rules_font.render(line, True, TEXT_COLOR)
            self.screen.blit(surf, surf.get_rect(center=(cx, top + i * line_height)))

        self.start_button_rect = self._draw_menu_button(START_BUTTON_RECT, "START GAME", AFFORD_COLOR)

    def draw_end_screen(self):
        self.screen.fill(LETTERBOX_COLOR)
        pygame.draw.rect(self.screen, WINDOW_BG, self._srect(pygame.Rect(0, 0, BASE_WIDTH, BASE_HEIGHT)))

        won = self.run_result == "win"
        text = "SUCCESS!" if won else "GAME OVER!"
        color = AFFORD_COLOR if won else DENY_COLOR

        title_surf = self._font(52, bold=True).render(text, True, color)
        self.screen.blit(title_surf, title_surf.get_rect(center=self._spt((BASE_WIDTH // 2, 220))))

        self.return_button_rect = self._draw_menu_button(RETURN_BUTTON_RECT, "RETURN TO MAIN MENU", darken(PANEL_BG, 90))
