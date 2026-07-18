from fib_module import fib


def test_fib_base_case_zero():
    assert fib(0) == 0


def test_fib_base_case_one():
    assert fib(1) == 1


def test_fib_larger_value():
    assert fib(10) == 55
