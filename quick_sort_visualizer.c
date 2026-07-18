/*
 * Educational, standalone visualization of the pointer walk performed by
 * partition() / bus_quick_sort() in sort_bus_lines.c, printed as a full
 * terminal log (no screen clearing -- each step just prints below the
 * last, so the whole run stays visible and scrollable).
 *
 * This file does NOT include or link against sort_bus_lines.c/.h, is NOT
 * part of the CMake build, and is NOT used by the Python bindings or any
 * test suite -- it is fully self-contained (compile with a single
 * `gcc quick_sort_visualizer.c -o quick_sort_visualizer`) so it cannot
 * interfere with the production code in any way.
 *
 * compare_bus_lines/median_of_three/partition/bus_quick_sort below are local
 * copies of the exact logic in sort_bus_lines.c -- every pointer-arithmetic
 * line, comparison, and swap is kept verbatim. The only additions are the
 * printf calls that display the memory state at each step.
 */
#include <stdio.h>
#include <string.h>

#define ANSI_YELLOW "\033[1;33m"
#define ANSI_RED "\033[1;31m"
#define ANSI_RESET "\033[0m"

#define NAME_LEN 21
#define FAKE_BASE 0x1000L

typedef struct BusLine
{
    char name[NAME_LEN];
    int distance, duration, frequency;
} BusLine;

typedef enum SortType
{
    DISTANCE,
    DURATION,
    FREQUENCY
} SortType;

/* Verbatim copy of sort_bus_lines.c's compare_bus_lines(). */
static int compare_bus_lines (BusLine *a, BusLine *b, SortType sort_type)
{
    switch (sort_type)
    {
        case DISTANCE:
            return a->distance <= b->distance;
        case DURATION:
            return a->duration <= b->duration;
        case FREQUENCY:
            return a->frequency <= b->frequency;
        default:
            return 0;
    }
}

/* Verbatim copy of sort_bus_lines.c's median_of_three(). */
static BusLine *median_of_three (BusLine *a, BusLine *b, BusLine *c, SortType sort_type)
{
    if (compare_bus_lines (a, b, sort_type))
    {
        if (compare_bus_lines (b, c, sort_type)) return b;
        if (compare_bus_lines (a, c, sort_type)) return c;
        return a;
    }
    if (compare_bus_lines (a, c, sort_type)) return a;
    if (compare_bus_lines (b, c, sort_type)) return c;
    return b;
}

/* ---- Visualization plumbing (no equivalent in the original code) ---- */

static BusLine *g_array_base;
static int g_array_len;

static long fake_addr (const BusLine *p)
{
    long idx = (long) (p - g_array_base);
    return FAKE_BASE + idx * (long) sizeof (BusLine);
}

typedef struct
{
    const BusLine *ptr;
    const char *label;
} PtrTag;

static void print_state (const char *title, PtrTag *tags, int tag_count)
{
    printf ("    %s\n", title);

    printf ("      addr: ");
    for (int i = 0; i < g_array_len; i++) printf ("%#8lx ", fake_addr (g_array_base + i));
    printf ("\n      name: ");
    for (int i = 0; i < g_array_len; i++) printf ("%8s ", (g_array_base + i)->name);
    printf ("\n      dist: ");
    for (int i = 0; i < g_array_len; i++) printf ("%8d ", (g_array_base + i)->distance);
    printf ("\n      ptrs: ");
    for (int i = 0; i < g_array_len; i++)
    {
        char buf[24] = "";
        for (int t = 0; t < tag_count; t++)
        {
            if (tags[t].ptr == g_array_base + i)
            {
                if (buf[0] != '\0') strcat (buf, "/");
                strcat (buf, tags[t].label);
            }
        }
        printf ("%8s ", buf);
    }
    printf ("\n");

    /* Pointers that fall outside the visible array (left = start-1, or the
     * one-past-the-end `end`/`start` at the top level) get their own line,
     * since they have no cell to sit under. */
    for (int t = 0; t < tag_count; t++)
    {
        long idx = tags[t].ptr - g_array_base;
        if (idx < 0 || idx >= g_array_len)
        {
            printf ("      %-6s -> addr %#lx (%s)\n", tags[t].label, fake_addr (tags[t].ptr),
                    idx < 0 ? "before the array -- not a valid cell"
                            : "one past the array -- not a valid cell");
        }
    }
}

