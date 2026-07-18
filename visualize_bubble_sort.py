"""
Educational, standalone visualization of the pointer walk performed by
bus_bubble_sort() in sort_bus_lines.c.

This script does NOT call or modify the real C function. It re-implements
the exact same loop structure in Python purely to print step-by-step memory
diagrams. `end` is one past the last array element (exclusive), matching
the real C function's convention; the inner loop bound `j < n - i - 1`
keeps pointer2 within the array on every pass.
"""

BASE_ADDRESS = 0x1000
STRIDE = 0x40


def address_of(index):
    return BASE_ADDRESS + index * STRIDE


def format_array(names, pointer1_index, pointer2_index):
    lines = []
    header = "  Address:  " + "".join(f"{address_of(i):#06x}      " for i in range(len(names)))
    lines.append(header)

    cells = "  Value:    "
    for i, name in enumerate(names):
        cells += f"{'[' + name + ']':<13}"
    lines.append(cells)

    markers = "             "
    for i in range(len(names)):
        tag = ""
        if i == pointer1_index and i == pointer2_index:
            tag = "^p1&p2"
        elif i == pointer1_index:
            tag = "^pointer1"
        elif i == pointer2_index:
            tag = "^pointer2"
        markers += f"{tag:<13}"
    lines.append(markers)

    return "\n".join(lines)


def print_start_end(n):
    print(f"  start = {address_of(0):#06x} (index 0)")
    print(f"  end   = {address_of(n):#06x} (one past index {n - 1}, NOT a valid element)")
    print()


def visualize(names):
    n = len(names)
    print("=" * 70)
    print(f"Initial array: {names}")
    print_start_end(n)

    for i in range(n):
        print("-" * 70)
        print(f"PASS i = {i}  (i is a plain counter, not a pointer; inner loop runs "
              f"j = 0..{n - i - 2 if n - i - 2 >= 0 else '(none)'}, per the code's "
              f"`j < n - i - 1` bound)")
        pointer1_index = 0
        pointer2_index = 1

        for j in range(n - i - 1):
            print()
            print(f"  Step: i={i}, j={j}")

            print(format_array(names, pointer1_index, pointer2_index))
            name1 = names[pointer1_index]
            name2 = names[pointer2_index]
            will_swap = name1 > name2
            print(f"  Comparing: \"{name1}\" vs \"{name2}\""
                  f"  ->  strcmp {'> 0' if will_swap else '<= 0'}"
                  f"  ->  {'SWAP' if will_swap else 'no swap'}")

            if will_swap:
                names[pointer1_index], names[pointer2_index] = (
                    names[pointer2_index], names[pointer1_index],
                )
                print("  After swap:")
                print(format_array(names, pointer1_index, pointer2_index))

            pointer1_index += 1
            pointer2_index += 1

    print("-" * 70)
    print(f"Final sorted array: {names}")
    print("=" * 70)


if __name__ == "__main__":
    visualize(["Dan", "Alice", "Charlie"])
