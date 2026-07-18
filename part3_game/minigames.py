"""Station mini-games for the Part C route-economy game.

Each run_*_task(gui) is a small, self-contained, blocking pygame event loop:
it owns drawing and input for the duration of the task and returns True
(passed) or False (failed) once the player resolves it. Triggered from
game.py right before a boarding attempt is finalized. This module never
calls engine.py/models.py/levels.py directly -- it only calls back into
gui.advance_clock() every frame so the real-time countdown keeps running
while a task is on screen, exactly like it does in game.py's main loop.

Layout is authored in the same BASE_WIDTH x BASE_HEIGHT design space as
game.py and drawn through the passed-in GameGUI's own scale/font/window-event
helpers (gui._spt/_slen/_font/handle_window_event), so a task looks and
behaves the same whether the window is resized or fullscreen.
"""

import math
import random

import pygame

BASE_WIDTH, BASE_HEIGHT = 800, 600  # must match game.py's BASE_WIDTH/BASE_HEIGHT

BACKDROP_COLOR = (20, 18, 16)
TEXT_COLOR = (235, 232, 225)
DIM_TEXT_COLOR = (180, 176, 168)
BUTTON_BG = (60, 56, 50)

RED_ZONE = (200, 60, 50)
YELLOW_ZONE = (215, 180, 40)
GREEN_ZONE = (60, 170, 80)
INDICATOR_COLOR = (245, 245, 245)

# Red circle, blue square, yellow triangle, purple pentagon -- fixed shape set
# for the memory task; every trial is a random ordering of these four.
SHAPE_DEFS = [
    ("circle", (210, 40, 40)),
    ("square", (40, 100, 210)),
    ("triangle", (215, 180, 40)),
    ("pentagon", (150, 60, 170)),
]


def _fill_backdrop(gui):
    """Full-window dark backdrop for a mini-game, independent of the map's
    own letterboxed content area -- this covers the whole actual window."""
    gui.screen.fill(BACKDROP_COLOR)


def _pump(gui):
    """Drain the event queue, handling window management first. Returns the
    remaining (non window-management) events for task-specific handling."""
    events = pygame.event.get()
    return [e for e in events if not gui.handle_window_event(e)]


def _draw_shape(surface, kind, center, size, color):
    x, y = center
    if kind == "circle":
        pygame.draw.circle(surface, color, center, size)
    elif kind == "square":
        rect = pygame.Rect(0, 0, size * 1.8, size * 1.8)
        rect.center = center
        pygame.draw.rect(surface, color, rect)
    elif kind == "triangle":
        points = [(x, y - size), (x - size, y + size), (x + size, y + size)]
        pygame.draw.polygon(surface, color, points)
    elif kind == "pentagon":
        points = [
            (x + size * math.cos(math.radians(90 + i * 72)),
             y - size * math.sin(math.radians(90 + i * 72)))
            for i in range(5)
        ]
        pygame.draw.polygon(surface, color, points)


def _draw_sequence(gui, sequence, base_center_left, spacing, size):
    x, y = base_center_left
    for kind, color in sequence:
        _draw_shape(gui.screen, kind, gui._spt((x, y)), gui._slen(size), color)
        x += spacing


# ---------------------------------------------------------------------------
# Task 1: Agility Task (Reaction Gauge)
# ---------------------------------------------------------------------------

