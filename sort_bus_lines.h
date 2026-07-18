#ifndef EX2_REPO_SORTBUSLINES_H
#define EX2_REPO_SORTBUSLINES_H
// write only between #define EX2_REPO_SORTBUSLINES_H and #endif //EX2_REPO_SORTBUSLINES_H
#include <string.h>
#define NAME_LEN 21
/**
 * Represents a bus line with a name, travel distance, duration, and frequency.
 */
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

/**
 * Sorts an array of BusLine structures by their name field using the bubble sort algorithm.
 * @param start - pointer to the first BusLine in the array.
 * @param end - pointer one past the last BusLine in the array (exclusive).
 */
void bus_bubble_sort (BusLine *start, BusLine *end);

/**
 * Compares two BusLine structures according to a given sort type.
 * @param a - pointer to the first BusLine.
 * @param b - pointer to the second BusLine.
 * @param sort_type - the field by which to compare (DISTANCE, DURATION, or FREQUENCY).
 * @return a positive value if the first bus line is "greater" than the second,
 * zero or negative otherwise.
 */

int compare_bus_lines(BusLine *a, BusLine *b, SortType sort_type);

/**
 * Sorts an array of BusLine structures using the quick sort algorithm based on a given sort type.
 * @param start - pointer to the first BusLine in the array.
 * @param end - pointer one past the last BusLine in the array (exclusive).
 * @param sort_type - the field by which to sort the array.
 */

void bus_quick_sort (BusLine *start, BusLine *end, SortType sort_type);

/**
 * Partitions the array around a pivot element for the quick sort algorithm.
 * @param start - pointer to the first BusLine in the range.
 * @param end - pointer one past the last BusLine in the range (exclusive); the pivot is chosen from among start, the midpoint, and end - 1.
 * @param sort_type - the field by which to perform the partition.
 * @return a pointer to the pivot's final position in the sorted array.
 */
BusLine *partition (BusLine *start, BusLine *end, SortType sort_type);
// write only between #define EX2_REPO_SORTBUSLINES_H and #endif //EX2_REPO_SORTBUSLINES_H
#endif //EX2_REPO_SORTBUSLINES_H
