"""Blocking sub-loop animations for the Part C route-economy game's GUI: the
bus-driving animation shown while boarding a line, and the traffic-delay
popup. Both follow the same pattern -- redraw the full frame every tick,
keep the clock ticking via self.advance_clock(), and return control once
resolved -- mirroring how minigames.py's run_*_task(gui) functions behave.
"""

import pygame

from game_constants import (
    BASE_HEIGHT, BASE_WIDTH, LETTERBOX_COLOR, MAP_CONTENT_RECT, OUTLINE_COLOR, POPUP_BG, POPUP_BORDER,
    POPUP_TEXT_COLOR, WINDOW_BG,
)
from game_geometry import interpolate_path, map_point, route_bounds


class AnimationMixin:
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

    def _animate_bus(self, base_path, color, duration=2.4):
        """Blocking sub-loop (same pattern as the mini-games) that drives a
        bus icon smoothly along base_path (BASE-space route.path points) in
        real time, redrawing the full frame every tick. The clock keeps
        ticking during this via advance_clock() -- it only pauses once
        game-over is reached, at which point the loop stops early."""
        if len(base_path) < 2:
            return
        row_range, col_range = route_bounds(self.level)
        base_points = [map_point(r, c, row_range, col_range, MAP_CONTENT_RECT) for r, c in base_path]

        elapsed = 0.0
        while elapsed < duration:
            dt = self.clock.tick(60) / 1000.0
            elapsed += dt
            self.advance_clock(dt)
            if self.screen_state != "playing":
                return

            for event in pygame.event.get():
                self.handle_window_event(event)

            pos = interpolate_path(base_points, elapsed / duration)

            self.screen.fill(LETTERBOX_COLOR)
            pygame.draw.rect(self.screen, WINDOW_BG, self._srect(pygame.Rect(0, 0, BASE_WIDTH, BASE_HEIGHT)))
            self.draw_status_bar()
            self.draw_map()
            self.draw_bottom_panel()
            self._draw_bus_icon(*self._spt(pos), color)
            pygame.display.flip()

    def _show_popup(self, message):
        """Blocking modal (same pattern as _animate_bus/mini-games): freezes
        the game behind a dark overlay and a message box until the player
        clicks or presses any key. The clock keeps ticking throughout, same
        as every other blocking sub-loop in this game."""
        while True:
            dt = self.clock.tick(60) / 1000.0
            self.advance_clock(dt)
            if self.screen_state != "playing":
                return

            dismissed = False
            for event in pygame.event.get():
                if self.handle_window_event(event):
                    continue
                if event.type == pygame.KEYDOWN or (event.type == pygame.MOUSEBUTTONDOWN and event.button == 1):
                    dismissed = True

            self.screen.fill(LETTERBOX_COLOR)
            pygame.draw.rect(self.screen, WINDOW_BG, self._srect(pygame.Rect(0, 0, BASE_WIDTH, BASE_HEIGHT)))
            self.draw_status_bar()
            self.draw_map()
            self.draw_bottom_panel()
            self._draw_popup_box(message)
            pygame.display.flip()

            if dismissed:
                return

    def _draw_popup_box(self, message):
        overlay = pygame.Surface((self.window_width, self.window_height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 160))
        self.screen.blit(overlay, (0, 0))

        box_rect = pygame.Rect(BASE_WIDTH // 2 - 220, BASE_HEIGHT // 2 - 90, 440, 180)
        screen_rect = self._srect(box_rect)
        pygame.draw.rect(self.screen, POPUP_BG, screen_rect, border_radius=self._slen(10))
        pygame.draw.rect(self.screen, POPUP_BORDER, screen_rect, max(1, self._slen(3)), border_radius=self._slen(10))

        title = self._font(22, bold=True).render("TRAFFIC DELAY!", True, POPUP_TEXT_COLOR)
        self.screen.blit(title, title.get_rect(center=self._spt((BASE_WIDTH // 2, BASE_HEIGHT // 2 - 55))))

        msg_font = self._font(17)
        max_width = box_rect.width * 0.85 * self.scale
        lines = self._wrap_text(message, msg_font, max_width)
        line_height = msg_font.get_linesize()
        cx = self._spt((BASE_WIDTH // 2, 0))[0]
        top = self._spt((0, BASE_HEIGHT // 2 - 12))[1]
        for i, line in enumerate(lines):
            surf = msg_font.render(line, True, POPUP_TEXT_COLOR)
            self.screen.blit(surf, surf.get_rect(center=(cx, top + i * line_height)))

        hint = self._font(13).render("Click or press any key to continue", True, POPUP_TEXT_COLOR)
        self.screen.blit(hint, hint.get_rect(center=self._spt((BASE_WIDTH // 2, BASE_HEIGHT // 2 + 68))))
