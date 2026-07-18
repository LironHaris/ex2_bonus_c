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

## Code Structure

```
ex2_bonus_c/
├── CMakeLists.txt              # C project build configuration
├── fib.c / fib.h                # Example Fibonacci function - foundation for the Python binding
├── part2.py                     # Part 2 entry point - runs one of the two visualizations based on user choice
├── visualize_bubble_sort.py      # Bubble Sort memory visualization (invoked by part2.py)
└── quick_sort_visualizer.c       # Quick Sort memory visualization in C (compiled and run by part2.py)
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
