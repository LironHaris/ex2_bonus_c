# ex2_bonus_c — Bus Lines Sorting & AI Agents Practice

Bonus project for **C/C++ for Practical Algorithmics (67315)**, Hebrew University of Jerusalem, Spring 2026. Builds on the bus-lines sorting exercise (Exercise 2) using AI coding agents, per the course's *"Safe and Creative Use of AI Coding Agents"* assignment.

## Implemented Parts

### Part 1 — Introductory Python Binding Setup
Establishes the foundational C project structure and architecture that a later Python binding will wrap, using a small `Fibonacci` function as the practice case before tackling the full binding. This step is purely architectural — **no execution is required**.

- **`fib.c`** / **`fib.h`** — the example C function (`CFib`) used to establish the binding pattern.
- **`CMakeLists.txt`** — the C project's build configuration.

### Part 2 — Memory Visualization
An educational, text-based memory visualization that demonstrates **pointer movement and pointer arithmetic** for the sorting algorithms used in the project: **Bubble Sort** and **Quick Sort**. Both visualizers re-implement the exact pointer logic of the original sorting functions (without modifying or calling them) purely to print step-by-step memory diagrams — array cells, fake addresses, and pointer positions at each step.

- **`visualize_bubble_sort.py`** — pure-Python visualization of the pointer walk performed by `bus_bubble_sort()`.
- **`quick_sort_visualizer.c`** — self-contained C visualization of the pointer walk performed by `partition()` / `bus_quick_sort()`, printed as a full terminal log.
- **`part2.py`** — the unified entry point for Part 2; lets the user choose which visualization to run.

### Part 3 — Interactive Route-Economy Game (Bonus Extension)

A full, playable **pygame** GUI game built directly on top of the C sorting core from Exercise 2 and Part 2 above — no reimplementation, no mocking. Every time the player sorts the bus-line list in-game, the click runs straight through `python_bindings_module/bus_module.py`'s `ctypes` bindings into the real compiled `bus_bubble_sort()` / `bus_quick_sort()` C functions and back.

#### General Concept

The player is a student racing a real-time countdown clock and a limited cash budget across **5 escalating levels** of a Jerusalem-themed public transit network, trying to reach the university before time or money runs out.

- **Transit simulation.** Each level is a small graph of HOME, UNIVERSITY, and (from Level 3 onward) transfer-hub nodes, connected by bus lines with their own price, distance, duration, and departure frequency. Sorting the line list — by name (Bubble Sort) or by distance/duration (Quick Sort) — is the whole point of the Trip Planner panel, and always calls the genuine C implementation.
- **The Time Leap — Waiting vs. Transit time.** Boarding a line costs time in two distinct, sequential phases, not one lump sum: the **Wait Jump** (Phase 1) deducts the wait for that line's *next scheduled departure* the instant boarding is confirmed, before anything else happens; the **Transit Duration** (Phase 2) deducts the route's own travel time only once the bus has actually finished animating its way to the destination. This split models a real commute more faithfully than a single flat deduction — a rider still "loses" the waiting time even if the ride itself is interrupted or re-routed.
- **Advanced cognitive challenges.** Selected intermediate stations gate boarding behind a mini-game from one of three categories — **Thinking** (trivia, linear equations, riddles), **Agility** (timing bars, whack-a-mole), **Memory** (sequence recall, the shell game, missing-number puzzles) — with harder variants unlocked level by level. Level 5's stations escalate this into the **Ultimate Challenge**: a randomized, back-to-back combo of one Thinking, one Agility, and one Memory task, each drawn from a different earlier level's difficulty tier, run as a single sequence where failing any one sub-task fails the whole station.
- **Interactive Tutorial walkthrough.** A 7-step guided onboarding flow, reachable from the title screen and driven by its own small state machine (`self.tutorial_step`), teaches the Status Bar, map navigation, the Electronic Sign dashboard, the Trip Planner, station tasks, and Admin Mode — each step spotlighting the relevant UI element against a small, self-contained mock scene, entirely separate from any real level or save state.

#### Code Architecture & Structure

The GUI (`part3_game/`) is deliberately split across many small, single-purpose files rather than one large script, so any one concern can be read, edited, or regenerated without touching the others:

| File | Responsibility |
|---|---|
| `engine.py` | Pure game-state transitions and rules (`can_board`, `board_route`, `tick`, win/loss, ...) plus the C sorting bridge (`sort_routes`) — no pygame, no I/O. |
| `models.py` / `levels.py` | The `GameState` / `BusRoute` / `LevelConfig` dataclasses, and the 5 hand-authored level layouts. |
| `game.py` | Assembles `GameGUI` from the Mixins below; owns window setup, responsive scaling, and the top-level event/render loop. |
| `game_logic.py` | **`GameLogicMixin`** — sorting, the live clock, boarding (the Wait Jump + Transit Duration split), win/loss detection, Admin Mode, and the global ESC pause overlay. |
| `game_animation.py` | **`AnimationMixin`** — the bus-driving animation and the random traffic-delay popup. |
| `game_map_render.py` | **`MapRendererMixin`** — buildings, roads, and every map/node icon. |
| `game_panels.py` | **`PanelsMixin`** — the status bar, the Electronic Sign, the Trip Planner, and the title/end screens. |
| `game_tutorial.py` | **`TutorialMixin`** — the interactive walkthrough's mock scene, spotlight-dim effect, and step navigation. |
| `game_constants.py` / `game_geometry.py` | Shared layout rects, colors, copy text, and stateless math/formatting helpers used across every file above. |
| `minigames.py` | The `task_type` + level → concrete mini-game function lookup (`run_task`), plus Level 5's Ultimate Challenge orchestration. |
| `mg_thinking.py`, `mg_memory.py`, `mg_agility.py` | The 9 individual mini-game implementations (3 per category), each a small, self-contained, blocking pygame event loop. |

