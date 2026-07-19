"""Mini-game dispatch for the Part C route-economy game.

The actual mini-game implementations live in three small, independent
modules (one per cognitive category, so each can be read/edited/regenerated
without touching the others):
  - mg_thinking.py -- Flag Trivia (Levels 1 & 3) and Linear Equation (Level 2).
  - mg_memory.py   -- Missing Number (Levels 1, 2 & 3).
  - mg_agility.py  -- Rapid Targets / Whack-a-Mole (Levels 1, 2 & 3), plus
                       the level-completion summary screen.

This module is just the task_type + level -> concrete implementation lookup
that game_logic.py's attempt_board() calls through run_task(); it holds no
pygame drawing code itself. All three underlying modules keep the global
countdown ticking via gui.advance_clock() every frame during their blocking
sub-loops, and reuse the shared BASE_WIDTH x BASE_HEIGHT design space and
gui._s*/_font scaling helpers, so every task -- and the summary screen --
stays visually consistent whether the window is resized or fullscreen.
"""

from mg_agility import run_whackamole_task, show_level_summary  # noqa: F401  (show_level_summary re-exported)
from mg_memory import run_missing_number_task
from mg_thinking import run_flag_trivia_task, run_linear_equation_task

LEVEL_2_INDEX = 1  # 0-based -- Level 2 is the only level using Linear Equation instead of Flag Trivia

TASKS = {
    "agility": run_whackamole_task,
    "memory": run_missing_number_task,
    "thinking": run_flag_trivia_task,  # overridden for Level 2 below
}


def run_task(task_type, gui):
    """agility/memory use the same implementation on every level that has
    mini-games (1-3). thinking differs: Level 2 gets Linear Equation, Levels
    1 and 3 get Flag Trivia -- see mg_thinking.py."""
    if task_type == "thinking" and gui.state.level_index == LEVEL_2_INDEX:
        return run_linear_equation_task(gui)
    return TASKS[task_type](gui)
