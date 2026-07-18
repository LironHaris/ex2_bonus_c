#include "sort_bus_lines.h"
#include "test_bus_lines.h"
#include <stdlib.h>
#include <stdio.h>
#include <string.h>

#define ARGS_NUMBER 2
#define MAX_LINE_LENGTH 62
#define PARAMETERS_NUMBER 4
#define MIN_DURATION 10
#define MAX_DURATION 100
#define MIN_DISTANCE 0
#define MAX_DISTANCE 1000
#define MIN_FREQ 1
#define MAX_FREQ 50
#define MAX_NUM_OF_LINES 10000
#define ERROR (-1)
#define QUICK_SORT 0
#define BUBBLE_SORT 1
#define TEST 2
#define INVALID 0
#define VALID 1


int parse_args (int argc, char *argv[], SortType *sort_type);
BusLine *initialize_bus_lines (int *num_of_lines);
void run_all_tests (BusLine *bus_lines, int num_of_lines);
void print_bus_lines (BusLine *start, BusLine *end);
int validate_bus_line (BusLine *curr, int scan_res);
static void drain_stdin_line_remainder (const char *buffer);

/**
 * Main orchestrator of the program.
 */
int main (int argc, char *argv[])
{
    SortType sort_type = DISTANCE;
    int mode = parse_args (argc, argv, &sort_type);
    if (mode == ERROR)
    {
        return EXIT_FAILURE;
    }

    int num_of_lines = 0;
    BusLine *bus_lines = initialize_bus_lines (&num_of_lines);
    if (bus_lines == NULL)
    {
        return EXIT_FAILURE;
    }

    BusLine *start = bus_lines;
    BusLine *end = bus_lines + num_of_lines;

    switch (mode)
    {
        case QUICK_SORT:
            bus_quick_sort (start, end, sort_type);
            print_bus_lines (start, end);
            break;

        case BUBBLE_SORT:
            bus_bubble_sort (start, end);
            print_bus_lines (start, end);
            break;

        case TEST:
            run_all_tests (bus_lines, num_of_lines);
            break;
    }

    free (bus_lines);
    return EXIT_SUCCESS;
}

/**
 * Validates command line arguments and determines the mode.
 * Returns: 0 for QuickSort, 1 for BubbleSort, 2 for Test, -1 for Error.
 */
int parse_args (int argc, char *argv[], SortType *sort_type)
{
    if (argc != ARGS_NUMBER)
    {
        fprintf (stdout, "Usage: sort_bus_lines <sort_type>\n");
        return ERROR;
    }

    if (strcmp (argv[1], "by_distance") == 0)
    {
        *sort_type = DISTANCE;
        return QUICK_SORT;
    }
    if (strcmp (argv[1], "by_duration") == 0)
    {
        *sort_type = DURATION;
        return QUICK_SORT;
    }
    if (strcmp (argv[1], "by_frequency") == 0)
    {
        *sort_type = FREQUENCY;
        return QUICK_SORT;
    }
    if (strcmp (argv[1], "by_name") == 0)
    {
        return BUBBLE_SORT;
    }
    if (strcmp (argv[1], "test") == 0)
    {
        return TEST;
    }

    fprintf (stdout, "Usage: sort_bus_lines <sort_type>\n");
    return ERROR;
}

/**
 * If fgets filled the buffer without reaching a newline, the rest of the
 * physical input line is still sitting in stdin. Discard it so the next
 * fgets call starts at the next real line instead of the leftover tail of
 * this one.
 */
static void drain_stdin_line_remainder (const char *buffer)
{
    if (strchr (buffer, '\n') != NULL)
    {
        return;
    }
    int c;
    while ((c = getchar ()) != '\n' && c != EOF)
    {
    }
}

/**
 * Prompts user for bus data, validates it, and returns a dynamically
 * allocated array of BusLine structs. Updates num_of_lines with the total count.
 */
