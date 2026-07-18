"""
Entry point for Part 2 (memory visualization).

Lets the user pick which sorting algorithm's pointer walk to watch. Neither
visualizer's own logic lives here - this file only dispatches to them:
- Bubble Sort: visualize_bubble_sort.py, called in-process.
- Quick Sort: quick_sort_visualizer.c, compiled with gcc and run as a
  subprocess so its full trace prints straight to the terminal.
"""

import subprocess
import sys
from pathlib import Path

from visualize_bubble_sort import visualize as visualize_bubble_sort

PROJECT_DIR = Path(__file__).parent
QUICK_SORT_SRC = PROJECT_DIR / "quick_sort_visualizer.c"
QUICK_SORT_BIN = PROJECT_DIR / "quick_sort_visualizer"


def run_quick_sort_visualizer():
    subprocess.run(["gcc", str(QUICK_SORT_SRC), "-o", str(QUICK_SORT_BIN)], check=True)
    subprocess.run([str(QUICK_SORT_BIN)], check=True)


def main():
    print("Part 2 - Memory Visualization")
    print("1) Bubble Sort (Python)")
    print("2) Quick Sort (C)")
    choice = input("Choose a visualization to run [1/2]: ").strip()

    if choice == "1":
        visualize_bubble_sort(["Dan", "Alice", "Charlie"])
    elif choice == "2":
        run_quick_sort_visualizer()
    else:
        print("Invalid choice.")
        sys.exit(1)


if __name__ == "__main__":
    main()
