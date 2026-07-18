#include "sort_bus_lines.h"

void bus_bubble_sort (BusLine *start, BusLine *end)
{
    if (start >= end) return;
    size_t n = end - start;

    for (size_t i = 0; i < n; i++)
    {
         BusLine *pointer1 = start;
         BusLine *pointer2 = start+1;
         for (size_t j = 0; j < n-i-1; j++)
         {
             if (strcmp(pointer1->name, pointer2->name) > 0)
             {
                 BusLine temp = *pointer1;
                 *pointer1 = *pointer2;
                 *pointer2 = temp;

             }
             pointer1++;
             pointer2++;
         }
    }
}

int compare_bus_lines(BusLine *a, BusLine *b, SortType sort_type)
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

/**
 * Returns whichever of a/b/c would sort in the middle, using the same
 * <=-comparator the rest of the module uses.
 */
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

BusLine *partition (BusLine *start, BusLine *end, SortType sort_type)
{
    /* `end` is one-past-the-last element (exclusive); the true last element
     * -- where the Lomuto scan below keeps the pivot -- is `last = end - 1`. */
    BusLine *last = end - 1;

    /* Pick the median of start/middle/last as the pivot and move it to `last`
     * before the existing Lomuto scan below (which still assumes the pivot
     * lives at `last`). A fixed last-element pivot degrades to O(n^2) time on
     * already-sorted or reverse-sorted input; median-of-three defeats that
     * specific (very common) adversarial/accidental pattern. */
    BusLine *mid = start + (last - start) / 2;
    BusLine *pivot_candidate = median_of_three (start, mid, last, sort_type);
    if (pivot_candidate != last)
    {
        BusLine temp = *pivot_candidate;
        *pivot_candidate = *last;
        *last = temp;
    }

    size_t n = last - start;
    BusLine *left = start-1;
    BusLine *right = start;
    for (size_t i = 0; i < n; i++)
    {
        if (compare_bus_lines(right, last, sort_type))
        {
            left++;
            BusLine temp = *left;
            *left = *right;
            *right = temp;
        }
        right++;
    }
    BusLine *new_pivot = left+1;
    BusLine temp = *new_pivot;
    *new_pivot= *last;
    *last = temp;
    return new_pivot;
}

void bus_quick_sort (BusLine *start, BusLine *end, SortType sort_type)
{
    /* Iterative tail call: always recurse into the smaller side and loop on
     * the larger side. This bounds recursion depth to O(log n) regardless of
     * input order -- a plain "recurse both sides" quicksort with a
     * last-element pivot degrades to O(n) recursion depth (and O(n^2) time)
     * on already-sorted input, which can exhaust the call stack. */
    while (start < end)
    {
        BusLine *pivot = partition(start, end, sort_type);
        if (pivot - start < end - pivot - 1)
        {
            bus_quick_sort(start, pivot, sort_type);
            start = pivot + 1;
        }
        else
        {
            bus_quick_sort(pivot + 1, end, sort_type);
            end = pivot;
        }
    }
}


