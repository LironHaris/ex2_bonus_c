import ctypes
import os
import sys

_lib_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "libsortbus.so")
_lib = ctypes.CDLL(_lib_path)
_libc = ctypes.CDLL("libc.so.6")

NAME_LEN = 21


class BusLine(ctypes.Structure):
    _fields_ = [
        ("name", ctypes.c_char * NAME_LEN),
        ("distance", ctypes.c_int),
        ("duration", ctypes.c_int),
        ("frequency", ctypes.c_int),
    ]


BusLinePtr = ctypes.POINTER(BusLine)


class SortType:
    DISTANCE = 0
    DURATION = 1
    FREQUENCY = 2


# Mode codes returned by parse_args(). These are #defined inside main.c itself
# (not exposed through any header), so the wrapper mirrors the literal values
# purely to interpret the C function's return code -- no branching logic is
# reimplemented, only the same top-level dispatch main() already performs.
ERROR = -1
QUICK_SORT = 0
BUBBLE_SORT = 1
TEST = 2

_lib.parse_args.argtypes = [
    ctypes.c_int,
    ctypes.POINTER(ctypes.c_char_p),
    ctypes.POINTER(ctypes.c_int),
]
_lib.parse_args.restype = ctypes.c_int

_lib.initialize_bus_lines.argtypes = [ctypes.POINTER(ctypes.c_int)]
_lib.initialize_bus_lines.restype = BusLinePtr

_lib.run_all_tests.argtypes = [BusLinePtr, ctypes.c_int]
_lib.run_all_tests.restype = None

_lib.print_bus_lines.argtypes = [BusLinePtr, BusLinePtr]
_lib.print_bus_lines.restype = None

_lib.validate_bus_line.argtypes = [BusLinePtr, ctypes.c_int]
_lib.validate_bus_line.restype = ctypes.c_int

_lib.bus_quick_sort.argtypes = [BusLinePtr, BusLinePtr, ctypes.c_int]
_lib.bus_quick_sort.restype = None

_lib.bus_bubble_sort.argtypes = [BusLinePtr, BusLinePtr]
_lib.bus_bubble_sort.restype = None

_libc.free.argtypes = [ctypes.c_void_p]
_libc.free.restype = None


def _build_argv(args):
    """Marshal a Python list of str into a C argc/argv pair.
    Returns (argc, argv_pointer, keepalive) -- keepalive must stay referenced
    for as long as argv_pointer is used, or the buffer may be garbage collected."""
    argc = len(args)
    argv_array = (ctypes.c_char_p * argc)(*[a.encode("utf-8") for a in args])
    argv_ptr = ctypes.cast(argv_array, ctypes.POINTER(ctypes.c_char_p))
    return argc, argv_ptr, argv_array


def run(argv_list):
    """
    Drives the compiled C program the same way main() does: parse_args() picks
    the mode, initialize_bus_lines() performs the actual interactive
    stdin/stdout prompting and validation in C, and the mode dispatch calls
    straight into bus_quick_sort/bus_bubble_sort/run_all_tests/print_bus_lines.
    Every computation and every prompt/print is executed by the C code; this
    function only reproduces main()'s call sequence and frees the buffer
    main() would otherwise free itself.

    argv_list: list of str, where argv_list[0] is the program name (mirrors argv).
    Returns the process exit code (0 = EXIT_SUCCESS, 1 = EXIT_FAILURE).
    """
    argc, argv_ptr, _keepalive = _build_argv(argv_list)
    sort_type = ctypes.c_int(SortType.DISTANCE)

    mode = _lib.parse_args(argc, argv_ptr, ctypes.byref(sort_type))
    if mode == ERROR:
        return 1

    num_of_lines = ctypes.c_int(0)
    bus_lines = _lib.initialize_bus_lines(ctypes.byref(num_of_lines))
    if not bus_lines:
        return 1

    start = bus_lines
    end = ctypes.cast(
        ctypes.byref(bus_lines.contents, num_of_lines.value * ctypes.sizeof(BusLine)),
        BusLinePtr,
    )

    if mode == QUICK_SORT:
        _lib.bus_quick_sort(start, end, sort_type.value)
        _lib.print_bus_lines(start, end)
    elif mode == BUBBLE_SORT:
        _lib.bus_bubble_sort(start, end)
        _lib.print_bus_lines(start, end)
    elif mode == TEST:
        _lib.run_all_tests(bus_lines, num_of_lines.value)

    _libc.free(bus_lines)
    return 0


if __name__ == "__main__":
    sys.exit(run(["sort_bus_lines"] + sys.argv[1:]))
