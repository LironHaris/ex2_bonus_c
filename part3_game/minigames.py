"""Station mini-games, plus the level-completion summary screen, for the
Part C route-economy game.

Each run_*_task(gui) is a small, self-contained, blocking pygame event loop:
it owns drawing and input for the duration of the task and returns True
(passed) or False (failed) once the player resolves it. Triggered from
game_logic.py's attempt_board() right before a boarding attempt is
finalized. show_level_summary(gui, level_number) is the same kind of
blocking loop but has no pass/fail outcome -- it just pauses on a "PROCEED
TO NEXT LEVEL" button between levels.

This module never calls engine.py/models.py/levels.py directly -- it only
calls back into gui.advance_clock() every frame so the real-time countdown
keeps running while a task (or the summary screen) is on screen, exactly
like it does in game.py's main loop.

Layout is authored in the same BASE_WIDTH x BASE_HEIGHT design space as the
rest of the GUI and drawn through the passed-in GameGUI's own scale/font/
window-event helpers (gui._spt/_slen/_font/handle_window_event), so a task
looks and behaves the same whether the window is resized or fullscreen.

Two distinct sets of Agility/Memory/Thinking mini-games exist: the original
Level 2 set (reaction gauge / shape sequence / math equation) and a second
Level 3 set (rapid targets / missing number / flag trivia). Both level's
BusRoute.task_type values are still just "agility"/"memory"/"thinking" --
run_task() picks which concrete implementation to run based on
gui.state.level_index, so the map's station icon glyphs (bolt/grid/gear)
stay meaningful across both levels without any change elsewhere.
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
# for the Level 2 memory task; every trial is a random ordering of these four.
SHAPE_DEFS = [
    ("circle", (210, 40, 40)),
    ("square", (40, 100, 210)),
    ("triangle", (215, 180, 40)),
    ("pentagon", (150, 60, 170)),
]

# Level 3 agility task (rapid targets).
TARGET_COLOR = (205, 70, 60)
TARGET_RING_COLOR = (235, 210, 90)
TARGET_BORDER = (20, 18, 16)

# Level 3 memory task (missing number).
MISSING_NUMBER_COLOR = (235, 210, 90)

# Level 3 thinking task (flag trivia) -- programmatically drawn flags, no
# image assets. Each entry is the list of bar colors, top-to-bottom or
# left-to-right depending on FLAG_ORIENTATION.
FLAG_BARS = {
    "France": [(0, 40, 108), (255, 255, 255), (239, 65, 53)],
    "Italy": [(0, 146, 70), (255, 255, 255), (206, 43, 55)],
    "Germany": [(0, 0, 0), (221, 0, 0), (255, 206, 0)],
}
FLAG_ORIENTATION = {"France": "vertical", "Italy": "vertical", "Germany": "horizontal"}
FLAG_BORDER = (20, 18, 16)
JAPAN_BG = (255, 255, 255)
JAPAN_DISC = (188, 0, 45)

# Level completion summary screen.
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
# Level completion summary screen
# ---------------------------------------------------------------------------

def show_level_summary(gui, level_number):
    """Blocking overlay shown right after clearing a level (once gui.state
    and gui.level already reflect the new level/position) and before the
    player can act on the new level's board. Summarizes what carries
    forward, then waits for a click on PROCEED TO NEXT LEVEL (or SPACE/
    ENTER) to continue. Same blocking-loop pattern as the mini-games below
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


# ---------------------------------------------------------------------------
# Level 2, Task 1: Agility Task (Reaction Gauge)
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
# Level 2, Task 2: Memory Task (Visual Shape Sequence)
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
# Level 2, Task 3: Thinking Task (Math Equation)
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


# ---------------------------------------------------------------------------
# Level 3, Task 1: Agility Task (Rapid Targets)
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
# Level 3, Task 2: Memory Task (Missing Number)
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# Level 3, Task 3: Thinking Task (Flag Trivia)
# ---------------------------------------------------------------------------

