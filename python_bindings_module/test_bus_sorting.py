import pytest

from bus_module import BusLine, SortType, bubble_sort, quick_sort


# ---------------------------------------------------------------------------
# Sorting by name (bubble_sort)
# ---------------------------------------------------------------------------

def test_bubble_sort_by_name_orders_alphabetically():
    data = [("zzz", 10, 20, 5), ("aaa", 50, 30, 7), ("mmm", 5, 15, 2)]
    result = bubble_sort(data)
    assert [line[0] for line in result] == ["aaa", "mmm", "zzz"]


def test_bubble_sort_by_name_preserves_full_record():
    data = [("bbb", 1, 10, 1), ("aaa", 2, 20, 2)]
    result = bubble_sort(data)
    assert result == [("aaa", 2, 20, 2), ("bbb", 1, 10, 1)]


def test_bubble_sort_does_not_mutate_input():
    data = [("zzz", 10, 20, 5), ("aaa", 50, 30, 7)]
    original = list(data)
    bubble_sort(data)
    assert data == original


# ---------------------------------------------------------------------------
# Sorting by distance (quick_sort)
# ---------------------------------------------------------------------------

def test_quick_sort_by_distance_orders_ascending():
    data = [("zzz", 10, 20, 5), ("aaa", 50, 30, 7), ("mmm", 5, 15, 2)]
    result = quick_sort(data, SortType.DISTANCE)
    assert [line[1] for line in result] == [5, 10, 50]
    assert [line[0] for line in result] == ["mmm", "zzz", "aaa"]


# ---------------------------------------------------------------------------
# Sorting by duration (quick_sort)
# ---------------------------------------------------------------------------

def test_quick_sort_by_duration_orders_ascending():
    data = [("a", 1, 90, 1), ("b", 2, 10, 2), ("c", 3, 50, 3)]
    result = quick_sort(data, SortType.DURATION)
    assert [line[2] for line in result] == [10, 50, 90]
    assert [line[0] for line in result] == ["b", "c", "a"]


# ---------------------------------------------------------------------------
# Sorting by frequency (quick_sort) -- extra coverage of the third SortType
# ---------------------------------------------------------------------------

def test_quick_sort_by_frequency_orders_ascending():
    data = [("a", 1, 10, 30), ("b", 2, 20, 5), ("c", 3, 30, 15)]
    result = quick_sort(data, SortType.FREQUENCY)
    assert [line[3] for line in result] == [5, 15, 30]
    assert [line[0] for line in result] == ["b", "c", "a"]


# ---------------------------------------------------------------------------
# Edge cases / invalid input
# ---------------------------------------------------------------------------

def test_empty_array_bubble_sort_returns_empty_list():
    assert bubble_sort([]) == []


def test_empty_array_quick_sort_returns_empty_list():
    assert quick_sort([], SortType.DISTANCE) == []


def test_out_of_range_distance_is_rejected():
    # bus_module now routes every element through the C program's own
    # validate_bus_line, so values outside main.c's declared ranges
    # (distance 0-1000, duration 10-100, frequency 1-50) are rejected instead
    # of silently sorting -- closing the "no domain validation" gap from the
    # code review.
    data = [("a", -5, 20, 1), ("b", 10, 10, 3)]
    with pytest.raises(ValueError):
        quick_sort(data, SortType.DISTANCE)


def test_out_of_range_duration_is_rejected():
    data = [("a", 5, 200, 1)]
    with pytest.raises(ValueError):
        quick_sort(data, SortType.DURATION)


def test_boundary_valid_values_sort_correctly():
    # Exercises the inclusive edges of every validated range (distance
    # 0-1000, duration 10-100, frequency 1-50) to confirm they're accepted,
    # not just rejected out-of-range values.
    data = [("hi", 1000, 100, 50), ("lo", 0, 10, 1), ("mid", 500, 55, 25)]
    result = quick_sort(data, SortType.DISTANCE)
    assert [line[1] for line in result] == [0, 500, 1000]


def test_invalid_sort_type_is_rejected():
    data = [("a", 1, 10, 1), ("b", 2, 20, 2)]
    with pytest.raises(ValueError):
        quick_sort(data, 99)


def test_empty_name_sorts_before_nonempty_names():
    data = [("zzz", 1, 10, 1), ("", 2, 20, 2), ("aaa", 3, 30, 3)]
    result = bubble_sort(data)
    assert [line[0] for line in result] == ["", "aaa", "zzz"]


def test_name_exactly_at_capacity_is_rejected():
    # BusLine.name is char[21]; a 21-byte name leaves no room for the C
    # string's null terminator, so the wrapper must reject it rather than
    # silently producing an unterminated C string.
    too_long_name = "x" * 21
    with pytest.raises(ValueError):
        bubble_sort([(too_long_name, 1, 10, 1)])


def test_name_at_max_valid_length_is_accepted():
    max_name = "x" * 20  # 20 chars + implicit '\0' == 21 bytes, fits exactly
    result = bubble_sort([(max_name, 1, 10, 1)])
    assert result == [(max_name, 1, 10, 1)]


# ---------------------------------------------------------------------------
# Single element / already sorted
# ---------------------------------------------------------------------------

def test_single_element_bubble_sort():
    data = [("only", 1, 10, 1)]
    assert bubble_sort(data) == data


def test_single_element_quick_sort():
    data = [("only", 42, 10, 1)]
    assert quick_sort(data, SortType.DISTANCE) == data


def test_already_sorted_array_by_distance_unchanged():
    data = [("a", 1, 10, 1), ("b", 2, 20, 2), ("c", 3, 30, 3)]
    assert quick_sort(data, SortType.DISTANCE) == data


def test_already_sorted_array_by_name_unchanged():
    data = [("aaa", 1, 10, 1), ("bbb", 2, 20, 2), ("ccc", 3, 30, 3)]
    assert bubble_sort(data) == data
