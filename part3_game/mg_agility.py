"""Agility-category station mini-games: Single Timing Bar (Level 2), Rapid
Targets / Whack-a-Mole (Level 3), and Dual Timing Bars (Level 4), plus the
level-completion summary screen (kept here rather than in a fourth file,
since neither mg_thinking.py nor mg_memory.py is a better thematic fit and
it's a similarly small, self-contained blocking overlay). Level 1 has no
Agility task at all (no mini-games whatsoever).

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

RED_ZONE = (200, 60, 50)
YELLOW_ZONE = (225, 190, 60)
NEEDLE_COLOR = (235, 232, 225)
BAR_BORDER = (20, 18, 16)

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


# Pre-game instruction overlay -- shared by every task in this module, drawn
# before that task's own gameplay loop starts. Gameplay/drawing/timers stay
# fully paused/hidden behind this static title + instructions + START TASK
# button until the player clicks it; the global background clock keeps
# ticking normally throughout (gui.advance_clock), same as every other
# blocking overlay in this game -- only each task's OWN internal
# timer/reveal/spawn logic is held back until then. Not used by
# show_level_summary below (not a task with a pass/fail outcome).
INTRO_START_BUTTON_RECT = pygame.Rect(BASE_WIDTH // 2 - 140, 380, 280, 60)
INTRO_BUTTON_COLOR = GREEN_ZONE


def _run_task_intro(gui, title, lines):
    """Blocks until the player clicks START TASK (or Admin Mode's SKIP TASK,
    handled by _pump like every other phase). `lines` is a list of
    instruction strings, one per rendered line. Returns False if the game
    ended while this screen was up."""
    while True:
        dt = gui.clock.tick(60) / 1000.0
        gui.advance_clock(dt)
        if gui.screen_state != "playing":
            return False

        started = False
        for event in _pump(gui):
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 \
                    and gui._srect(INTRO_START_BUTTON_RECT).collidepoint(event.pos):
                started = True

        _fill_backdrop(gui)
        title_surf = gui._font(30, bold=True).render(title, True, TEXT_COLOR)
        gui.screen.blit(title_surf, title_surf.get_rect(center=gui._spt((BASE_WIDTH // 2, 190))))
        y = 240
        for line in lines:
            surf = gui._font(18).render(line, True, DIM_TEXT_COLOR)
            gui.screen.blit(surf, surf.get_rect(center=gui._spt((BASE_WIDTH // 2, y))))
            y += 28

        button_rect = gui._srect(INTRO_START_BUTTON_RECT)
        pygame.draw.rect(gui.screen, INTRO_BUTTON_COLOR, button_rect, border_radius=gui._slen(10))
        pygame.draw.rect(gui.screen, TEXT_COLOR, button_rect, gui._slen(2), border_radius=gui._slen(10))
        label = gui._font(22, bold=True).render("START TASK", True, (250, 250, 245))
        gui.screen.blit(label, label.get_rect(center=button_rect.center))

        _draw_admin_skip_button(gui)
        pygame.display.flip()

        if started:
            return True


# ---------------------------------------------------------------------------
# Shared timing-bar building blocks (Level 2's single bar and Level 4's dual
# bars both use these).
# ---------------------------------------------------------------------------

# Fractional [start, end) bounds of each zone along a bar, left to right:
# red - yellow - green (the sweet spot) - yellow - red.
BAR_ZONES = [
    (0.0, 0.2, RED_ZONE),
    (0.2, 0.4, YELLOW_ZONE),
    (0.4, 0.6, GREEN_ZONE),
    (0.6, 0.8, YELLOW_ZONE),
    (0.8, 1.0, RED_ZONE),
]


class _TimingBar:
    """A needle that sweeps back and forth across the bar at a constant
    speed, bouncing off each end; the player wants it resting in the middle
    green sweet spot. Independently-paced/phased bars drift in and out of
    alignment with each other."""

    def __init__(self, speed):
        self.pos = random.uniform(0.0, 1.0)
        self.direction = random.choice([-1, 1])
        self.speed = speed  # fraction of the bar's width per second

    def update(self, dt):
        self.pos += self.direction * self.speed * dt
        if self.pos >= 1.0:
            self.pos, self.direction = 1.0, -1
        elif self.pos <= 0.0:
            self.pos, self.direction = 0.0, 1

    @property
    def in_green(self):
        return 0.4 <= self.pos <= 0.6


def _draw_timing_bar(gui, rect, bar):
    screen_rect = gui._srect(rect)
    for start, end, color in BAR_ZONES:
        zone_rect = pygame.Rect(
            screen_rect.left + int(start * screen_rect.width), screen_rect.top,
            max(1, int((end - start) * screen_rect.width)), screen_rect.height,
        )
        pygame.draw.rect(gui.screen, color, zone_rect)
    pygame.draw.rect(gui.screen, BAR_BORDER, screen_rect, gui._slen(2))

    needle_x = screen_rect.left + int(bar.pos * screen_rect.width)
    pygame.draw.line(
        gui.screen, NEEDLE_COLOR,
        (needle_x, screen_rect.top - gui._slen(6)), (needle_x, screen_rect.bottom + gui._slen(6)),
        gui._slen(4),
    )


def _bar_press_triggered(gui):
    """True if this frame's events include a left click or SPACE press --
    the universal "lock it in" trigger shared by both timing-bar tasks
    (position/target of the click doesn't matter, only its timing)."""
    for event in _pump(gui):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            return True
        if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
            return True
    return False


# ---------------------------------------------------------------------------
# Level 2: Single Timing Bar
# ---------------------------------------------------------------------------

SINGLE_BAR_RECT = pygame.Rect(BASE_WIDTH // 2 - 150, 280, 300, 44)


def run_single_timing_bar_task(gui):
    """One needle sweeps back and forth across a single bar; the player
    presses SPACE or clicks (anywhere) to lock it in. There's no timeout --
    the background level clock keeps ticking, but this task itself only
    resolves the instant the player actually presses: win if the needle is
    in the green sweet spot at that moment, lose otherwise. Gated behind a
    static pre-game instruction overlay (_run_task_intro) -- the needle
    never starts sweeping until the player clicks START TASK there."""
    bar = _TimingBar(speed=0.6)

    try:
        if not _run_task_intro(gui, "TIMING CHALLENGE",
                                ["Press SPACE or click when the needle is in the green zone!"]):
            return False

        while True:
            dt = gui.clock.tick(60) / 1000.0
            gui.advance_clock(dt)
            if gui.screen_state != "playing":
                return False
            bar.update(dt)

            if _bar_press_triggered(gui):
                return bar.in_green

            _fill_backdrop(gui)
            title = gui._font(26, bold=True).render("AGILITY TASK - Timing Bar", True, TEXT_COLOR)
            gui.screen.blit(title, title.get_rect(center=gui._spt((BASE_WIDTH // 2, 110))))
            hint = gui._font(18).render(
                "Press SPACE or click when the needle is in the green zone!", True, DIM_TEXT_COLOR)
            gui.screen.blit(hint, hint.get_rect(center=gui._spt((BASE_WIDTH // 2, 150))))

            _draw_timing_bar(gui, SINGLE_BAR_RECT, bar)

            _draw_admin_skip_button(gui)
            pygame.display.flip()
    except _AdminSkipTask:
        return True


# ---------------------------------------------------------------------------
# Level 3: Rapid Targets / Whack-a-Mole
# ---------------------------------------------------------------------------

def run_whackamole_task(gui):
    """5 circular targets, one at a time, each at a random position with its
    own tight countdown (shown as a shrinking ring). Miss any one -- either
    by not clicking it in time or running out of the level's own clock --
    and the task fails; all 5 hit in time passes it. Gated behind a static
    pre-game instruction overlay (_run_task_intro) -- circles never spawn
    and the per-target timer never starts until the player clicks START
    TASK there."""
    target_r = 34  # BASE-space radius
    time_limit_per_target = 1.4

    try:
        if not _run_task_intro(gui, "RAPID TARGETS CHALLENGE",
                                ["5 target circles will appear rapidly one after another.",
                                 "Click them as fast as you can!"]):
            return False

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

                _draw_admin_skip_button(gui)
                pygame.display.flip()

            if not hit:
                return False

        return True
    except _AdminSkipTask:
        return True


# ---------------------------------------------------------------------------
# Level 4: Dual Timing Bars
# ---------------------------------------------------------------------------

BAR_W, BAR_H = 300, 44
BAR_RECTS = [
    pygame.Rect(BASE_WIDTH // 2 - 320, 280, BAR_W, BAR_H),
    pygame.Rect(BASE_WIDTH // 2 + 20, 280, BAR_W, BAR_H),
]


def run_dual_timing_bars_task(gui):
    """Two independently-sweeping timing bars, side by side, each with its
    own green sweet spot. The player presses SPACE or clicks (anywhere) to
    lock both bars in at once -- there is no target to click and no
    timeout. The player is completely safe until they actually attempt a
    press: a loss is triggered ONLY if they press while at least one bar is
    outside its green zone; winning requires both bars to be in green at
    the instant of the press. Gated behind a static pre-game instruction
    overlay (_run_task_intro) -- neither needle starts sweeping until the
    player clicks START TASK there."""
    bars = [_TimingBar(speed=0.55), _TimingBar(speed=0.8)]

    try:
        if not _run_task_intro(gui, "DUAL TIMING CHALLENGE",
                                ["Two needles will sweep independently.",
                                 "Press SPACE or click ONLY when BOTH are in the green zone!"]):
            return False

        while True:
            dt = gui.clock.tick(60) / 1000.0
            gui.advance_clock(dt)
            if gui.screen_state != "playing":
                return False
            for bar in bars:
                bar.update(dt)

            if _bar_press_triggered(gui):
                return all(bar.in_green for bar in bars)

            _fill_backdrop(gui)
            title = gui._font(26, bold=True).render("AGILITY TASK - Dual Timing Bars", True, TEXT_COLOR)
            gui.screen.blit(title, title.get_rect(center=gui._spt((BASE_WIDTH // 2, 110))))
            hint = gui._font(18).render(
                "Press SPACE or click ONLY when BOTH needles are in the green zone!", True, DIM_TEXT_COLOR)
            gui.screen.blit(hint, hint.get_rect(center=gui._spt((BASE_WIDTH // 2, 150))))

            for bar, rect in zip(bars, BAR_RECTS):
                _draw_timing_bar(gui, rect, bar)

            _draw_admin_skip_button(gui)
            pygame.display.flip()
    except _AdminSkipTask:
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
