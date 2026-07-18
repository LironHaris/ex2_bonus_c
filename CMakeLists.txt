cmake_minimum_required(VERSION 3.10)
project(fib_bonus C)

set(CMAKE_C_STANDARD 99)

add_executable(fib_bonus fib.c fib.h)

add_executable(sort_bus_lines main.c sort_bus_lines.c sort_bus_lines.h test_bus_lines.c test_bus_lines.h)
