"""Mini-game dispatch for the Part C route-economy game.

The actual mini-game implementations live in three small, independent
modules (one per cognitive category, so each can be read/edited/regenerated
without touching the others):
  - mg_thinking.py -- Flag Trivia (default -- Level 2), Linear Equation
                       (Level 3), Advanced Riddles pool (Level 4).
  - mg_memory.py   -- Shape Sequences (Level 2), Missing Number (default --
                       Level 3), Three Shells & A Ball (Level 4).
  - mg_agility.py  -- Single Timing Bar (Level 2), Rapid Targets /
                       Whack-a-Mole (default -- Level 3), Dual Timing Bars
                       (Level 4), plus the level-completion summary screen.

Level 1 has no mini-games at all (station/task_type are None on every one
of its routes -- see levels.py), so run_task() is never called for it.

This module is just the task_type + level -> concrete implementation lookup
that game_logic.py's attempt_board() calls through run_task(); it holds no
pygame drawing code itself. All underlying modules keep the global
countdown ticking via gui.advance_clock() every frame during their blocking
sub-loops (Admin Mode is orthogonal to this -- it only affects whether
attempt_board's money/time gate runs at all, not what happens once a
mini-game itself starts), and reuse the shared BASE_WIDTH x BASE_HEIGHT
design space and gui._s*/_font scaling helpers, so every task -- and the
summary screen -- stays visually consistent whether the window is resized
or fullscreen.
"""

from mg_agility import (  # noqa: F401  (show_level_summary re-exported)
    run_dual_timing_bars_task,
    run_single_timing_bar_task,
    run_whackamole_task,
    show_level_summary,
)
from mg_memory import run_missing_number_task, run_shape_sequence_task, run_shell_game_task
from mg_thinking import run_advanced_riddle_task, run_flag_trivia_task, run_linear_equation_task

LEVEL_2_INDEX = 1  # 0-based -- Level 2 swaps Agility + Memory for its own tasks
LEVEL_3_INDEX = 2  # 0-based -- Level 3 swaps Thinking for Linear Equation
LEVEL_4_INDEX = 3  # 0-based -- Level 4 swaps all 3 categories for its own tasks

# Defaults double as Level 3's assignments except for Thinking (overridden
# below), since Level 3 is otherwise the "baseline" mini-game set.
TASKS = {
    "agility": run_whackamole_task,
    "memory": run_missing_number_task,
    "thinking": run_flag_trivia_task,  # default -- Flag Trivia (Level 2)
}

# Per-level overrides of the default TASKS lookup above.
LEVEL_OVERRIDES = {
    LEVEL_2_INDEX: {
        "agility": run_single_timing_bar_task,
        "memory": run_shape_sequence_task,
    },
    LEVEL_3_INDEX: {"thinking": run_linear_equation_task},
    LEVEL_4_INDEX: {
        "thinking": run_advanced_riddle_task,
        "memory": run_shell_game_task,
        "agility": run_dual_timing_bars_task,
    },
}


def run_task(task_type, gui):
    """Default agility/memory/thinking implementations apply on every level
    with mini-games (2-4), except where LEVEL_OVERRIDES swaps in a
    level-specific variant -- Level 2's Single Timing Bar + Shape
    Sequences, Level 3's Linear Equation, Level 4's advanced trio -- see
    mg_thinking.py/mg_memory.py/mg_agility.py. Never called for Level 1,
    which has no station/task_type on any route."""
    overrides = LEVEL_OVERRIDES.get(gui.state.level_index, {})
    task_fn = overrides.get(task_type, TASKS[task_type])
    return task_fn(gui)
