"""Agility-category station mini-game: Rapid Targets / Whack-a-Mole
(Levels 1, 2, and 3), plus the level-completion summary screen (kept here
rather than in a fourth file, since neither mg_thinking.py nor mg_memory.py
is a better thematic fit and it's a similarly small, self-contained
blocking overlay).

See minigames.py for the task_type + level -> function dispatch. Same
blocking-loop pattern as mg_thinking.py/mg_memory.py: owns drawing and
input until resolved, and keeps the persistent clock ticking every frame
via gui.advance_clock(). Layout is authored in the same BASE_WIDTH x
BASE_HEIGHT design space as the rest of the GUI and drawn through gui's own
scale/font/window-event helpers, so it looks and behaves the same whether
the window is resized or fullscreen.
"""

import random

import pygame

from game_constants import BASE_WIDTH

BACKDROP_COLOR = (20, 18, 16)
TEXT_COLOR = (235, 232, 225)
DIM_TEXT_COLOR = (180, 176, 168)

TARGET_COLOR = (205, 70, 60)
TARGET_RING_COLOR = (235, 210, 90)
TARGET_BORDER = (20, 18, 16)

GREEN_ZONE = (60, 170, 80)
SUMMARY_TITLE_COLOR = (140, 230, 150)
PROCEED_BUTTON_COLOR = GREEN_ZONE


def _fill_backdrop(gui):
    """Full-window dark backdrop for a mini-game, independent of the map's
    own letterboxed content area -- this covers the whole actual window."""
    gui.screen.fill(BACKDROP_COLOR)


def _pump(gui):
    """Drain the event queue, handling window management first. Returns the
    remaining (non window-management) events for task-specific handling."""
    events = pygame.event.get()
    return [e for e in events if not gui.handle_window_event(e)]


# ---------------------------------------------------------------------------
# Levels 1, 2 & 3: Agility Task (Rapid Targets)
# ---------------------------------------------------------------------------

def run_whackamole_task(gui):
    """5 circular targets, one at a time, each at a random position with its
    own tight countdown (shown as a shrinking ring). Miss any one -- either
    by not clicking it in time or running out of the level's own clock --
    and the task fails; all 5 hit in time passes it."""
    target_r = 34  # BASE-space radius
    time_limit_per_target = 1.4

    for index in range(5):
        cx = random.uniform(120, BASE_WIDTH - 120)
        cy = random.uniform(190, 460)
        elapsed = 0.0
        hit = False

        while elapsed < time_limit_per_target and not hit:
            dt = gui.clock.tick(60) / 1000.0
            elapsed += dt
            gui.advance_clock(dt)
            if gui.screen_state != "playing":
                return False

            for event in _pump(gui):
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    center = gui._spt((cx, cy))
                    radius = gui._slen(target_r)
                    dx, dy = event.pos[0] - center[0], event.pos[1] - center[1]
                    if dx * dx + dy * dy <= radius * radius:
                        hit = True

            _fill_backdrop(gui)
            title = gui._font(26, bold=True).render("AGILITY TASK - Rapid Targets", True, TEXT_COLOR)
            gui.screen.blit(title, title.get_rect(center=gui._spt((BASE_WIDTH // 2, 90))))
            hint = gui._font(18).render(f"Target {index + 1} / 5 -- click it fast!", True, DIM_TEXT_COLOR)
            gui.screen.blit(hint, hint.get_rect(center=gui._spt((BASE_WIDTH // 2, 128))))

            remaining_frac = max(0.0, 1.0 - elapsed / time_limit_per_target)
            center = gui._spt((cx, cy))
            pygame.draw.circle(gui.screen, TARGET_RING_COLOR, center,
                                gui._slen(target_r * (0.55 + 0.55 * remaining_frac)), gui._slen(3))
            pygame.draw.circle(gui.screen, TARGET_COLOR, center, gui._slen(target_r))
            pygame.draw.circle(gui.screen, TARGET_BORDER, center, gui._slen(target_r), gui._slen(2))

            pygame.display.flip()

        if not hit:
            return False

    return True


# ---------------------------------------------------------------------------
# Level completion summary screen
# ---------------------------------------------------------------------------

def show_level_summary(gui, level_number):
    """Blocking overlay shown right after clearing a level (once gui.state
    and gui.level already reflect the new level/position) and before the
    player can act on the new level's board. Summarizes what carries
    forward, then waits for a click on PROCEED TO NEXT LEVEL (or SPACE/
    ENTER) to continue. Same blocking-loop pattern as the mini-games above
    -- the clock keeps ticking via gui.advance_clock(), so dawdling here
    still costs real time."""
    button_rect = pygame.Rect(BASE_WIDTH // 2 - 160, 420, 320, 58)

    while True:
        dt = gui.clock.tick(60) / 1000.0
        gui.advance_clock(dt)
        if gui.screen_state != "playing":
            return

        proceed = False
        for event in _pump(gui):
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if gui._srect(button_rect).collidepoint(event.pos):
                    proceed = True
            elif event.type == pygame.KEYDOWN and event.key in (pygame.K_SPACE, pygame.K_RETURN):
                proceed = True

        _fill_backdrop(gui)
        title = gui._font(34, bold=True).render(f"LEVEL {level_number} COMPLETE!", True, SUMMARY_TITLE_COLOR)
        gui.screen.blit(title, title.get_rect(center=gui._spt((BASE_WIDTH // 2, 160))))

        total_seconds = max(0, round(gui.state.time_remaining * 60))
        minutes, seconds = divmod(total_seconds, 60)
        time_line = gui._font(22).render(
            f"Time Carried Over: {minutes:02d}:{seconds:02d}", True, TEXT_COLOR)
        gui.screen.blit(time_line, time_line.get_rect(center=gui._spt((BASE_WIDTH // 2, 250))))

        cash_line = gui._font(22).render(
            f"Cash Remaining: {gui.state.money} NIS", True, TEXT_COLOR)
        gui.screen.blit(cash_line, cash_line.get_rect(center=gui._spt((BASE_WIDTH // 2, 290))))

        screen_rect = gui._srect(button_rect)
        pygame.draw.rect(gui.screen, PROCEED_BUTTON_COLOR, screen_rect, border_radius=gui._slen(10))
        pygame.draw.rect(gui.screen, TEXT_COLOR, screen_rect, gui._slen(2), border_radius=gui._slen(10))
        label = gui._font(20, bold=True).render("PROCEED TO NEXT LEVEL", True, (250, 250, 245))
        gui.screen.blit(label, label.get_rect(center=screen_rect.center))

        pygame.display.flip()

        if proceed:
            return
