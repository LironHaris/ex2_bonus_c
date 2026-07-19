"""Stateless geometry/formatting helpers shared across the GUI's mixin
modules (game_logic.py, game_animation.py, game_map_render.py,
game_panels.py). No pygame.display/state dependencies -- pure functions.
"""

import math


def lighten(color, amount):
    return tuple(min(255, c + amount) for c in color)


def darken(color, amount):
    return tuple(max(0, c - amount) for c in color)


def blend(color_a, color_b, t):
    return tuple(round(a + (b - a) * t) for a, b in zip(color_a, color_b))


def map_point(row, col, row_range, col_range, rect):
    r0, r1 = row_range
    c0, c1 = col_range
    rr = 0.5 if r1 == r0 else (row - r0) / (r1 - r0)
    cc = 0.5 if c1 == c0 else (col - c0) / (c1 - c0)
    return rect.x + cc * rect.width, rect.y + rr * rect.height


def route_bounds(level):
    rows = [p[0] for r in level.bus_routes for p in r.path] + [c[0] for c in level.nodes.values()]
    cols = [p[1] for r in level.bus_routes for p in r.path] + [c[1] for c in level.nodes.values()]
    return (min(rows), max(rows)), (min(cols), max(cols))


def node_label(node_name):
    """Human-readable label for a node: HOME/UNIVERSITY as-is, transfer hubs
    ("CENTRAL_STATION") title-cased with spaces ("Central Station")."""
    if node_name in ("HOME", "UNIVERSITY"):
        return node_name
    return node_name.replace("_", " ").title()


def node_short_label(node_name):
    """Compact tag for narrow table columns (Trip Planner FROM/TO) -- just
    the first word of the full label, e.g. "Central Station" -> "CENTRAL"."""
    return node_label(node_name).split(" ")[0].upper()


def point_segment_distance(p, a, b):
    """Perpendicular distance from point p to the segment a-b (all real
    screen-space (x, y) pairs), used for map hover-detection."""
    px, py = p
    ax, ay = a
    bx, by = b
    dx, dy = bx - ax, by - ay
    if dx == 0 and dy == 0:
        return math.hypot(px - ax, py - ay)
    t = max(0, min(1, ((px - ax) * dx + (py - ay) * dy) / (dx * dx + dy * dy)))
    return math.hypot(px - (ax + t * dx), py - (ay + t * dy))


def interpolate_path(points, t):
    """Arc-length-parameterized position at fraction t (0..1) along a
    polyline. points/return value are in the same coordinate space (BASE or
    screen, caller's choice) -- used to animate the bus at a constant speed
    regardless of how uneven the path's segment lengths are."""
    if len(points) == 1:
        return points[0]
    seg_lengths = [math.hypot(b[0] - a[0], b[1] - a[1]) for a, b in zip(points, points[1:])]
    total = sum(seg_lengths)
    if total == 0:
        return points[0]
    target = max(0.0, min(1.0, t)) * total
    acc = 0.0
    for (a, b), seg_len in zip(zip(points, points[1:]), seg_lengths):
        if seg_len == 0:
            continue
        if acc + seg_len >= target:
            local_t = (target - acc) / seg_len
            return (a[0] + (b[0] - a[0]) * local_t, a[1] + (b[1] - a[1]) * local_t)
        acc += seg_len
    return points[-1]
