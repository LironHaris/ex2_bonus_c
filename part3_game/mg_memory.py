"""Memory-category station mini-games: Shape Sequences (Level 2), Missing
Number (Level 3), and Three Shells & A Ball (Level 4). Level 1 has no
Memory task at all (no mini-games whatsoever).

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

CUP_COLOR = (150, 90, 40)
CUP_RIM_COLOR = (190, 130, 70)
BALL_COLOR = (225, 60, 60)
CUP_W, CUP_H = 130, 150
CUP_SLOT_X = [BASE_WIDTH // 2 - 220, BASE_WIDTH // 2, BASE_WIDTH // 2 + 220]
CUP_Y = 320
BALL_START_POS = (BASE_WIDTH // 2, CUP_Y - 150)  # neutral holding spot above the cups


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
# Level 2: Shape Sequences
# ---------------------------------------------------------------------------

SHAPE_NAMES = ["circle", "square", "triangle", "diamond"]
SHAPE_BASE_COLOR = (120, 110, 95)
SHAPE_FLASH_COLOR = (235, 210, 90)
SHAPE_TILE_W, SHAPE_TILE_H, SHAPE_GAP = 120, 120, 24
SEQUENCE_LENGTH = 4


def _shape_tile_rects():
    total_w = len(SHAPE_NAMES) * SHAPE_TILE_W + (len(SHAPE_NAMES) - 1) * SHAPE_GAP
    left = BASE_WIDTH // 2 - total_w // 2
    return [
        pygame.Rect(left + i * (SHAPE_TILE_W + SHAPE_GAP), 260, SHAPE_TILE_W, SHAPE_TILE_H)
        for i in range(len(SHAPE_NAMES))
    ]


def _draw_shape(gui, name, rect, color):
    """Every shape is drawn from plain pygame primitives (rect/circle/
    polygon) -- no image assets."""
    screen_rect = gui._srect(rect)
    pygame.draw.rect(gui.screen, BUTTON_BG, screen_rect, border_radius=gui._slen(8))
    pygame.draw.rect(gui.screen, TEXT_COLOR, screen_rect, gui._slen(2), border_radius=gui._slen(8))
    cx, cy = screen_rect.center
    size = gui._slen(36)
    if name == "circle":
        pygame.draw.circle(gui.screen, color, (cx, cy), size)
    elif name == "square":
        pygame.draw.rect(gui.screen, color, pygame.Rect(cx - size, cy - size, size * 2, size * 2))
    elif name == "triangle":
        pygame.draw.polygon(gui.screen, color, [(cx, cy - size), (cx - size, cy + size), (cx + size, cy + size)])
    else:  # diamond
        pygame.draw.polygon(gui.screen, color, [(cx, cy - size), (cx + size, cy), (cx, cy + size), (cx - size, cy)])


def run_shape_sequence_task(gui):
    """4 shapes flash one at a time in a random order (length 4, repeats
    allowed); the player must then click them back in the same order. Any
    wrong click fails the task immediately; completing the full sequence
    passes it."""
    sequence = [random.choice(SHAPE_NAMES) for _ in range(SEQUENCE_LENGTH)]
    tile_rects = _shape_tile_rects()

    def _draw_tiles(hint, highlight_index=None):
        _fill_backdrop(gui)
        title = gui._font(26, bold=True).render("MEMORY TASK - Shape Sequence", True, TEXT_COLOR)
        gui.screen.blit(title, title.get_rect(center=gui._spt((BASE_WIDTH // 2, 90))))
        hint_surf = gui._font(18).render(hint, True, DIM_TEXT_COLOR)
        gui.screen.blit(hint_surf, hint_surf.get_rect(center=gui._spt((BASE_WIDTH // 2, 128))))
        for i, (name, rect) in enumerate(zip(SHAPE_NAMES, tile_rects)):
            color = SHAPE_FLASH_COLOR if i == highlight_index else SHAPE_BASE_COLOR
            _draw_shape(gui, name, rect, color)

    # -- phase 1: play back the sequence, one shape flashed at a time --
    for step_shape in sequence:
        step_index = SHAPE_NAMES.index(step_shape)

        elapsed = 0.0
        while elapsed < 0.6:
            dt = gui.clock.tick(60) / 1000.0
            elapsed += dt
            gui.advance_clock(dt)
            if gui.screen_state != "playing":
                return False
            _pump(gui)
            _draw_tiles("Watch the sequence...", highlight_index=step_index)
            pygame.display.flip()

        elapsed = 0.0
        while elapsed < 0.25:
            dt = gui.clock.tick(60) / 1000.0
            elapsed += dt
            gui.advance_clock(dt)
            if gui.screen_state != "playing":
                return False
            _pump(gui)
            _draw_tiles("Watch the sequence...")
            pygame.display.flip()

    # -- phase 2: the player repeats the sequence by clicking the tiles --
    progress = 0

    def _flash_clicked_tile(index):
        """Brief highlight on the just-clicked tile, identical styling to
        the demo phase's flash, so a click gets instant visual feedback
        before the correctness check resolves (and possibly ends the task).
        Returns False if the game ended mid-flash."""
        elapsed = 0.0
        while elapsed < 0.2:
            dt = gui.clock.tick(60) / 1000.0
            elapsed += dt
            gui.advance_clock(dt)
            if gui.screen_state != "playing":
                return False
            _pump(gui)
            _draw_tiles(f"Now repeat it! ({progress}/{len(sequence)})", highlight_index=index)
            pygame.display.flip()
        return True

    while True:
        dt = gui.clock.tick(60) / 1000.0
        gui.advance_clock(dt)
        if gui.screen_state != "playing":
            return False

        events = _pump(gui)
        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                for i, rect in enumerate(tile_rects):
                    if gui._srect(rect).collidepoint(event.pos):
                        if not _flash_clicked_tile(i):
                            return False
                        if SHAPE_NAMES[i] != sequence[progress]:
                            return False
                        progress += 1
                        if progress == len(sequence):
                            return True

        _draw_tiles(f"Now repeat it! ({progress}/{len(sequence)})")
        pygame.display.flip()


# ---------------------------------------------------------------------------
# Level 3: Missing Number
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
# Level 4: Three Shells & A Ball
# ---------------------------------------------------------------------------

def _draw_cup(gui, x, y):
    """rect is in BASE space; the cup is a plain trapezoid + rim strip --
    drawn from pygame primitives only. The ball (if any) is drawn separately
    by the caller, on top of or beneath the cups as the scene requires."""
    rect = pygame.Rect(int(x - CUP_W / 2), int(y - CUP_H / 2), CUP_W, CUP_H)
    screen_rect = gui._srect(rect)
    pygame.draw.polygon(gui.screen, CUP_COLOR, [
        (screen_rect.left, screen_rect.top),
        (screen_rect.right, screen_rect.top),
        (screen_rect.centerx + gui._slen(CUP_W * 0.28), screen_rect.bottom),
        (screen_rect.centerx - gui._slen(CUP_W * 0.28), screen_rect.bottom),
    ])
    pygame.draw.rect(gui.screen, CUP_RIM_COLOR,
                      (screen_rect.left, screen_rect.top, screen_rect.width, gui._slen(10)))


def _draw_ball(gui, pos):
    pygame.draw.circle(gui.screen, BALL_COLOR, gui._spt(pos), gui._slen(18))


def run_shell_game_task(gui):
    """3 cups, one hiding a ball. First an unhurried reveal sequence: the
    ball appears at a neutral starting position, then visibly slides across
    to and settles under its chosen cup, which is held long enough to be
    unambiguous. The cups then hide it, a simplified horizontal shuffle
    swaps cup positions a few times (animated), and the player must click
    the cup that ended up with the ball."""
    cups = [{"id": i, "x": float(CUP_SLOT_X[i])} for i in range(3)]
    ball_cup_id = random.choice(cups)["id"]
    ball_target_x = next(c["x"] for c in cups if c["id"] == ball_cup_id)

    def _draw_scene(hint, ball_pos=None):
        _fill_backdrop(gui)
        title = gui._font(26, bold=True).render("MEMORY TASK - Three Shells & A Ball", True, TEXT_COLOR)
        gui.screen.blit(title, title.get_rect(center=gui._spt((BASE_WIDTH // 2, 90))))
        hint_surf = gui._font(18).render(hint, True, DIM_TEXT_COLOR)
        gui.screen.blit(hint_surf, hint_surf.get_rect(center=gui._spt((BASE_WIDTH // 2, 128))))
        for cup in cups:
            _draw_cup(gui, cup["x"], CUP_Y)
        if ball_pos is not None:
            _draw_ball(gui, ball_pos)

    # -- phase 1a: the ball appears at a neutral starting position, held
    # still long enough for the player to clearly register where it starts --
    elapsed = 0.0
    while elapsed < 0.7:
        dt = gui.clock.tick(60) / 1000.0
        elapsed += dt
        gui.advance_clock(dt)
        if gui.screen_state != "playing":
            return False
        _pump(gui)
        _draw_scene("Here is the ball...", ball_pos=BALL_START_POS)
        pygame.display.flip()

    # -- phase 1b: the ball visibly slides over to and settles under its cup --
    slide_duration = 1.1
    elapsed = 0.0
    while elapsed < slide_duration:
        dt = gui.clock.tick(60) / 1000.0
        elapsed += dt
        gui.advance_clock(dt)
        if gui.screen_state != "playing":
            return False
        _pump(gui)
        frac = min(1.0, elapsed / slide_duration)
        x = BALL_START_POS[0] + (ball_target_x - BALL_START_POS[0]) * frac
        y = BALL_START_POS[1] + (CUP_Y - BALL_START_POS[1]) * frac
        _draw_scene("Watch it slide under a cup...", ball_pos=(x, y))
        pygame.display.flip()

    # -- phase 1c: the ball rests under its cup, held so the position is
    # unambiguous before the cups close over it --
    elapsed = 0.0
    while elapsed < 0.6:
        dt = gui.clock.tick(60) / 1000.0
        elapsed += dt
        gui.advance_clock(dt)
        if gui.screen_state != "playing":
            return False
        _pump(gui)
        _draw_scene("Watch closely...", ball_pos=(ball_target_x, CUP_Y))
        pygame.display.flip()

    # -- phase 2: hide -- the cups now fully cover the ball --
    elapsed = 0.0
    while elapsed < 0.5:
        dt = gui.clock.tick(60) / 1000.0
        elapsed += dt
        gui.advance_clock(dt)
        if gui.screen_state != "playing":
            return False
        _pump(gui)
        _draw_scene("...")
        pygame.display.flip()

    # -- phase 3: shuffle -- a few animated position swaps --
    swap_duration = 0.45
    for _ in range(4):
        i, j = random.sample(range(3), 2)
        start_i, start_j = cups[i]["x"], cups[j]["x"]
        elapsed = 0.0
        while elapsed < swap_duration:
            dt = gui.clock.tick(60) / 1000.0
            elapsed += dt
            gui.advance_clock(dt)
            if gui.screen_state != "playing":
                return False
            _pump(gui)
            frac = min(1.0, elapsed / swap_duration)
            cups[i]["x"] = start_i + (start_j - start_i) * frac
            cups[j]["x"] = start_j + (start_i - start_j) * frac
            _draw_scene("Shuffling...")
            pygame.display.flip()
        cups[i]["x"], cups[j]["x"] = start_j, start_i

    # -- phase 4: pick a cup --
    while True:
        dt = gui.clock.tick(60) / 1000.0
        gui.advance_clock(dt)
        if gui.screen_state != "playing":
            return False

        events = _pump(gui)
        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                for cup in cups:
                    rect = pygame.Rect(int(cup["x"] - CUP_W / 2), int(CUP_Y - CUP_H / 2), CUP_W, CUP_H)
                    if gui._srect(rect).collidepoint(event.pos):
                        return cup["id"] == ball_cup_id

        _draw_scene("Which cup has the ball? Click it!")
        pygame.display.flip()
