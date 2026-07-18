import ctypes
import os

_lib_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "libsortbus.so")
_lib = ctypes.CDLL(_lib_path)

NAME_LEN = 21


class BusLine(ctypes.Structure):
    """Python/ctypes mirror of the C `struct BusLine` (sort_bus_lines.h):
    char name[21]; int distance, duration, frequency;
    Field order, types, and therefore memory layout match the C struct exactly."""

    _fields_ = [
        ("name", ctypes.c_char * NAME_LEN),
        ("distance", ctypes.c_int),
        ("duration", ctypes.c_int),
        ("frequency", ctypes.c_int),
    ]


BusLinePtr = ctypes.POINTER(BusLine)


class SortType:
    """Mirrors the C `enum SortType` (sort_bus_lines.h)."""

    DISTANCE = 0
    DURATION = 1
    FREQUENCY = 2


_lib.bus_bubble_sort.argtypes = [BusLinePtr, BusLinePtr]
_lib.bus_bubble_sort.restype = None

_lib.bus_quick_sort.argtypes = [BusLinePtr, BusLinePtr, ctypes.c_int]
_lib.bus_quick_sort.restype = None

_lib.compare_bus_lines.argtypes = [BusLinePtr, BusLinePtr, ctypes.c_int]
_lib.compare_bus_lines.restype = ctypes.c_int

_lib.partition.argtypes = [BusLinePtr, BusLinePtr, ctypes.c_int]
_lib.partition.restype = BusLinePtr

_lib.validate_bus_line.argtypes = [BusLinePtr, ctypes.c_int]
_lib.validate_bus_line.restype = ctypes.c_int

_VALID_SORT_TYPES = (SortType.DISTANCE, SortType.DURATION, SortType.FREQUENCY)

# validate_bus_line()'s success sentinel and expected sscanf field count are
# private #defines inside main.c (VALID=1, PARAMETERS_NUMBER=4), not exposed
# via any header. Every tuple handed to this module already has all 4 fields
# parsed out by Python, so the field count is always 4 here.
_VALID = 1
_EXPECTED_SCAN_FIELDS = 4


def _to_c_array(bus_lines):
    """Convert a Python list of (name, distance, duration, frequency) tuples
    into a C-contiguous ctypes BusLine array."""
    n = len(bus_lines)
    arr = (BusLine * n)()
    for i, (name, distance, duration, frequency) in enumerate(bus_lines):
        encoded_name = name.encode("ascii")
        if len(encoded_name) > NAME_LEN - 1:
            # name[NAME_LEN] must hold a trailing '\0' for C's strcmp to be
            # well-defined; NAME_LEN bytes with no room for the terminator
            # would leave the C string unterminated.
            raise ValueError(
                f"name {name!r} is too long: max {NAME_LEN - 1} characters"
            )
        arr[i].name = encoded_name
        arr[i].distance = distance
        arr[i].duration = duration
        arr[i].frequency = frequency

        # Reuse the C program's own validate_bus_line (name charset, and the
        # distance/duration/frequency range checks) instead of duplicating
        # those rules in Python -- keeps this module's notion of "valid" in
        # lockstep with main.c's, and the sort functions never accept data
        # the interactive C program itself would have rejected.
        if _lib.validate_bus_line(ctypes.pointer(arr[i]), _EXPECTED_SCAN_FIELDS) != _VALID:
            raise ValueError(f"invalid bus line: {bus_lines[i]!r}")
    return arr


def _to_py_list(arr):
    """Convert a ctypes BusLine array back into plain Python tuples."""
    return [(bl.name.decode("ascii"), bl.distance, bl.duration, bl.frequency) for bl in arr]


def _bounds(arr):
    """Pointers to the first element and one past the last element,
    matching this codebase's exclusive [start, end) convention used by
    every C function. `arr` is a fixed-size ctypes array, so the one-past
    address is built via a byte offset rather than indexing (arr[n] would
    raise IndexError)."""
    n = len(arr)
    start = ctypes.cast(arr, BusLinePtr)
    end = ctypes.cast(ctypes.byref(arr, n * ctypes.sizeof(BusLine)), BusLinePtr)
    return start, end


def bubble_sort(bus_lines):
    """Sort a list of bus-line tuples by name using the C bubble sort
    (bus_bubble_sort). Data conversion only -- the sort itself runs in C."""
    if not bus_lines:
        return []
    arr = _to_c_array(bus_lines)
    start, end = _bounds(arr)
    _lib.bus_bubble_sort(start, end)
    return _to_py_list(arr)


def quick_sort(bus_lines, sort_type):
    """Sort a list of bus-line tuples by the given SortType field using the
    C quicksort (bus_quick_sort). Data conversion only -- the sort itself
    runs in C."""
    if sort_type not in _VALID_SORT_TYPES:
        # compare_bus_lines() silently returns 0 for an unrecognized
        # sort_type instead of erroring, so this boundary check is what
        # actually stops a bad value from producing a silently-wrong sort.
        raise ValueError(f"invalid sort_type: {sort_type!r}")
    if not bus_lines:
        return []
    arr = _to_c_array(bus_lines)
    start, end = _bounds(arr)
    _lib.bus_quick_sort(start, end, sort_type)
    return _to_py_list(arr)
