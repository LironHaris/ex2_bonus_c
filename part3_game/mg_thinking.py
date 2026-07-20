"""Thinking-category station mini-games: Flag Trivia (default -- Level 2),
Linear Equation (Level 3), and the Advanced Riddles pool (Level 4). Level 1
has no Thinking task at all (no mini-games whatsoever). See minigames.py
for the task_type + level -> function dispatch that picks between them.

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

# Admin Mode's SKIP TASK button -- drawn on every frame of every task below
# while gui.admin_mode is on, bottom-right corner. Admin Mode no longer
# auto-bypasses mini-games (they always launch and must be played normally);
# this button is the explicit, player-triggered way to instantly pass one.
ADMIN_SKIP_RECT = pygame.Rect(BASE_WIDTH - 190, 540, 170, 42)
ADMIN_SKIP_BG = (120, 50, 40)
ADMIN_SKIP_BORDER = (235, 180, 90)


class _AdminSkipTask(Exception):
    """Raised by _pump() when Admin Mode's SKIP TASK button is clicked, to
    unwind out of a task's blocking loop in one step and count as a pass --
    caught once at the top of each run_*_task()."""


def _draw_admin_skip_button(gui):
    if not gui.admin_mode:
        return
    rect = gui._srect(ADMIN_SKIP_RECT)
    pygame.draw.rect(gui.screen, ADMIN_SKIP_BG, rect, border_radius=gui._slen(8))
    pygame.draw.rect(gui.screen, ADMIN_SKIP_BORDER, rect, gui._slen(2), border_radius=gui._slen(8))
    label = gui._font(15, bold=True).render("SKIP TASK (ADMIN)", True, ADMIN_SKIP_BORDER)
    gui.screen.blit(label, label.get_rect(center=rect.center))

# Flags are drawn from plain pygame primitives (rects/a circle) -- no image
# assets. Each entry is the list of bar colors; orientation says whether
# they're read left-to-right or top-to-bottom.
FLAG_BARS = {
    "France": [(0, 40, 108), (255, 255, 255), (239, 65, 53)],
    "Italy": [(0, 146, 70), (255, 255, 255), (206, 43, 55)],
    "Germany": [(0, 0, 0), (221, 0, 0), (255, 206, 0)],
    "Belgium": [(0, 0, 0), (255, 213, 0), (237, 41, 57)],
    "Netherlands": [(174, 28, 40), (255, 255, 255), (33, 70, 139)],
    "Ireland": [(22, 155, 76), (255, 255, 255), (255, 136, 53)],
    "Austria": [(237, 41, 57), (255, 255, 255), (237, 41, 57)],
    "Ukraine": [(65, 155, 219), (255, 213, 0)],
}
FLAG_ORIENTATION = {
    "France": "vertical", "Italy": "vertical", "Germany": "horizontal",
    "Belgium": "vertical", "Netherlands": "horizontal",
    "Ireland": "vertical", "Austria": "horizontal", "Ukraine": "horizontal",
}
FLAG_BORDER = (20, 18, 16)
JAPAN_BG = (255, 255, 255)
JAPAN_DISC = (188, 0, 45)


def _fill_backdrop(gui):
    """Full-window dark backdrop for a mini-game, independent of the map's
    own letterboxed content area -- this covers the whole actual window."""
    gui.screen.fill(BACKDROP_COLOR)


def _pump(gui):
    """Drain the event queue, handling window management first, then Admin
    Mode's SKIP TASK button (raises _AdminSkipTask if clicked). Returns the
    remaining events for task-specific handling."""
    events = pygame.event.get()
    remaining = []
    for e in events:
        if gui.handle_window_event(e):
            continue
        if gui.admin_mode and e.type == pygame.MOUSEBUTTONDOWN and e.button == 1 \
                and gui._srect(ADMIN_SKIP_RECT).collidepoint(e.pos):
            raise _AdminSkipTask()
        remaining.append(e)
    return remaining


# ---------------------------------------------------------------------------
# Level 2 (default Thinking task): Flag Trivia
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


FLAG_COUNTRIES = [
    "France", "Italy", "Germany", "Japan", "Belgium", "Netherlands",
    "Ireland", "Austria", "Ukraine",
]


def run_flag_trivia_task(gui):
    answer = random.choice(FLAG_COUNTRIES)
    distractors = random.sample([c for c in FLAG_COUNTRIES if c != answer], 3)
    choices = [answer] + distractors
    random.shuffle(choices)

    flag_rect = pygame.Rect(BASE_WIDTH // 2 - 90, 140, 180, 120)

    button_w, button_h, gap = 170, 56, 16
    total_w = len(choices) * button_w + (len(choices) - 1) * gap
    left = BASE_WIDTH // 2 - total_w // 2
    base_rects = [
        pygame.Rect(left + i * (button_w + gap), 380, button_w, button_h)
        for i in range(len(choices))
    ]

    try:
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

            _draw_admin_skip_button(gui)
            pygame.display.flip()
    except _AdminSkipTask:
        return True


# ---------------------------------------------------------------------------
# Level 3: Linear Equation (ax + b = c)
# ---------------------------------------------------------------------------

def _generate_linear_equation():
    """A random ax + b = c with an integer solution, plus 3 near-miss
    integer distractors so guessing isn't trivially obvious from magnitude
    alone. Wide randomized pool: a in [2, 9], b in [-15, 15], x in
    [-12, 12] \\ {0}."""
    a = random.randint(2, 9)
    x_answer = random.choice([n for n in range(-12, 13) if n != 0])
    b = random.randint(-15, 15)
    c = a * x_answer + b

    distractors = set()
    offsets = [-4, -3, -2, -1, 1, 2, 3, 4]
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

    try:
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

            _draw_admin_skip_button(gui)
            pygame.display.flip()
    except _AdminSkipTask:
        return True


# ---------------------------------------------------------------------------
# Level 4: Advanced Riddles pool -- a System of 2 Equations riddle, or one of
# two anonymized numeric-sequence puzzles (their underlying rule is never
# named in the UI, only the raw numbers are shown -- see run_advanced_riddle_task).
# ---------------------------------------------------------------------------

_SEQUENCE_PROMPT = "Complete the sequence by choosing the next number: {sequence}, ...?"


def _generate_fibonacci_riddle():
    """A Fibonacci-style sequence from two random positive seeds (each term
    is the sum of the previous two); the player names the next term. The
    underlying rule is never stated -- only the raw numbers are shown."""
    a = random.randint(1, 4)
    b = random.randint(1, 4)
    seq = [a, b]
    for _ in range(4):
        seq.append(seq[-1] + seq[-2])
    answer = seq[-1] + seq[-2]

    distractors = {answer + 1, answer - 1, seq[-1] * 2, seq[-1] + seq[-3]}
    distractors.discard(answer)
    distractors = list(distractors)[:3]
    while len(distractors) < 3:
        candidate = answer + random.choice([-3, -2, 2, 3, 4])
        if candidate != answer and candidate not in distractors and candidate > 0:
            distractors.append(candidate)

    options = [str(answer)] + [str(d) for d in distractors]
    random.shuffle(options)
    sequence_text = ", ".join(str(n) for n in seq)
    question_text = _SEQUENCE_PROMPT.format(sequence=sequence_text)
    return question_text, options, str(answer)


def _digit_loop_count(number_str):
    """0, 6, and 9 each have exactly 1 closed loop; 8 has exactly 2; every
    other digit has 0. Internal only -- this rule is never shown to the
    player, it just drives the hidden pattern below."""
    count = 0
    for ch in number_str:
        if ch in ("0", "6", "9"):
            count += 1
        elif ch == "8":
            count += 2
    return count


def _make_number_with_loop_count(target_count):
    """Build a random digit string whose total closed-loop count (per
    _digit_loop_count) is exactly target_count, padded with a few
    non-loop filler digits for visual variety."""
    loop_digits_1 = ["0", "6", "9"]  # 1 loop each
    loop_digits_2 = ["8"]            # 2 loops each
    filler_digits = ["1", "2", "3", "4", "5", "7"]  # 0 loops each

    digits = []
    remaining = target_count
    while remaining > 0:
        if remaining >= 2 and random.random() < 0.5:
            digits.append(random.choice(loop_digits_2))
            remaining -= 2
        else:
            digits.append(random.choice(loop_digits_1))
            remaining -= 1
    for _ in range(random.randint(0, 2)):
        digits.append(random.choice(filler_digits))
    random.shuffle(digits)

    number_str = "".join(digits)
    if number_str[0] == "0" and len(number_str) > 1:
        # Cosmetic only: rotate a non-zero digit to the front so the number
        # doesn't display with a leading zero.
        for i, ch in enumerate(number_str):
            if ch != "0":
                number_str = number_str[i] + number_str[:i] + number_str[i + 1:]
                break
    return number_str


def _generate_digit_circle_riddle():
    """A sequence of numbers whose hidden rule is that each term's total
    closed-loop count is one more than the previous term's. The rule itself
    is never shown -- only the raw numbers -- so the player must infer the
    pattern purely from the sequence, same as the Fibonacci-style puzzle."""
    start_count = random.randint(1, 2)
    term_counts = [start_count, start_count + 1, start_count + 2]
    terms = [_make_number_with_loop_count(c) for c in term_counts]

    answer_count = start_count + 3
    answer = _make_number_with_loop_count(answer_count)

    distractors = set()
    for offset in (-1, 1, 2):
        candidate_count = answer_count + offset
        if candidate_count >= 1:
            candidate = _make_number_with_loop_count(candidate_count)
            if candidate != answer:
                distractors.add(candidate)
    distractors = list(distractors)[:3]
    while len(distractors) < 3:
        candidate = _make_number_with_loop_count(random.randint(1, 6))
        if candidate != answer and candidate not in distractors:
            distractors.append(candidate)

    options = [answer] + distractors
    random.shuffle(options)
    sequence_text = ", ".join(terms)
    question_text = _SEQUENCE_PROMPT.format(sequence=sequence_text)
    return question_text, options, answer


def _generate_system_riddle():
    """A system of 2 linear equations in x and y with a unique small integer
    solution: x + y = S, {a2}x - y = D."""
    x_answer = random.randint(1, 9)
    y_answer = random.randint(1, 9)
    while y_answer == x_answer:
        y_answer = random.randint(1, 9)
    eq1_c = x_answer + y_answer
    a2 = random.choice([2, 3])
    eq2_c = a2 * x_answer - y_answer
    answer = f"({x_answer}, {y_answer})"

    distractor_pairs = {
        (y_answer, x_answer),
        (x_answer + 1, y_answer - 1),
        (x_answer - 1, y_answer + 1),
        (x_answer + 1, y_answer),
        (x_answer, y_answer + 1),
    }
    distractor_pairs.discard((x_answer, y_answer))
    distractors = [f"({px}, {py})" for px, py in list(distractor_pairs)[:3]]

    options = [answer] + distractors
    random.shuffle(options)
    question_text = f"Solve the system: x + y = {eq1_c},  {a2}x - y = {eq2_c}.  Find (x, y)."
    return question_text, options, answer


_SEQUENCE_RIDDLE_GENERATORS = [_generate_fibonacci_riddle, _generate_digit_circle_riddle]


def run_advanced_riddle_task(gui):
    """Each attempt is a coin flip between the System of 2 Equations riddle
    (50%) and one of the two Sequence puzzles -- Fibonacci or Digit Circle
    Count, picked with equal probability between themselves (50% combined,
    25% each) -- then rendered with the same multiple-choice button pattern
    as the other Thinking tasks."""
    if random.random() < 0.5:
        question_text, options, answer = _generate_system_riddle()
    else:
        question_text, options, answer = random.choice(_SEQUENCE_RIDDLE_GENERATORS)()

    button_w, button_h, gap = 190, 60, 18
    total_w = len(options) * button_w + (len(options) - 1) * gap
    left = BASE_WIDTH // 2 - total_w // 2
    base_rects = [
        pygame.Rect(left + i * (button_w + gap), 380, button_w, button_h)
        for i in range(len(options))
    ]

    try:
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
            title = gui._font(26, bold=True).render("THINKING TASK - Advanced Riddle", True, TEXT_COLOR)
            gui.screen.blit(title, title.get_rect(center=gui._spt((BASE_WIDTH // 2, 110))))
            question_surf = gui._font(21, bold=True).render(question_text, True, TEXT_COLOR)
            if question_surf.get_width() > BASE_WIDTH - 80:
                question_surf = gui._font(17, bold=True).render(question_text, True, TEXT_COLOR)
            gui.screen.blit(question_surf, question_surf.get_rect(center=gui._spt((BASE_WIDTH // 2, 260))))

            for rect, value in zip(base_rects, options):
                screen_rect = gui._srect(rect)
                pygame.draw.rect(gui.screen, BUTTON_BG, screen_rect, border_radius=gui._slen(8))
                pygame.draw.rect(gui.screen, TEXT_COLOR, screen_rect, gui._slen(2), border_radius=gui._slen(8))
                text = gui._font(20, bold=True).render(value, True, TEXT_COLOR)
                gui.screen.blit(text, text.get_rect(center=screen_rect.center))

            _draw_admin_skip_button(gui)
            pygame.display.flip()
    except _AdminSkipTask:
        return True
