"""Thinking-category station mini-games: Flag Trivia (Levels 1 and 3) and
Linear Equation (Level 2). See minigames.py for the task_type + level ->
function dispatch that picks between the two.

Each run_*_task(gui) is a small, self-contained, blocking pygame event loop
that owns drawing and input until the player resolves it, returning True
(passed) or False (failed). The clock keeps ticking throughout via
gui.advance_clock() every frame, exactly like it does in game.py's main
loop, so dawdling on a question still costs real time. Layout is authored
in the same BASE_WIDTH x BASE_HEIGHT design space as the rest of the GUI and
drawn through the passed-in GameGUI's own scale/font/window-event helpers
(gui._spt/_slen/_font/handle_window_event), so a task looks and behaves the
same whether the window is resized or fullscreen.
"""

import random

import pygame

from game_constants import BASE_WIDTH

BACKDROP_COLOR = (20, 18, 16)
TEXT_COLOR = (235, 232, 225)
DIM_TEXT_COLOR = (180, 176, 168)
BUTTON_BG = (60, 56, 50)

# Flags are drawn from plain pygame primitives (rects/a circle) -- no image
# assets. Each entry is the list of bar colors; orientation says whether
# they're read left-to-right or top-to-bottom.
FLAG_BARS = {
    "France": [(0, 40, 108), (255, 255, 255), (239, 65, 53)],
    "Italy": [(0, 146, 70), (255, 255, 255), (206, 43, 55)],
    "Germany": [(0, 0, 0), (221, 0, 0), (255, 206, 0)],
}
FLAG_ORIENTATION = {"France": "vertical", "Italy": "vertical", "Germany": "horizontal"}
FLAG_BORDER = (20, 18, 16)
JAPAN_BG = (255, 255, 255)
JAPAN_DISC = (188, 0, 45)


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
# Levels 1 & 3: Flag Trivia
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
# Level 2: Linear Equation (ax + b = c)
# ---------------------------------------------------------------------------

def _generate_linear_equation():
    """A random ax + b = c with an integer solution, plus 3 near-miss
    integer distractors so guessing isn't trivially obvious from magnitude
    alone."""
    a = random.randint(2, 6)
    x_answer = random.choice([n for n in range(-9, 10) if n != 0])
    b = random.randint(-10, 10)
    c = a * x_answer + b

    distractors = set()
    offsets = [-3, -2, -1, 1, 2, 3]
    random.shuffle(offsets)
    for offset in offsets:
        if len(distractors) >= 3:
            break
        candidate = x_answer + offset
        if candidate != x_answer:
            distractors.add(candidate)

    options = [x_answer] + list(distractors)
    random.shuffle(options)
    sign = "+" if b >= 0 else "-"
    equation_text = f"Solve for x: {a}x {sign} {abs(b)} = {c}"
    return equation_text, options, x_answer


def run_linear_equation_task(gui):
    equation_text, options, answer = _generate_linear_equation()

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
                for rect, value in zip(base_rects, options):
                    if gui._srect(rect).collidepoint(event.pos):
                        return value == answer

        _fill_backdrop(gui)
        title = gui._font(26, bold=True).render("THINKING TASK - Linear Equation", True, TEXT_COLOR)
        gui.screen.blit(title, title.get_rect(center=gui._spt((BASE_WIDTH // 2, 190))))
        eq = gui._font(28, bold=True).render(equation_text, True, TEXT_COLOR)
        gui.screen.blit(eq, eq.get_rect(center=gui._spt((BASE_WIDTH // 2, 260))))

        for rect, value in zip(base_rects, options):
            screen_rect = gui._srect(rect)
            pygame.draw.rect(gui.screen, BUTTON_BG, screen_rect, border_radius=gui._slen(8))
            pygame.draw.rect(gui.screen, TEXT_COLOR, screen_rect, gui._slen(2), border_radius=gui._slen(8))
            text = gui._font(22, bold=True).render(f"x = {value}", True, TEXT_COLOR)
            gui.screen.blit(text, text.get_rect(center=screen_rect.center))

        pygame.display.flip()
