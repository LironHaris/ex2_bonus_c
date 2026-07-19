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
Level 5 doesn't get a new mini-game module of its own -- its "Ultimate
Challenge" is a manager-level concern (run_ultimate_challenge_task, below)
that randomly reuses 3 of the functions already imported from Levels 2-4.

This module is just the task_type + level -> concrete implementation lookup
that game_logic.py's attempt_board() calls through run_task(); it holds no
pygame drawing code itself (aside from run_ultimate_challenge_task's own
orchestration, which just calls into the other modules' functions). All
underlying task functions keep the global countdown ticking via
gui.advance_clock() every frame during their blocking sub-loops (Admin Mode
is orthogonal to this for Levels 2-4 -- it only affects whether
attempt_board's money/time gate runs at all, not what happens once a
mini-game itself starts; Level 5's combo is the one exception, see below),
and reuse the shared BASE_WIDTH x BASE_HEIGHT design space and gui._s*/_font
scaling helpers, so every task -- and the summary screen -- stays visually
consistent whether the window is resized or fullscreen.
"""

import random

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
LEVEL_5_INDEX = 4  # 0-based -- Level 5 swaps all 3 categories for the Ultimate Challenge combo

# Defaults double as Level 3's assignments except for Thinking (overridden
# below), since Level 3 is otherwise the "baseline" mini-game set.
TASKS = {
    "agility": run_whackamole_task,
    "memory": run_missing_number_task,
    "thinking": run_flag_trivia_task,  # default -- Flag Trivia (Level 2)
}

# The 3 "tiers" the Ultimate Challenge (Level 5) draws from -- one function
# per category, taken straight from each earlier level's own assignment.
TIER_2_POOL = {
    "memory": run_shape_sequence_task,
    "agility": run_single_timing_bar_task,
    "thinking": run_flag_trivia_task,
}
TIER_3_POOL = {
    "memory": run_missing_number_task,
    "agility": run_whackamole_task,
    "thinking": run_linear_equation_task,
}
TIER_4_POOL = {
    "memory": run_shell_game_task,
    "agility": run_dual_timing_bars_task,
    "thinking": run_advanced_riddle_task,
}
_TIER_POOLS = [TIER_2_POOL, TIER_3_POOL, TIER_4_POOL]
_CATEGORIES = ["memory", "agility", "thinking"]


def run_ultimate_challenge_task(gui):
    """Level 5's station challenge: exactly one Memory, one Agility, and one
    Thinking task, each drawn from a different tier's pool (a random
    bijection between the 3 categories and the 3 tiers -- so no two of the
    three sub-tasks ever come from the same original level), then run
    back-to-back in a random order within a single blocking sequence. The
    background clock never stops across the whole combo, since each
    sub-task already keeps it ticking via gui.advance_clock() every frame;
    failing any one sub-task (or running out of global time mid-task, which
    surfaces the same way) fails the whole station challenge immediately,
    without running the remaining ones. Admin Mode bypasses this entire
    combo outright -- see game_logic.py's GameLogicMixin._toggle_admin_mode."""
    if gui.admin_mode:
        return True

    tiers = _TIER_POOLS[:]
    random.shuffle(tiers)  # tiers[i] is assigned to _CATEGORIES[i]
    selected = [tiers[i][category] for i, category in enumerate(_CATEGORIES)]
    random.shuffle(selected)  # randomize the run order too

    for task_fn in selected:
        if not task_fn(gui):
            return False
    return True


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
    LEVEL_5_INDEX: {
        "thinking": run_ultimate_challenge_task,
        "memory": run_ultimate_challenge_task,
        "agility": run_ultimate_challenge_task,
    },
}


def run_task(task_type, gui):
    """Default agility/memory/thinking implementations apply on every level
    with mini-games (2-4), except where LEVEL_OVERRIDES swaps in a
    level-specific variant -- Level 2's Single Timing Bar + Shape
    Sequences, Level 3's Linear Equation, Level 4's advanced trio, Level 5's
    Ultimate Challenge combo (which runs regardless of task_type -- see
    run_ultimate_challenge_task) -- see mg_thinking.py/mg_memory.py/
    mg_agility.py. Never called for Level 1, which has no station/task_type
    on any route."""
    overrides = LEVEL_OVERRIDES.get(gui.state.level_index, {})
    task_fn = overrides.get(task_type, TASKS[task_type])
    return task_fn(gui)