def run_agility_task(gui):
    bar_rect = pygame.Rect(150, 300, 500, 40)
    zone_fracs = [
        (0.00, 0.15, RED_ZONE),
        (0.15, 0.35, YELLOW_ZONE),
        (0.35, 0.65, GREEN_ZONE),
        (0.65, 0.85, YELLOW_ZONE),
        (0.85, 1.00, RED_ZONE),
    ]
    zones = [
        (pygame.Rect(bar_rect.x + f0 * bar_rect.width, bar_rect.y,
                      (f1 - f0) * bar_rect.width, bar_rect.height), color)
        for f0, f1, color in zone_fracs
    ]
    green_zone = zones[2][0]

    speed = 420.0  # base px/sec (design space)
    x = float(bar_rect.x)
    direction = 1
    time_limit = 6.0
    elapsed = 0.0

    while True:
        dt = gui.clock.tick(60) / 1000.0
        elapsed += dt
        gui.advance_clock(dt)
        if gui.screen_state != "playing":
            return False

        for event in _pump(gui):
            if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                return green_zone.collidepoint(x, bar_rect.centery)

        if elapsed >= time_limit:
            return False

        x += direction * speed * dt
        if x <= bar_rect.x:
            x, direction = bar_rect.x, 1
        elif x >= bar_rect.right:
            x, direction = bar_rect.right, -1

        _fill_backdrop(gui)
        title = gui._font(26, bold=True).render("AGILITY TASK - Station Check", True, TEXT_COLOR)
        gui.screen.blit(title, title.get_rect(center=gui._spt((BASE_WIDTH // 2, 190))))
        hint = gui._font(18).render("Press SPACE when the indicator is in the GREEN zone!", True, DIM_TEXT_COLOR)
        gui.screen.blit(hint, hint.get_rect(center=gui._spt((BASE_WIDTH // 2, 230))))

        for rect, color in zones:
            pygame.draw.rect(gui.screen, color, gui._srect(rect))
        pygame.draw.rect(gui.screen, TEXT_COLOR, gui._srect(bar_rect), gui._slen(2))
        top = gui._spt((x, bar_rect.y - 12))
        bottom = gui._spt((x, bar_rect.bottom + 12))
        pygame.draw.line(gui.screen, INDICATOR_COLOR, top, bottom, gui._slen(4))

        pygame.display.flip()


# ---------------------------------------------------------------------------
# Task 2: Memory Task (Visual Shape Sequence)
# ---------------------------------------------------------------------------

def run_memory_task(gui):
    sequence = SHAPE_DEFS[:]
    random.shuffle(sequence)

    choices = [sequence[:]]
    attempts = 0
    while len(choices) < 3 and attempts < 50:
        attempts += 1
        candidate = sequence[:]
        random.shuffle(candidate)
        if candidate not in choices:
            choices.append(candidate)
    random.shuffle(choices)

    seq_start_x = BASE_WIDTH // 2 - (len(sequence) - 1) * 70 // 2

    # -- phase 1: show the sequence --
    elapsed = 0.0
    while elapsed < 2.5:
        dt = gui.clock.tick(60) / 1000.0
        elapsed += dt
        gui.advance_clock(dt)
        if gui.screen_state != "playing":
            return False
        _pump(gui)

        _fill_backdrop(gui)
        title = gui._font(26, bold=True).render("MEMORY TASK - Station Check", True, TEXT_COLOR)
        gui.screen.blit(title, title.get_rect(center=gui._spt((BASE_WIDTH // 2, 160))))
        hint = gui._font(18).render("Memorize this sequence...", True, DIM_TEXT_COLOR)
        gui.screen.blit(hint, hint.get_rect(center=gui._spt((BASE_WIDTH // 2, 200))))
        _draw_sequence(gui, sequence, (seq_start_x, 300), spacing=70, size=26)
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

    # -- phase 3: multiple-choice buttons (each rendered as a mini shape row) --
    button_w, button_h, gap = 380, 70, 20
    total_h = len(choices) * button_h + (len(choices) - 1) * gap
    top = BASE_HEIGHT // 2 - total_h // 2 + 50
    base_rects = [
        pygame.Rect(BASE_WIDTH // 2 - button_w // 2, top + i * (button_h + gap), button_w, button_h)
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
                for rect, candidate in zip(base_rects, choices):
                    if gui._srect(rect).collidepoint(event.pos):
                        return candidate == sequence

        _fill_backdrop(gui)
        title = gui._font(26, bold=True).render("MEMORY TASK - Station Check", True, TEXT_COLOR)
        gui.screen.blit(title, title.get_rect(center=gui._spt((BASE_WIDTH // 2, 110))))
        hint = gui._font(18).render("Click the button showing the original sequence.", True, DIM_TEXT_COLOR)
        gui.screen.blit(hint, hint.get_rect(center=gui._spt((BASE_WIDTH // 2, 145))))

        for rect, candidate in zip(base_rects, choices):
            screen_rect = gui._srect(rect)
            pygame.draw.rect(gui.screen, BUTTON_BG, screen_rect, border_radius=gui._slen(8))
            pygame.draw.rect(gui.screen, TEXT_COLOR, screen_rect, gui._slen(2), border_radius=gui._slen(8))
            _draw_sequence(gui, candidate, (rect.x + 55, rect.centery), spacing=70, size=18)

        pygame.display.flip()


# ---------------------------------------------------------------------------
# Task 3: Thinking Task (Math Equation)
# ---------------------------------------------------------------------------

def run_thinking_task(gui):
    options = [("A", 3), ("B", 4), ("C", 5), ("D", 6)]
    correct_label = "B"  # 2x + 3 = 11 -> x = 4

    button_w, button_h, gap = 150, 60, 20
    total_w = len(options) * button_w + (len(options) - 1) * gap
    left = BASE_WIDTH // 2 - total_w // 2
    base_rects = [
        pygame.Rect(left + i * (button_w + gap), 340, button_w, button_h)
        for i in range(len(options))
    ]

    while True:
        dt = gui.clock.tick(60) / 1000.0
        gui.advance_clock(dt)
        if gui.screen_state != "playing":
            return False

        events = _pump(gui)
        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                for rect, (label, _value) in zip(base_rects, options):
                    if gui._srect(rect).collidepoint(event.pos):
                        return label == correct_label

        _fill_backdrop(gui)
        title = gui._font(26, bold=True).render("THINKING TASK - Station Check", True, TEXT_COLOR)
        gui.screen.blit(title, title.get_rect(center=gui._spt((BASE_WIDTH // 2, 190))))
        eq = gui._font(30, bold=True).render("Solve for x: 2x + 3 = 11", True, TEXT_COLOR)
        gui.screen.blit(eq, eq.get_rect(center=gui._spt((BASE_WIDTH // 2, 260))))

        for rect, (label, value) in zip(base_rects, options):
            screen_rect = gui._srect(rect)
            pygame.draw.rect(gui.screen, BUTTON_BG, screen_rect, border_radius=gui._slen(8))
            pygame.draw.rect(gui.screen, TEXT_COLOR, screen_rect, gui._slen(2), border_radius=gui._slen(8))
            text = gui._font(22, bold=True).render(f"{label}: {value}", True, TEXT_COLOR)
            gui.screen.blit(text, text.get_rect(center=screen_rect.center))

        pygame.display.flip()


TASKS = {
    "agility": run_agility_task,
    "memory": run_memory_task,
    "thinking": run_thinking_task,
}


def run_task(task_type, gui):
    return TASKS[task_type](gui)