def _draw_flag(gui, name, rect):
    """rect is in BASE space; every flag is drawn from plain pygame
    primitives (rects/a circle) -- no image assets."""
    screen_rect = gui._srect(rect)
    if name == "Japan":
        pygame.draw.rect(gui.screen, JAPAN_BG, screen_rect)
        radius = min(screen_rect.width, screen_rect.height) * 0.3
        pygame.draw.circle(gui.screen, JAPAN_DISC, screen_rect.center, radius)
    elif FLAG_ORIENTATION[name] == "vertical":
        bars = FLAG_BARS[name]
        bar_w = screen_rect.width / len(bars)
        for i, color in enumerate(bars):
            bar = pygame.Rect(screen_rect.x + i * bar_w, screen_rect.y, bar_w + 1, screen_rect.height)
            pygame.draw.rect(gui.screen, color, bar)
    else:
        bars = FLAG_BARS[name]
        bar_h = screen_rect.height / len(bars)
        for i, color in enumerate(bars):
            bar = pygame.Rect(screen_rect.x, screen_rect.y + i * bar_h, screen_rect.width, bar_h + 1)
            pygame.draw.rect(gui.screen, color, bar)
    pygame.draw.rect(gui.screen, FLAG_BORDER, screen_rect, max(1, gui._slen(2)))


def run_flag_trivia_task(gui):
    countries = ["France", "Italy", "Germany", "Japan"]
    answer = random.choice(countries)
    choices = countries[:]
    random.shuffle(choices)

    flag_rect = pygame.Rect(BASE_WIDTH // 2 - 90, 140, 180, 120)

    button_w, button_h, gap = 170, 56, 16
    total_w = len(choices) * button_w + (len(choices) - 1) * gap
    left = BASE_WIDTH // 2 - total_w // 2
    base_rects = [
        pygame.Rect(left + i * (button_w + gap), 380, button_w, button_h)
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
                for rect, choice in zip(base_rects, choices):
                    if gui._srect(rect).collidepoint(event.pos):
                        return choice == answer

        _fill_backdrop(gui)
        title = gui._font(26, bold=True).render("THINKING TASK - Flag Trivia", True, TEXT_COLOR)
        gui.screen.blit(title, title.get_rect(center=gui._spt((BASE_WIDTH // 2, 80))))
        hint = gui._font(18).render("Which country does this flag belong to?", True, DIM_TEXT_COLOR)
        gui.screen.blit(hint, hint.get_rect(center=gui._spt((BASE_WIDTH // 2, 115))))

        _draw_flag(gui, answer, flag_rect)

        for rect, choice in zip(base_rects, choices):
            screen_rect = gui._srect(rect)
            pygame.draw.rect(gui.screen, BUTTON_BG, screen_rect, border_radius=gui._slen(8))
            pygame.draw.rect(gui.screen, TEXT_COLOR, screen_rect, gui._slen(2), border_radius=gui._slen(8))
            text = gui._font(20, bold=True).render(choice, True, TEXT_COLOR)
            gui.screen.blit(text, text.get_rect(center=screen_rect.center))

        pygame.display.flip()


# ---------------------------------------------------------------------------
# Dispatch: task_type -> concrete implementation, chosen by level
# ---------------------------------------------------------------------------

LEVEL_2_TASKS = {
    "agility": run_agility_task,
    "memory": run_memory_task,
    "thinking": run_thinking_task,
}

LEVEL_3_TASKS = {
    "agility": run_whackamole_task,
    "memory": run_missing_number_task,
    "thinking": run_flag_trivia_task,
}


def run_task(task_type, gui):
    """Both Level 2 and Level 3 routes use the same 3 task_type category
    names; which concrete mini-game actually runs depends on which level is
    currently active (gui.state.level_index is 0-based, so Level 3 is
    index 2), so the map's station icon glyphs stay meaningful either way."""
    tasks = LEVEL_3_TASKS if gui.state.level_index == 2 else LEVEL_2_TASKS
    return tasks[task_type](gui)