BusLine *initialize_bus_lines (int *num_of_lines)
{
    char line_buffer[MAX_LINE_LENGTH] = {0};
    printf ("Enter number of lines. Then enter\n");
    if (fgets (line_buffer, sizeof (line_buffer), stdin) == NULL) return NULL;
    drain_stdin_line_remainder (line_buffer);
    while (sscanf (line_buffer, "%d", num_of_lines) != 1 || *num_of_lines <= 0
           || *num_of_lines > MAX_NUM_OF_LINES)
    {
        printf ("Error: Invalid number of lines\n");
        printf ("Enter number of lines. Then enter\n");
        if (fgets (line_buffer, sizeof (line_buffer), stdin) == NULL) return NULL;
        drain_stdin_line_remainder (line_buffer);
    }
    BusLine *bus_lines = malloc (sizeof (BusLine) * *num_of_lines);    if (bus_lines == NULL) return NULL;
    for (int i = 0; i < *num_of_lines; i++)
    {
        fprintf (stdout, "Enter line info. Then enter\n");
        char input_buffer[MAX_LINE_LENGTH] = {0};
        if (fgets (input_buffer, sizeof (input_buffer), stdin) == NULL)
        {
            free(bus_lines);
            return NULL;
        }
        drain_stdin_line_remainder (input_buffer);
        BusLine *curr = bus_lines + i;
        int res = sscanf (input_buffer, "%20[^,],%d,%d,%d", curr->name,&curr->distance, &curr->duration, &curr->frequency);
        if (validate_bus_line (curr, res) == INVALID)
        {
            i--;
        }
    }
    return bus_lines;
}

/**
 * Runs the 8 required tests for the 'test' mode.
 */
void run_all_tests (BusLine *bus_lines, int num_of_lines)
{
    BusLine *original_copy = malloc (num_of_lines * sizeof (BusLine));
    if (original_copy == NULL) return;
    memcpy (original_copy, bus_lines, num_of_lines * sizeof (BusLine));

    BusLine *start = bus_lines;
    BusLine *end = bus_lines + num_of_lines;
    const BusLine *orig_start = original_copy;
    const BusLine *orig_end = original_copy + num_of_lines;
    const char *field_names[] = {"distance", "duration", "frequency"};
    int test_num = 1;

    for (int i = 0; i < 3; i++)
    {
        memcpy (bus_lines, original_copy, num_of_lines * sizeof (BusLine));
        bus_quick_sort (start, end, (SortType)i);

        int sorted = 0;
        if (i == 0) sorted = is_sorted_by_distance (start, end);
        else if (i == 1) sorted = is_sorted_by_duration (start, end);
        else if (i == 2) sorted = is_sorted_by_frequency (start, end);

        if (sorted) printf ("TEST %d PASSED: array is sorted by %s\n", test_num++, field_names[i]);
        else printf ("TEST %d FAILED: array is not sorted by %s\n", test_num++, field_names[i]);

        if (is_equal (start, end, orig_start, orig_end))
            printf ("TEST %d PASSED: integrity check passed\n", test_num++);
        else
            printf ("TEST %d FAILED: integrity check failed\n", test_num++);
    }

    memcpy (bus_lines, original_copy, num_of_lines * sizeof (BusLine));
    bus_bubble_sort (start, end);

    if (is_sorted_by_name (start, end)) printf ("TEST 7 PASSED: array is sorted by name\n");
    else printf ("TEST 7 FAILED: array is not sorted by name\n");

    if (is_equal (start, end, orig_start, orig_end)) printf ("TEST 8 PASSED: integrity check passed\n");
    else printf ("TEST 8 FAILED: integrity check failed\n");

    free (original_copy);
}

/**
 * Utility to print the bus lines in CSV format.
 */
void print_bus_lines (BusLine *start, BusLine *end)
{
    for (const BusLine *curr = start; curr < end; curr++)
    {
        printf ("%s,%d,%d,%d\n", curr->name, curr->distance, curr->duration, curr->frequency);
    }
}

/**
 * Validates the bus line data and format, printing specific error messages on failure.
 * Returns VALID if all checks pass, otherwise returns INVALID.
 */
int validate_bus_line (BusLine *curr, int scan_res)
{
    if (scan_res != PARAMETERS_NUMBER)
    {
        fprintf (stdout, "Error: Invalid input format. Expected: name,distance,duration,frequency\n");
        return INVALID;
    }
    for (int j = 0; curr->name[j] != '\0'; j++)
    {
        if (!((curr->name[j] >= 'a' && curr->name[j] <= 'z') || (curr->name[j] >= '0' && curr->name[j] <= '9')))
        {
            fprintf (stdout, "Error: bus name should contains only digits and small chars\n");
            return INVALID;
        }
    }
    if (curr->distance < MIN_DISTANCE || curr->distance > MAX_DISTANCE)
    {
        fprintf (stdout, "Error: distance must be an integer between 0 and 1000 (inclusive).\n");
        return INVALID;
    }
    if (curr->duration < MIN_DURATION || curr->duration > MAX_DURATION)
    {
        fprintf (stdout, "Error: duration must be an integer between 10 and 100 (inclusive).\n");
        return INVALID;
    }
    if (curr->frequency < MIN_FREQ || curr->frequency > MAX_FREQ)
    {
        fprintf (stdout, "Error: frequency must be an integer between 1 and 50 (inclusive).\n");
        return INVALID;
    }
    return VALID;
}