/* A short, colored banner line used to "flash" a comparison or swap event. */
static void flash (const char *color, const char *text)
{
    printf ("%s%s%s\n", color, text, ANSI_RESET);
}

/* ---- Local copies of partition()/bus_quick_sort() ---- */

static BusLine *visual_partition (BusLine *start, BusLine *end, SortType sort_type, int depth)
{
    BusLine *last = end - 1;

    printf ("[depth %d] partition(start=%#lx, end=%#lx [one past last])\n",
            depth, fake_addr (start), fake_addr (end));
    printf ("  last = end - 1  ->  addr %#lx (%s, distance=%d)\n",
            fake_addr (last), last->name, last->distance);
    PtrTag last_tags[] = {{start, "start"}, {end, "end"}, {last, "last"}};
    print_state ("current range:", last_tags, 3);

    BusLine *mid = start + (last - start) / 2;

    printf ("[depth %d] mid = start + (last-start)/2  ->  addr %#lx (%s, distance=%d)\n",
            depth, fake_addr (mid), mid->name, mid->distance);
    PtrTag mid_tags[] = {{start, "start"}, {last, "last"}, {mid, "mid"}};
    print_state ("current range:", mid_tags, 3);

    BusLine *pivot_candidate = median_of_three (start, mid, last, sort_type);

    printf ("[depth %d] median_of_three(start, mid, last)  ->  addr %#lx (%s, distance=%d)\n",
            depth, fake_addr (pivot_candidate), pivot_candidate->name, pivot_candidate->distance);
    PtrTag cand_tags[] = {{pivot_candidate, "cand"}, {last, "last"}};
    print_state ("current range:", cand_tags, 2);

    if (pivot_candidate != last)
    {
        PtrTag swap_tags[] = {{pivot_candidate, "cand"}, {last, "last"}};
        char msg[96];

        snprintf (msg, sizeof msg, ">>> SWAP: cand (distance=%d) <-> last (distance=%d) <<<",
                  pivot_candidate->distance, last->distance);
        flash (ANSI_RED, msg);
        printf ("[depth %d] pivot candidate != last  ->  swapping addr %#lx <-> addr %#lx\n",
                depth, fake_addr (pivot_candidate), fake_addr (last));
        print_state ("before swap:", swap_tags, 2);

        BusLine temp = *pivot_candidate;
        *pivot_candidate = *last;
        *last = temp;

        flash (ANSI_RED, ">>> SWAP COMPLETE <<<");
        print_state ("after swap:", swap_tags, 2);
    }
    else
    {
        printf ("[depth %d] pivot candidate already at last  ->  no swap needed\n", depth);
        PtrTag tags[] = {{last, "last"}};
        print_state ("current range:", tags, 1);
    }

    size_t n = last - start;
    BusLine *left = start - 1;
    BusLine *right = start;

    printf ("[depth %d] Lomuto scan begins: n=%zu\n", depth, n);
    printf ("  left = start-1 -> addr %#lx, right = start -> addr %#lx\n",
            fake_addr (left), fake_addr (right));
    PtrTag scan_start_tags[] = {{left, "left"}, {right, "right"}, {last, "last"}};
    print_state ("current range:", scan_start_tags, 3);

    for (size_t i = 0; i < n; i++)
    {
        int qualifies = compare_bus_lines (right, last, sort_type);
        char msg[96];

        printf ("[depth %d] scan step i=%zu: right -> addr %#lx (%s, distance=%d)\n",
                depth, i, fake_addr (right), right->name, right->distance);
        snprintf (msg, sizeof msg, ">>> compare_bus_lines(right=%d, last=%d) => %s <<<",
                  right->distance, last->distance, qualifies ? "TRUE (right <= pivot)" : "FALSE (right > pivot)");
        flash (ANSI_YELLOW, msg);
        PtrTag cmp_tags[] = {{left, "left"}, {right, "right"}, {last, "last"}};
        print_state ("current range:", cmp_tags, 3);

        if (qualifies)
        {
            left++;
            PtrTag swap_tags[] = {{left, "left"}, {right, "right"}, {last, "last"}};

            snprintf (msg, sizeof msg, ">>> SWAP: left (distance=%d) <-> right (distance=%d) <<<",
                      left->distance, right->distance);
            flash (ANSI_RED, msg);
            printf ("[depth %d] left++  ->  addr %#lx; swapping addr %#lx <-> addr %#lx\n",
                    depth, fake_addr (left), fake_addr (left), fake_addr (right));
            print_state ("before swap:", swap_tags, 3);

            BusLine temp = *left;
            *left = *right;
            *right = temp;

            flash (ANSI_RED, ">>> SWAP COMPLETE <<<");
            print_state ("after swap:", swap_tags, 3);
        }
        right++;

        printf ("[depth %d] right++  ->  addr %#lx\n", depth, fake_addr (right));
        PtrTag inc_tags[] = {{left, "left"}, {right, "right"}, {last, "last"}};
        print_state ("current range:", inc_tags, 3);
    }

    BusLine *new_pivot = left + 1;

    printf ("[depth %d] scan complete. new_pivot = left+1  ->  addr %#lx\n", depth, fake_addr (new_pivot));
    PtrTag np_tags[] = {{new_pivot, "pivot"}, {last, "last"}};
    print_state ("current range:", np_tags, 2);

    PtrTag final_tags[] = {{new_pivot, "pivot"}, {last, "last"}};
    char msg[96];

    snprintf (msg, sizeof msg, ">>> FINAL PIVOT PLACEMENT SWAP: pivot (distance=%d) <-> last (distance=%d) <<<",
              new_pivot->distance, last->distance);
    flash (ANSI_RED, msg);
    printf ("[depth %d] swapping addr %#lx <-> addr %#lx\n", depth, fake_addr (new_pivot), fake_addr (last));
    print_state ("before swap:", final_tags, 2);

    BusLine temp = *new_pivot;
    *new_pivot = *last;
    *last = temp;

    flash (ANSI_RED, ">>> SWAP COMPLETE <<<");
    print_state ("after swap:", final_tags, 2);

    printf ("[depth %d] partition returns pivot at addr %#lx (%s, distance=%d)\n",
            depth, fake_addr (new_pivot), new_pivot->name, new_pivot->distance);
    print_state ("current range:", final_tags, 2);

    return new_pivot;
}

