"""Map rendering for the Part C route-economy game's GUI: the pseudo-3D
building/road primitives, and every node icon (HOME, UNIVERSITY, the
generic transfer-hub puck, and the landmark-specific Old City wall / Market
stall icons), assembled by draw_map().
"""

import math

import pygame

from game_constants import (
    AFFORD_COLOR, BUILDING_COLORS, BUILDING_LAYOUT, HOUSE_AWNING_COLOR, HOUSE_DOOR_COLOR, HOUSE_ROOF_COLOR,
    HOUSE_WALL_COLOR, MAP_BG, MAP_CONTENT_RECT, MAP_PATCHES, MAP_RECT, MARKET_COUNTER_COLOR, MARKET_STRIPE_RED,
    MARKET_STRIPE_WHITE, OUTLINE_COLOR, ROAD_EDGE, ROAD_FILL, ROAD_OUTLINE, ROUTE_COLORS, SHADOW_COLOR, TEXT_COLOR,
    UNIVERSITY_BUILDING_COLOR, WALL_STONE_COLOR, WALL_STONE_DARK, WINDOW_FRAME_COLOR, WINDOW_GLASS_COLOR,
)
from game_geometry import blend, darken, lighten, map_point, node_short_label, route_bounds


class MapRendererMixin:
    # -- drawing: pseudo-3D primitives ---------------------------------------
    def _draw_ground_shadow(self, x, y, w, h):
        pts = [self._spt(p) for p in [
            (x - 2, y + h), (x + w + 4, y + h), (x + w + 8, y + h + 5), (x - 6, y + h + 5),
        ]]
        pygame.draw.polygon(self.screen, SHADOW_COLOR, pts)

    def _draw_window(self, x, y, size):
        pts = [self._spt(p) for p in [(x, y), (x + size, y), (x + size, y + size), (x, y + size)]]
        pygame.draw.polygon(self.screen, WINDOW_GLASS_COLOR, pts)
        pygame.draw.polygon(self.screen, WINDOW_FRAME_COLOR, pts, max(1, self._slen(1.5)))
        mullion_w = max(1, self._slen(1))
        pygame.draw.line(self.screen, WINDOW_FRAME_COLOR,
                          self._spt((x + size / 2, y)), self._spt((x + size / 2, y + size)), mullion_w)
        pygame.draw.line(self.screen, WINDOW_FRAME_COLOR,
                          self._spt((x, y + size / 2)), self._spt((x + size, y + size / 2)), mullion_w)
        pygame.draw.polygon(self.screen, OUTLINE_COLOR, pts, max(1, self._slen(1)))

    def _draw_block_3d(self, base_rect, base_color, depth=6, windows=0, roof_unit=False):
        """A simple pseudo-isometric block: front face + lighter roof face +
        darker side face, all outlined in a shared ink color, with a ground
        shadow, optional framed windows, and a roof-mounted cooling unit.
        base_rect/depth are in BASE coordinates."""
        x, y, w, h = base_rect.x, base_rect.y, base_rect.width, base_rect.height
        dx = dy = depth

        self._draw_ground_shadow(x, y, w, h)

        front = [(x, y), (x + w, y), (x + w, y + h), (x, y + h)]
        roof = [(x, y), (x + w, y), (x + w + dx, y - dy), (x + dx, y - dy)]
        side = [(x + w, y), (x + w + dx, y - dy), (x + w + dx, y - dy + h), (x + w, y + h)]

        front_pts = [self._spt(p) for p in front]
        roof_pts = [self._spt(p) for p in roof]
        side_pts = [self._spt(p) for p in side]
        line_w = self._slen(2.5)

        pygame.draw.polygon(self.screen, darken(base_color, 60), side_pts)
        pygame.draw.polygon(self.screen, lighten(base_color, 55), roof_pts)
        pygame.draw.polygon(self.screen, base_color, front_pts)
        pygame.draw.polygon(self.screen, OUTLINE_COLOR, side_pts, line_w)
        pygame.draw.polygon(self.screen, OUTLINE_COLOR, roof_pts, line_w)
        pygame.draw.polygon(self.screen, OUTLINE_COLOR, front_pts, line_w)

        if windows:
            wsize = min(w, h) * 0.22
            margin = wsize * 0.9
            usable = w - 2 * margin
            step = usable / windows if windows > 1 else 0
            wy = y + h * 0.30
            for i in range(windows):
                self._draw_window(x + margin + i * step, wy, wsize)

        if roof_unit:
            ux, uy = x + w * 0.55, y - dy * 0.65
            usize = w * 0.22
            unit_pts = [self._spt(p) for p in [
                (ux, uy), (ux + usize, uy), (ux + usize, uy + usize * 0.55), (ux, uy + usize * 0.55),
            ]]
            pygame.draw.polygon(self.screen, darken(base_color, 70), unit_pts)
            pygame.draw.polygon(self.screen, OUTLINE_COLOR, unit_pts, max(1, self._slen(1.5)))
            grille = self._spt((ux + usize * 0.5, uy + usize * 0.28))
            pygame.draw.circle(self.screen, OUTLINE_COLOR, grille, max(1, self._slen(1.6)))

    # -- drawing: map -----------------------------------------------------------
    def _draw_map_texture(self):
        map_screen_rect = self._srect(MAP_RECT)
        overlay = pygame.Surface((max(1, round(map_screen_rect.width)),
                                   max(1, round(map_screen_rect.height))), pygame.SRCALPHA)
        for xf, yf, radius, color in MAP_PATCHES:
            cx = xf * MAP_RECT.width * self.scale
            cy = yf * MAP_RECT.height * self.scale
            pygame.draw.circle(overlay, color, (cx, cy), radius * self.scale)
        self.screen.blit(overlay, (map_screen_rect.x, map_screen_rect.y))

    def _draw_city_blocks(self):
        for i, (xf, yf, w, h, roof_unit) in enumerate(BUILDING_LAYOUT):
            cx = MAP_RECT.x + xf * MAP_RECT.width
            cy = MAP_RECT.y + yf * MAP_RECT.height
            base_rect = pygame.Rect(cx - w / 2, cy - h / 2, w, h)
            color = BUILDING_COLORS[i % len(BUILDING_COLORS)]
            self._draw_block_3d(base_rect, color, depth=5, windows=1, roof_unit=roof_unit)

    def _draw_home_icon(self, pos):
        x, y = pos
        base_w, base_h, depth = 26, 18, 5
        base_rect = pygame.Rect(x - base_w / 2, y - base_h / 2, base_w, base_h)
        self._draw_block_3d(base_rect, HOUSE_WALL_COLOR, depth=depth, windows=1)

        # door with a small green awning above it
        door_w, door_h = base_w * 0.22, base_h * 0.55
        door_x, door_y = x - door_w / 2, y + base_h / 2 - door_h
        door_pts = [self._spt(p) for p in [
            (door_x, door_y), (door_x + door_w, door_y),
            (door_x + door_w, door_y + door_h), (door_x, door_y + door_h),
        ]]
        pygame.draw.polygon(self.screen, HOUSE_DOOR_COLOR, door_pts)
        pygame.draw.polygon(self.screen, OUTLINE_COLOR, door_pts, max(1, self._slen(1.2)))

        awning_pts = [self._spt(p) for p in [
            (door_x - 2, door_y - 3), (door_x + door_w + 2, door_y - 3),
            (door_x + door_w, door_y), (door_x, door_y),
        ]]
        pygame.draw.polygon(self.screen, HOUSE_AWNING_COLOR, awning_pts)
        pygame.draw.polygon(self.screen, OUTLINE_COLOR, awning_pts, max(1, self._slen(1)))

        roof_points = [
            (x - base_w / 2 - depth - 4, y - base_h / 2),
            (x + base_w / 2 + depth + 4, y - base_h / 2),
            (x + base_w / 2, y - base_h / 2 - 18),
            (x - base_w / 2, y - base_h / 2 - 18),
        ]
        roof_pts = [self._spt(p) for p in roof_points]
        pygame.draw.polygon(self.screen, HOUSE_ROOF_COLOR, roof_pts)
        pygame.draw.polygon(self.screen, OUTLINE_COLOR, roof_pts, self._slen(2.5))

        label = self._font(14, bold=True).render("HOME", True, TEXT_COLOR)
        lx, ly = self._spt((x, y + base_h / 2 + depth + 14))
        self.screen.blit(label, label.get_rect(center=(lx, ly)))

    def _draw_university_icon(self, pos):
        x, y = pos
        widths = [22, 34, 22]
        heights = [34, 50, 30]
        total_w = sum(widths) + 8
        cx = x - total_w / 2
        for i, (w, h) in enumerate(zip(widths, heights)):
            base_rect = pygame.Rect(cx, y - h, w, h)
            self._draw_block_3d(base_rect, UNIVERSITY_BUILDING_COLOR, depth=6, windows=3 if i == 1 else 2)
            cx += w + 4

        label = self._font(14, bold=True).render("UNIVERSITY", True, TEXT_COLOR)
        lx, ly = self._spt((x, y + 14))
        self.screen.blit(label, label.get_rect(center=(lx, ly)))

    def _draw_hub_icon(self, pos, node_name):
        """A transfer hub (levels 3-5): two overlapping rings on a stone
        puck -- the classic "interchange" glyph -- with a bright halo while
        it's the node the player currently stands at, so it's always clear
        where the currently-listed lines depart from."""
        cx, cy = self._spt(pos)
        r_shadow = self._slen(22)
        r_outline = self._slen(21)
        r_face = self._slen(17)
        shadow_off = self._slen(3.5)

        self._draw_current_node_halo(pos, node_name, 27)

        pygame.draw.circle(self.screen, SHADOW_COLOR, (cx + shadow_off, cy + shadow_off * 1.4), r_shadow)
        pygame.draw.circle(self.screen, OUTLINE_COLOR, (cx, cy), r_outline)
        pygame.draw.circle(self.screen, (215, 205, 188), (cx, cy), r_face)
        pygame.draw.circle(self.screen, OUTLINE_COLOR, (cx, cy), r_face, max(1, self._slen(1.5)))

        ring_r = r_face * 0.42
        offset = ring_r * 0.55
        line_w = max(1, self._slen(2))
        pygame.draw.circle(self.screen, (60, 95, 150), (cx - offset, cy), ring_r, line_w)
        pygame.draw.circle(self.screen, (170, 60, 50), (cx + offset, cy), ring_r, line_w)

        label = self._font(13, bold=True).render(node_short_label(node_name), True, TEXT_COLOR)
        lx, ly = self._spt((pos[0], pos[1] + 32))
        self.screen.blit(label, label.get_rect(center=(lx, ly)))

    def _draw_current_node_halo(self, pos, node_name, radius):
        if node_name == self.state.current_node:
            cx, cy = self._spt(pos)
            pygame.draw.circle(self.screen, lighten(AFFORD_COLOR, 110), (cx, cy), self._slen(radius))

    def _draw_old_city_icon(self, pos, node_name):
        """Old City (Ir Atika): a stylized stone-wall/fortress segment with
        battlements, evoking the Old City walls -- distinct from the generic
        hub puck used for Central Station."""
        x, y = pos
        self._draw_current_node_halo(pos, node_name, 30)
        self._draw_ground_shadow(x - 24, y - 4, 48, 14)

        wall_w, wall_h = 46, 20
        body = [(x - wall_w / 2, y - wall_h / 2), (x + wall_w / 2, y - wall_h / 2),
                (x + wall_w / 2, y + wall_h / 2), (x - wall_w / 2, y + wall_h / 2)]
        body_pts = [self._spt(p) for p in body]
        pygame.draw.polygon(self.screen, WALL_STONE_COLOR, body_pts)
        pygame.draw.polygon(self.screen, OUTLINE_COLOR, body_pts, self._slen(2.5))

        # crenellations (battlements) along the top edge
        teeth = 5
        tooth_w = wall_w / (teeth * 2 - 1)
        top_y = y - wall_h / 2
        for i in range(teeth):
            tx = x - wall_w / 2 + i * 2 * tooth_w
            tooth = [(tx, top_y - 8), (tx + tooth_w, top_y - 8), (tx + tooth_w, top_y), (tx, top_y)]
            tooth_pts = [self._spt(p) for p in tooth]
            pygame.draw.polygon(self.screen, WALL_STONE_COLOR, tooth_pts)
            pygame.draw.polygon(self.screen, OUTLINE_COLOR, tooth_pts, max(1, self._slen(1.5)))

        # stone-block seams for texture
        for i in range(1, 3):
            seam_x = x - wall_w / 2 + i * wall_w / 3
            pygame.draw.line(self.screen, WALL_STONE_DARK, self._spt((seam_x, y - wall_h / 2)),
                              self._spt((seam_x, y + wall_h / 2)), max(1, self._slen(1.2)))

        label = self._font(13, bold=True).render(node_short_label(node_name), True, TEXT_COLOR)
        lx, ly = self._spt((x, y + wall_h / 2 + 22))
        self.screen.blit(label, label.get_rect(center=(lx, ly)))

    def _draw_market_icon(self, pos, node_name):
        """The Market (Machane Yehuda): a stall counter with a striped
        red/white canopy, distinct from the generic hub puck used for
        Central Station."""
        x, y = pos
        self._draw_current_node_halo(pos, node_name, 30)
        self._draw_ground_shadow(x - 20, y, 40, 14)

        counter_w, counter_h = 34, 14
        counter = [(x - counter_w / 2, y), (x + counter_w / 2, y),
                   (x + counter_w / 2, y + counter_h), (x - counter_w / 2, y + counter_h)]
        counter_pts = [self._spt(p) for p in counter]
        pygame.draw.polygon(self.screen, MARKET_COUNTER_COLOR, counter_pts)
        pygame.draw.polygon(self.screen, OUTLINE_COLOR, counter_pts, self._slen(2))

        pole_w = max(1, self._slen(2))
        pygame.draw.line(self.screen, OUTLINE_COLOR, self._spt((x - counter_w / 2 + 2, y)),
                          self._spt((x - counter_w / 2 + 2, y - 18)), pole_w)
        pygame.draw.line(self.screen, OUTLINE_COLOR, self._spt((x + counter_w / 2 - 2, y)),
                          self._spt((x + counter_w / 2 - 2, y - 18)), pole_w)

        # striped scalloped awning: alternating red/white trapezoid segments
        canopy_top_y, canopy_bottom_y = y - 18, y - 8
        segments = 5
        canopy_w = counter_w + 6
        seg_w = canopy_w / segments
        start_x = x - canopy_w / 2
        for i in range(segments):
            sx = start_x + i * seg_w
            color = MARKET_STRIPE_RED if i % 2 == 0 else MARKET_STRIPE_WHITE
            seg = [(sx, canopy_top_y), (sx + seg_w, canopy_top_y),
                   (sx + seg_w * 0.7, canopy_bottom_y), (sx + seg_w * 0.3, canopy_bottom_y)]
            seg_pts = [self._spt(p) for p in seg]
            pygame.draw.polygon(self.screen, color, seg_pts)
            pygame.draw.polygon(self.screen, OUTLINE_COLOR, seg_pts, max(1, self._slen(1)))

        bar_pts = [self._spt((start_x, canopy_top_y)), self._spt((start_x + canopy_w, canopy_top_y))]
        pygame.draw.line(self.screen, OUTLINE_COLOR, bar_pts[0], bar_pts[1], max(1, self._slen(2)))

        label = self._font(13, bold=True).render(node_short_label(node_name), True, TEXT_COLOR)
        lx, ly = self._spt((x, y + counter_h + 14))
        self.screen.blit(label, label.get_rect(center=(lx, ly)))

    def _draw_station_icon(self, cx, cy, r, task_type):
        """A tiny task-specific glyph drawn inside the station's colored
        core, in a bright contrasting color: a lightning bolt (agility),
        a 2x2 grid (memory), or a gear (thinking)."""
        icon_color = (250, 250, 248)
        if task_type == "agility":
            s = r * 0.9
            pts = [
                (cx - 0.10 * s, cy - s), (cx + 0.45 * s, cy - 0.05 * s), (cx + 0.05 * s, cy - 0.05 * s),
                (cx + 0.20 * s, cy + s), (cx - 0.45 * s, cy + 0.15 * s), (cx - 0.05 * s, cy + 0.15 * s),
            ]
            pygame.draw.polygon(self.screen, icon_color, pts)
            pygame.draw.polygon(self.screen, OUTLINE_COLOR, pts, max(1, round(self._slen(1) * 0.6)))
        elif task_type == "memory":
            size = r * 1.1
            rect = pygame.Rect(cx - size / 2, cy - size / 2, size, size)
            line_w = max(1, self._slen(1.6))
            pygame.draw.rect(self.screen, icon_color, rect, line_w, border_radius=max(1, round(line_w * 0.4)))
            pygame.draw.line(self.screen, icon_color, (cx, rect.top + line_w), (cx, rect.bottom - line_w), line_w)
            pygame.draw.line(self.screen, icon_color, (rect.left + line_w, cy), (rect.right - line_w, cy), line_w)
        elif task_type == "thinking":
            gear_r = r * 0.72
            line_w = max(1, self._slen(1.4))
            for i in range(8):
                angle = math.radians(i * 45)
                x1 = cx + gear_r * 0.75 * math.cos(angle)
                y1 = cy + gear_r * 0.75 * math.sin(angle)
                x2 = cx + gear_r * 1.3 * math.cos(angle)
                y2 = cy + gear_r * 1.3 * math.sin(angle)
                pygame.draw.line(self.screen, icon_color, (x1, y1), (x2, y2), line_w)
            pygame.draw.circle(self.screen, icon_color, (cx, cy), gear_r, line_w)
            pygame.draw.circle(self.screen, icon_color, (cx, cy), gear_r * 0.35, line_w)

    def _draw_station(self, pos, color, task_type):
        """A layered "puck" button, matching the level-select node style:
        ground shadow -> thick dark outline -> metallic stone rim (with a
        light/dark crescent for a curved-edge look) -> recessed dish ->
        light inner face -> colored core (this route's identity) -> a
        task-specific glyph identifying the mini-game waiting at this stop."""
        cx, cy = self._spt(pos)
        r_shadow = self._slen(19)
        r_outline = self._slen(18)
        r_rim = self._slen(16)
        r_dish = self._slen(12)
        r_face = self._slen(9)
        r_core = self._slen(7)
        shadow_off = self._slen(3.5)

        pygame.draw.circle(self.screen, SHADOW_COLOR, (cx + shadow_off, cy + shadow_off * 1.4), r_shadow)
        pygame.draw.circle(self.screen, OUTLINE_COLOR, (cx, cy), r_outline)
        pygame.draw.circle(self.screen, (198, 196, 190), (cx, cy), r_rim)
        pygame.draw.circle(self.screen, (150, 148, 142), (cx + r_rim * 0.28, cy + r_rim * 0.28), r_rim * 0.85)
        pygame.draw.circle(self.screen, (228, 226, 220), (cx - r_rim * 0.22, cy - r_rim * 0.22), r_rim * 0.78)
        pygame.draw.circle(self.screen, (118, 116, 112), (cx, cy), r_dish)
        pygame.draw.circle(self.screen, (240, 238, 232), (cx, cy), r_face)
        pygame.draw.circle(self.screen, color, (cx, cy), r_core)
        pygame.draw.circle(self.screen, OUTLINE_COLOR, (cx, cy), r_core, max(1, self._slen(1)))
        self._draw_station_icon(cx, cy, r_core, task_type)

    def _draw_thick_polyline(self, points, color, width):
        """pygame.draw.lines leaves gaps at sharp joints for thick strokes;
        stamp a circle at every vertex to keep corners looking solid."""
        if len(points) < 2:
            return
        pygame.draw.lines(self.screen, color, False, points, width)
        for p in points:
            pygame.draw.circle(self.screen, color, p, width / 2)

    def draw_map(self):
        pygame.draw.rect(self.screen, MAP_BG, self._srect(MAP_RECT), border_radius=self._slen(6))
        self._draw_map_texture()

        row_range, col_range = route_bounds(self.level)
        route_points = [
            [self._spt(map_point(r, c, row_range, col_range, MAP_CONTENT_RECT)) for r, c in route.path]
            for route in self.level.bus_routes
        ]

        # Roads: thick dark outline, a light stone-cream edge trim, a dark
        # asphalt body, then the colored transit line on top of each --
        # a bordered street bed with a crisp highlighted edge, not one flat line.
        outline_w = self._slen(15)
        edge_w = self._slen(12)
        fill_w = self._slen(8)
        route_w = self._slen(3)
        route_w_hover = self._slen(6)
        for points in route_points:
            self._draw_thick_polyline(points, ROAD_OUTLINE, outline_w)
        for points in route_points:
            self._draw_thick_polyline(points, ROAD_EDGE, edge_w)
        for points in route_points:
            self._draw_thick_polyline(points, ROAD_FILL, fill_w)

        # The hovered/selected line is drawn thicker and brighter; the other
        # 4 fade toward the road color so the highlighted one stands out.
        for i, (points, route) in enumerate(zip(route_points, self.level.bus_routes)):
            base_color = ROUTE_COLORS[i % len(ROUTE_COLORS)]
            if self.hovered_route is None:
                color, width = base_color, route_w
            elif route is self.hovered_route:
                color, width = lighten(base_color, 50), route_w_hover
            else:
                color, width = blend(base_color, ROAD_FILL, 0.55), route_w
            self._draw_thick_polyline(points, color, width)

        self._draw_city_blocks()

        # Station signposts, one per route, colored + iconed to match that
        # route -- skipped for lines with no station (Level 1's direct
        # HOME -> UNIVERSITY routes).
        for i, route in enumerate(self.level.bus_routes):
            if route.station is None:
                continue
            station_pos = map_point(*route.station, row_range, col_range, MAP_CONTENT_RECT)
            self._draw_station(station_pos, ROUTE_COLORS[i % len(ROUTE_COLORS)], route.task_type)

        # Every node in the level: HOME and UNIVERSITY get their dedicated
        # icons; transfer hubs get a landmark-specific icon where one is
        # defined (Old City, the Market), and the generic interchange puck
        # otherwise (Central Station and any other hub).
        for node_name, coord in self.level.nodes.items():
            pos = map_point(*coord, row_range, col_range, MAP_CONTENT_RECT)
            if node_name == "HOME":
                self._draw_home_icon(pos)
            elif node_name == "UNIVERSITY":
                self._draw_university_icon(pos)
            elif node_name == "OLD_CITY":
                self._draw_old_city_icon(pos, node_name)
            elif node_name == "MARKET_JCT":
                self._draw_market_icon(pos, node_name)
            else:
                self._draw_hub_icon(pos, node_name)
