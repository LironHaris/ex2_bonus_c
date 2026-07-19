"""Memory-category station mini-game: Missing Number (Levels 1, 2, and 3).

See minigames.py for the task_type + level -> function dispatch. Same
blocking-loop pattern as mg_thinking.py/mg_agility.py: owns drawing and
input until resolved, returns True (passed) or False (failed), and keeps
the persistent clock ticking every frame via gui.advance_clock() -- so
taking a long time to answer still costs real time. Layout is authored in
the same BASE_WIDTH x BASE_HEIGHT design space as the rest of the GUI and
drawn through gui's own scale/font/window-event helpers, so it looks and
behaves the same whether the window is resized or fullscreen.
"""

import random

import pygame

from game_constants import BASE_WIDTH

BACKDROP_COLOR = (20, 18, 16)
TEXT_COLOR = (235, 232, 225)
DIM_TEXT_COLOR = (180, 176, 168)
BUTTON_BG = (60, 56, 50)
MISSING_NUMBER_COLOR = (235, 210, 90)


def _fill_backdrop(gui):
    """Full-window dark backdrop for a mini-game, independent of the map's
    own letterboxed content area -- this covers the whole actual window."""
    gui.screen.fill(BACKDROP_COLOR)


def _pump(gui):
    """Drain the event queue, handling window management first. Returns the
    remaining (non window-management) events for task-specific handling."""
    events = pygame.event.get()
    return [e for e in events if not gui.handle_window_event(e)]


def run_missing_number_task(gui):
    """6 of the digits 1-7 are scattered on screen (random size + rotation)
    for 3 seconds; the player must then pick out the one digit that was
    never shown, from 4 choices (the missing digit plus 3 real distractors
    that genuinely were on screen)."""
    pool = list(range(1, 8))  # {1, 2, 3, 4, 5, 6, 7}
    missing = random.choice(pool)
    shown = [n for n in pool if n != missing]
    random.shuffle(shown)

    positions = [(random.uniform(90, BASE_WIDTH - 90), random.uniform(150, 400)) for _ in shown]
    sizes = [random.randint(28, 52) for _ in shown]
    angles = [random.uniform(-45, 45) for _ in shown]

    # -- phase 1: show the 6 numbers for 3 seconds --
    elapsed = 0.0
    while elapsed < 3.0:
        dt = gui.clock.tick(60) / 1000.0
        elapsed += dt
        gui.advance_clock(dt)
        if gui.screen_state != "playing":
            return False
        _pump(gui)

        _fill_backdrop(gui)
        title = gui._font(26, bold=True).render("MEMORY TASK - Missing Number", True, TEXT_COLOR)
        gui.screen.blit(title, title.get_rect(center=gui._spt((BASE_WIDTH // 2, 70))))
        hint = gui._font(18).render("Memorize these numbers...", True, DIM_TEXT_COLOR)
        gui.screen.blit(hint, hint.get_rect(center=gui._spt((BASE_WIDTH // 2, 105))))

        for (x, y), size, angle, n in zip(positions, sizes, angles, shown):
            surf = gui._font(size, bold=True).render(str(n), True, MISSING_NUMBER_COLOR)
            rotated = pygame.transform.rotate(surf, angle)
            gui.screen.blit(rotated, rotated.get_rect(center=gui._spt((x, y))))

        pygame.display.flip()

    # -- phase 2: hide --
    elapsed = 0.0
    while elapsed < 0.6:
        dt = gui.clock.tick(60) / 1000.0
        elapsed += dt
        gui.advance_clock(dt)
        if gui.screen_state != "playing":
            return False
        _pump(gui)
        _fill_backdrop(gui)
        hint = gui._font(18).render("...", True, DIM_TEXT_COLOR)
        gui.screen.blit(hint, hint.get_rect(center=gui._spt((BASE_WIDTH // 2, 300))))
        pygame.display.flip()

    # -- phase 3: 4 multiple-choice buttons (the missing digit + 3 real distractors) --
    distractors = shown[:3]
    choices = [missing] + distractors
    random.shuffle(choices)

    button_w, button_h, gap = 150, 70, 20
    total_w = len(choices) * button_w + (len(choices) - 1) * gap
    left = BASE_WIDTH // 2 - total_w // 2
    base_rects = [
        pygame.Rect(left + i * (button_w + gap), 340, button_w, button_h)
        for i in range(len(choices))
    ]

    while True:
        dt = gui.clock.tick(60) / 1000.0
        gui.advance_clock(dt)
        if gui.screen_state != "playing":
            return False

        events = _pump(gui)
        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                for rect, value in zip(base_rects, choices):
                    if gui._srect(rect).collidepoint(event.pos):
                        return value == missing

        _fill_backdrop(gui)
        title = gui._font(26, bold=True).render("MEMORY TASK - Missing Number", True, TEXT_COLOR)
        gui.screen.blit(title, title.get_rect(center=gui._spt((BASE_WIDTH // 2, 190))))
        hint = gui._font(18).render("Which number was NOT shown?", True, DIM_TEXT_COLOR)
        gui.screen.blit(hint, hint.get_rect(center=gui._spt((BASE_WIDTH // 2, 225))))

        for rect, value in zip(base_rects, choices):
            screen_rect = gui._srect(rect)
            pygame.draw.rect(gui.screen, BUTTON_BG, screen_rect, border_radius=gui._slen(8))
            pygame.draw.rect(gui.screen, TEXT_COLOR, screen_rect, gui._slen(2), border_radius=gui._slen(8))
            text = gui._font(28, bold=True).render(str(value), True, TEXT_COLOR)
            gui.screen.blit(text, text.get_rect(center=screen_rect.center))

        pygame.display.flip()
