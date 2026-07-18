#ifndef EX2_REPO_TESTBUSLINES_H
#define EX2_REPO_TESTBUSLINES_H
// write only between #define EX2_REPO_TESTBUSLINES_H and #endif //EX2_REPO_TESTBUSLINES_H
#include "sort_bus_lines.h"
#include <string.h>
/**
 * Checks if the given array is sorted by distance in non-descending order.
 * @param start - pointer to the first BusLine in the array.
 * @param end - pointer one past the last BusLine in the array (exclusive).
 * @return 1 if the array is sorted by distance, 0 otherwise.
 */
int is_sorted_by_distance (const BusLine *start, const BusLine *end);

/**
 * Checks if the given array is sorted by duration in non-descending order.
 * @param start - pointer to the first BusLine in the array.
 * @param end - pointer one past the last BusLine in the array (exclusive).
 * @return 1 if the array is sorted by duration, 0 otherwise.
 */
int is_sorted_by_duration (const BusLine *start, const BusLine *end);

/**
 * Checks if the given array is sorted by frequency in non-descending order.
 * @param start - pointer to the first BusLine in the array.
 * @param end - pointer one past the last BusLine in the array (exclusive).
 * @return 1 if the array is sorted by frequency, 0 otherwise.
 */
int is_sorted_by_frequency (const BusLine *start, const BusLine *end);

/**
 * Checks if the given array is sorted by name in lexicographical order.
 * @param start - pointer to the first BusLine in the array.
 * @param end - pointer one past the last BusLine in the array (exclusive).
 * @return 1 if the array is sorted by name, 0 otherwise.
 */
int is_sorted_by_name (const BusLine *start, const BusLine *end);

/**
 * Checks if a specific bus line exists within a given range of a BusLine array.
 * @param start - pointer to the first BusLine in the range.
 * @param end - pointer one past the last BusLine in the range (exclusive).
 * @param busline - pointer to the BusLine structure to search for.
 * @return 1 if the bus line is found in the range, 0 otherwise.
 */
int is_in_array(const BusLine *start, const BusLine *end, const BusLine *busline);


/**
 * Verifies that the sorted array contains exactly the same elements as the original array.
 * @param start_sorted - pointer to the first BusLine in the sorted array.
 * @param end_sorted - pointer one past the last BusLine in the sorted array (exclusive).
 * @param start_original - pointer to the first BusLine in the original array.
 * @param end_original - pointer one past the last BusLine in the original array (exclusive).
 * @return 1 if the arrays contain the same elements, 0 otherwise.
 */
int is_equal (const BusLine *start_sorted,
              const BusLine *end_sorted,
              const BusLine *start_original,
              const BusLine *end_original);
// write only between #define EX2_REPO_TESTBUSLINES_H and #endif //EX2_REPO_TESTBUSLINES_H
#endif //EX2_REPO_TESTBUSLINES_H