**Why Mixins:** `game.py`'s `GameGUI` class inherits from every `*Mixin` above (`class GameGUI(GameLogicMixin, AnimationMixin, MapRendererMixin, PanelsMixin, TutorialMixin)`), so every method — regardless of which file it's defined in — operates on the exact same shared `self` instance. This keeps each file focused on one concern while behaving, at runtime, as a single unified class.

**A single, never-pausing clock.** The countdown (`GameLogicMixin.advance_clock`) is called once per frame from `game.py`'s main loop *and* from inside every blocking sub-loop — each mini-game task, the bus animation, the traffic-delay popup, the level-completion summary — so the clock keeps ticking down in real time no matter which modal currently owns the screen. It only truly stops when the player leaves the "playing" state entirely: winning, losing, or opening the global pause overlay (ESC), which freezes it precisely by never calling `advance_clock()` while paused.

**Admin Mode — a safety bypass, not a cheat-everything switch.** Toggled via the on-screen ADMIN MODE button, it lifts only the *validation* gates around boarding — money/time affordability and station connectivity — so a developer can board any line from any station on the map for isolated testing, while the economy (time and cash) still simulates exactly as in normal play, including going negative. Mini-games are **never** auto-skipped by Admin Mode: they always launch and must be played, or explicitly dismissed via each task's own on-screen **"SKIP TASK (ADMIN)"** button. This same "unwind cleanly from anywhere" philosophy also powers the global pause system: RETURN TO MAIN MENU can be clicked from arbitrarily deep inside a mini-game's blocking loop and still unwinds all the way back to the title screen in one step.

## Code Structure

```
ex2_bonus_c/
├── CMakeLists.txt                # C project build configuration
├── fib.c / fib.h                  # Example Fibonacci function - foundation for the Python binding
├── part2.py                       # Part 2 entry point - runs one of the two visualizations based on user choice
├── visualize_bubble_sort.py        # Bubble Sort memory visualization (invoked by part2.py)
├── quick_sort_visualizer.c         # Quick Sort memory visualization in C (compiled and run by part2.py)
├── sort_bus_lines.c / .h            # The real C sorting core (bubble + quick sort) shared by every part
├── requirements.txt                # Python dependencies (pytest, pygame) for Parts 2-3
├── python_bindings_module/
│   └── bus_module.py                # ctypes bindings -> libsortbus.so (the compiled C sorting core)
└── part3_game/                     # Part 3 - the interactive route-economy game
    ├── game.py                      # Entry point - assembles GameGUI, owns the event/render loop
    ├── engine.py                    # Game-state rules + the C sorting bridge (sort_routes)
    ├── models.py / levels.py        # State/route/level dataclasses and the 5 level layouts
    ├── game_logic.py                # GameLogicMixin - clock, boarding, Admin Mode, pause overlay
    ├── game_animation.py            # AnimationMixin - bus animation, traffic-delay popup
    ├── game_map_render.py           # MapRendererMixin - buildings, roads, node icons
    ├── game_panels.py               # PanelsMixin - status bar, Electronic Sign, Trip Planner, title/end screens
    ├── game_tutorial.py             # TutorialMixin - the interactive walkthrough
    ├── game_constants.py            # Shared colors, layout rects, and copy text
    ├── game_geometry.py             # Shared stateless math/formatting helpers
    ├── minigames.py                 # task_type + level -> mini-game dispatch, Level 5's Ultimate Challenge
    └── mg_thinking.py / mg_memory.py / mg_agility.py   # The 9 individual mini-game implementations
```

## How to Run

**Part 1:** No execution needed at this stage — it is architectural setup only.

**Part 2:**

```bash
python3 part2.py
```

You'll be prompted to choose a visualization:

- `1` — runs the Bubble Sort visualization directly in Python.
- `2` — compiles `quick_sort_visualizer.c` with `gcc` and runs it, printing the full trace at once.

> **Note:** Running option `2` requires `gcc` to be available on your `PATH`, since `part2.py` compiles the visualizer on demand.

**Part 3:**

Part 3 is a graphical `pygame` application, so it needs an actual display — on WSL (Ubuntu/Linux under Windows), that means **WSLg** (bundled with Windows 11 / recent Windows 10 WSL builds) or an X server; on native Linux or macOS, any standard desktop session works out of the box.

1. **Check/install the dependencies** (from the repository root):

   ```bash
   python3 -m pip install -r requirements.txt
   ```

   This installs `pygame` (the GUI/rendering engine) and `pytest` (used by the project's test suites). To just verify `pygame` is already available without reinstalling anything:

   ```bash
   python3 -c "import pygame; print(pygame.ver)"
   ```

2. **Make sure the C sorting core is built.** `part3_game/engine.py` calls into it via `python_bindings_module/bus_module.py`, which loads the compiled `libsortbus.so` through `ctypes` — build it first if it isn't already present:

   ```bash
   gcc -shared -fPIC -o python_bindings_module/libsortbus.so sort_bus_lines.c
   ```

3. **Launch the game:**

   ```bash
   python3 part3_game/game.py
   ```

   The window opens on the title screen — click **START GAME** to jump straight into Level 1, or **TUTORIAL** for the guided 7-step walkthrough first. The window is resizable and can be toggled fullscreen with `F11`; press `ESC` at any time during a level to pause.

> **Note (WSL only):** if the window fails to open with a display/driver error, confirm WSLg is active by running `echo $DISPLAY` (it should print something, e.g. `:0`) — if it's empty, update WSL (`wsl --update` from Windows PowerShell) or install an X server such as VcXsrv and export `DISPLAY` manually before retrying.
