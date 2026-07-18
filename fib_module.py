import ctypes

fib_lib = ctypes.CDLL("./libfib.so")

fib_lib.CFib.argtypes = [ctypes.c_int]
fib_lib.CFib.restype = ctypes.c_int


def fib(n):
    return fib_lib.CFib(n)
