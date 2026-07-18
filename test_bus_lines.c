#include "test_bus_lines.h"
#include <stdlib.h>
#include <string.h>

int is_sorted_by_distance(const BusLine *start, const BusLine *end)
{
    if (start >= end) return 1;

    const BusLine *curr = start;
    while (curr + 1 < end)
    {
        if (curr->distance > (curr + 1)->distance)
        {
            return 0;
        }
        curr++;
    }
    return 1;
}

int is_sorted_by_duration (const BusLine *start, const BusLine *end)
{
    if (start >= end) return 1;

    const BusLine *curr = start;
    while (curr + 1 < end)
    {
        if (curr->duration > (curr + 1)->duration)
        {
            return 0;
        }
        curr++;
    }
    return 1;
}

int is_sorted_by_frequency (const BusLine *start, const BusLine *end)
{
    if (start >= end) return 1;

    const BusLine *curr = start;
    while (curr + 1 < end)
    {
        if (curr->frequency > (curr + 1)->frequency)
        {
            return 0;
        }
        curr++;
    }
    return 1;
}

int is_sorted_by_name (const BusLine *start, const BusLine *end)
{
    if (start >= end) return 1;

    const BusLine *curr = start;
    while (curr + 1 < end)
    {
        if (strcmp(curr->name, (curr+1)->name) > 0)
        {
            return 0;
        }
        curr++;
    }
    return 1;
}
int is_in_array(const BusLine *start, const BusLine *end, const BusLine *busline)
{
    const BusLine *curr = start;
    while (curr < end)
    {
        if (strcmp(curr->name, busline->name) == 0) return 1;
        curr++;
    }
    return 0;
}
int is_equal (const BusLine *start_sorted,
              const BusLine *end_sorted,
              const BusLine *start_original,
              const BusLine *end_original)
{
    if (end_original - start_original != end_sorted - start_sorted)
    {
        return 0;
    }
    const BusLine *curr = start_original;
    while (curr < end_original)
    {
        if (is_in_array(start_sorted,end_sorted,curr) == 0) return 0;
        curr++;
    }
    return 1;
}