static void visual_quick_sort (BusLine *start, BusLine *end, SortType sort_type, int depth)
{
    while (start < end)
    {
        printf ("[depth %d] quick_sort range [addr %#lx, addr %#lx)\n",
                depth, fake_addr (start), fake_addr (end));
        PtrTag range_tags[] = {{start, "start"}, {end, "end"}};
        print_state ("current range:", range_tags, 2);

        BusLine *pivot = visual_partition (start, end, sort_type, depth);

        long left_count = pivot - start;
        long right_count = end - pivot - 1;
        PtrTag decision_tags[] = {{start, "start"}, {pivot, "pivot"}, {end, "end"}};

        printf ("[depth %d] left side has %ld element(s), right side has %ld element(s)\n",
                depth, left_count, right_count);
        print_state ("current range:", decision_tags, 3);

        if (pivot - start < end - pivot - 1)
        {
            printf ("[depth %d] recursing into LEFT side, then looping on RIGHT side\n", depth);
            print_state ("current range:", decision_tags, 3);

            visual_quick_sort (start, pivot, sort_type, depth + 1);
            start = pivot + 1;
        }
        else
        {
            printf ("[depth %d] recursing into RIGHT side, then looping on LEFT side\n", depth);
            print_state ("current range:", decision_tags, 3);

            visual_quick_sort (pivot + 1, end, sort_type, depth + 1);
            end = pivot;
        }
    }
}

int main (void)
{
    BusLine lines[3] = {
        {"Dan", 20, 0, 0},
        {"Alice", 30, 0, 0},
        {"Charlie", 10, 0, 0},
    };
    g_array_base = lines;
    g_array_len = 3;

    printf ("sizeof(BusLine) = %zu bytes -- that is the REAL, compiler-computed stride between\n",
            sizeof (BusLine));
    printf ("cells below. Only the starting address (0x1000) is a fake display base; the\n");
    printf ("spacing itself is genuine, not a rounded stand-in.\n");
    PtrTag initial_tags[] = {{lines, "start"}, {lines + 3, "end"}};
    print_state ("initial array:", initial_tags, 2);

    visual_quick_sort (lines, lines + 3, DISTANCE, 0);

    PtrTag final_tags[] = {{lines, "start"}, {lines + 3, "end"}};
    print_state ("final sorted array (by distance):", final_tags, 2);
    printf ("\nDone.\n");
    fflush (stdout);

    return 0;
}
