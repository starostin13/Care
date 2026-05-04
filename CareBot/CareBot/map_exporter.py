"""Utilities for rendering a realistic hex map export as PNG bytes."""

from io import BytesIO
import math
from typing import Dict, Iterable, List, Optional, Tuple

import matplotlib.patches as patches
import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection
import numpy as np


TERRAIN_STYLES: Dict[str, Dict[str, str]] = {
    "Леса": {"fill": "#2E7D32"},
    "Тундра/снег": {"fill": "#E3F2FD"},
    "Пустыня": {"fill": "#D4A373"},
    "Отравленные земли": {"fill": "#6B8E23"},
    "Завод": {"fill": "#6C757D"},
    "Город": {"fill": "#5C6BC0"},
    "Разрушенный город": {"fill": "#8D6E63"},
    "Подземные системы": {"fill": "#37474F"},
    "Останки корабля": {"fill": "#B0BEC5"},
    "Свалка": {"fill": "#8D6E63"},
    "Храмовый квартал": {"fill": "#FBC02D"},
    "Изменённое варпом пространство": {"fill": "#6A1B9A"},
}

# Compatibility alias for old typo in legacy data.
TERRAIN_ALIASES = {
    "Храовый квартал": "Храмовый квартал",
    # English terrain names used in production DB.
    "Forest": "Леса",
    "Tundra/Snow": "Тундра/снег",
    "Desert": "Пустыня",
    "Poisoned Lands": "Отравленные земли",
    "Factory": "Завод",
    "City": "Город",
    "Ruined City": "Разрушенный город",
    "Underground Systems": "Подземные системы",
    "Ship Wreckage": "Останки корабля",
    "Junkyard": "Свалка",
    "Temple Quarter": "Храмовый квартал",
    "Warp-altered Space": "Изменённое варпом пространство",
}

DEFAULT_TERRAIN_STYLE = {"fill": "#CFD8DC"}
NEUTRAL_BORDER_COLOR = "#546E7A"
ALLIANCE_FALLBACK_COLORS = [
    "#C62828",
    "#1565C0",
    "#2E7D32",
    "#6A1B9A",
    "#EF6C00",
    "#37474F",
    "#AD1457",
    "#00838F",
]

# Axial neighbor directions for pointy-top hexes
_HEX_DIRECTIONS = [(1, 0), (1, -1), (0, -1), (-1, 0), (-1, 1), (0, 1)]

# Maps each axial direction to the two vertex indices (0-5) forming the shared edge.
# Vertex k is at angle pi/6 + k*pi/3 (pointy-top, vertices start lower-right, CCW).
#   E(1,0)->(5,0)   NE(1,-1)->(0,1)   NW(0,-1)->(1,2)
#   W(-1,0)->(2,3)  SW(-1,1)->(3,4)   SE(0,1)->(4,5)
_DIRECTION_EDGE_VERTICES: Dict[Tuple[int, int], Tuple[int, int]] = {
    (1,  0): (5, 0),
    (1, -1): (0, 1),
    (0, -1): (1, 2),
    (-1, 0): (2, 3),
    (-1, 1): (3, 4),
    (0,  1): (4, 5),
}


def _hex_ring(center_q: int, center_r: int, radius: int) -> List[Tuple[int, int]]:
    directions = [(1, 0), (1, -1), (0, -1), (-1, 0), (-1, 1), (0, 1)]
    if radius == 0:
        return [(center_q, center_r)]

    ring_coords: List[Tuple[int, int]] = []
    q, r = center_q + directions[4][0] * radius, center_r + directions[4][1] * radius
    for i in range(6):
        for _ in range(radius):
            ring_coords.append((q, r))
            dq, dr = directions[i]
            q += dq
            r += dr
    return ring_coords


def _reconstruct_coordinates(hex_count: int) -> Dict[int, Tuple[int, int]]:
    coordinates: Dict[int, Tuple[int, int]] = {1: (0, 0)}
    current_pos = 2
    radius = 1

    while current_pos <= hex_count:
        for coord in _hex_ring(0, 0, radius):
            if current_pos > hex_count:
                break
            coordinates[current_pos] = coord
            current_pos += 1
        radius += 1

        if radius > 100:
            break

    return coordinates


def _hex_to_pixel(q: int, r: int, size: float) -> Tuple[float, float]:
    # Pointy-top hexagon axial coordinates (matches the rotation in render_realistic_map_png)
    x = size * math.sqrt(3) * (q + r / 2.0)
    y = size * 3.0 / 2.0 * r
    return x, y


def _alliance_color(alliance_id: Optional[int], color_from_db: Optional[str]) -> str:
    if color_from_db:
        return color_from_db
    if alliance_id is None or alliance_id == 0:
        return NEUTRAL_BORDER_COLOR
    return ALLIANCE_FALLBACK_COLORS[(int(alliance_id) - 1) % len(ALLIANCE_FALLBACK_COLORS)]


def _normalize_terrain_name(name: str) -> str:
    cleaned = " ".join((name or "").split())
    if not cleaned:
        return cleaned

    # Exact lookup first (fast path).
    direct = TERRAIN_ALIASES.get(cleaned)
    if direct:
        return direct

    # Case-insensitive fallback for legacy datasets.
    lower_cleaned = cleaned.lower()
    for alias, canonical in TERRAIN_ALIASES.items():
        if alias.lower() == lower_cleaned:
            return canonical
    return cleaned


def _draw_sprite_trees(ax, x: float, y: float, size: float) -> None:
    """Draw 3 stylized pine tree triangles inside a Lesa hex."""
    positions = [(-0.25, 0.06), (0.21, 0.10), (-0.02, -0.20)]
    h = size * 0.22
    w = size * 0.13
    for dx, dy in positions:
        tx, ty = x + dx * size, y + dy * size
        tree = patches.Polygon(
            [(tx, ty + h), (tx - w, ty - h * 0.45), (tx + w, ty - h * 0.45)],
            facecolor="#1B5E20", edgecolor="#0D3B12", linewidth=0.4, zorder=4,
        )
        ax.add_patch(tree)


def _draw_sprite_city(ax, x: float, y: float, size: float, ruined: bool = False) -> None:
    """Draw 3 stylized multi-story buildings inside a Gorod hex."""
    body_color = "#4A5568" if ruined else "#455A64"
    win_color = "#9CA3AF" if ruined else "#FBBF24"
    # (x_offset, y_base, width, height) in size units relative to hex center
    buildings = [
        (-0.26, -0.22, 0.16, 0.30),
        (-0.02, -0.28, 0.18, 0.46),
        (0.24,  -0.20, 0.15, 0.24),
    ]
    for bx_off, by_off, bw, bh in buildings:
        bx = x + bx_off * size
        by = y + by_off * size
        bw_px = bw * size
        bh_px = bh * size
        if ruined:
            pts = [
                (bx,               by),
                (bx + bw_px,       by),
                (bx + bw_px,       by + bh_px * 0.75),
                (bx + bw_px * 0.7, by + bh_px),
                (bx + bw_px * 0.5, by + bh_px * 0.82),
                (bx + bw_px * 0.3, by + bh_px * 0.95),
                (bx,               by + bh_px * 0.60),
            ]
            building = patches.Polygon(
                pts, facecolor=body_color, edgecolor="#263238", linewidth=0.5, zorder=4
            )
        else:
            building = patches.Rectangle(
                (bx, by), bw_px, bh_px,
                facecolor=body_color, edgecolor="#263238", linewidth=0.5, zorder=4,
            )
        ax.add_patch(building)
        if not ruined:
            ww = bw_px * 0.23
            wh = bh_px * 0.11
            col_xs = [bx + bw_px * 0.15, bx + bw_px * 0.60]
            row_ys = [by + bh_px * (0.10 + row_i * 0.28) for row_i in range(3)]
            for wy in row_ys:
                for wx_win in col_xs:
                    ax.add_patch(patches.Rectangle(
                        (wx_win, wy), ww, wh,
                        facecolor=win_color, edgecolor="none", linewidth=0, zorder=5,
                    ))


def _draw_sprite_factory(ax, x: float, y: float, size: float) -> None:
    """Draw a stylized blast furnace for Zavod terrain."""
    bx = x - size * 0.24
    by = y - size * 0.26
    bw = size * 0.48
    bh = size * 0.30

    ax.add_patch(patches.Rectangle(
        (bx, by), bw, bh,
        facecolor="#5D6D7E", edgecolor="#263238", linewidth=0.6, zorder=4,
    ))

    furnace_w = size * 0.20
    furnace_h = size * 0.42
    fx = x - furnace_w * 0.35
    fy = by + bh * 0.45
    ax.add_patch(patches.Rectangle(
        (fx, fy), furnace_w, furnace_h,
        facecolor="#6F7D8C", edgecolor="#263238", linewidth=0.6, zorder=5,
    ))
    ax.add_patch(patches.Circle(
        (fx + furnace_w / 2, fy + furnace_h),
        radius=furnace_w * 0.5,
        facecolor="#6F7D8C", edgecolor="#263238", linewidth=0.5, zorder=5,
    ))

    chimney_w = size * 0.10
    chimney_h = size * 0.40
    cx = x + size * 0.13
    cy = by + bh * 0.60
    ax.add_patch(patches.Rectangle(
        (cx, cy), chimney_w, chimney_h,
        facecolor="#455A64", edgecolor="#263238", linewidth=0.6, zorder=5,
    ))

    # Furnace glow
    ax.add_patch(patches.Circle((x - size * 0.03, by + size * 0.10), size * 0.06,
                                facecolor="#FFB300", edgecolor="none", alpha=0.95, zorder=6))
    ax.add_patch(patches.Circle((x - size * 0.03, by + size * 0.10), size * 0.03,
                                facecolor="#FFE082", edgecolor="none", alpha=1.0, zorder=7))


def _draw_sprite_ship_wreck(ax, x: float, y: float, size: float) -> None:
    """Draw a broken spaceship wreck fragment."""
    pts = [
        (x - size * 0.34, y - size * 0.08),
        (x - size * 0.18, y + size * 0.12),
        (x + size * 0.12, y + size * 0.08),
        (x + size * 0.30, y - size * 0.02),
        (x + size * 0.10, y - size * 0.18),
        (x - size * 0.22, y - size * 0.20),
    ]
    ax.add_patch(patches.Polygon(
        pts, facecolor="#90A4AE", edgecolor="#37474F", linewidth=0.7, zorder=4
    ))
    ax.add_patch(patches.Circle((x - size * 0.06, y - size * 0.02), size * 0.04,
                                facecolor="#546E7A", edgecolor="#37474F", linewidth=0.4, zorder=5))
    ax.add_patch(patches.Circle((x + size * 0.09, y - size * 0.07), size * 0.03,
                                facecolor="#546E7A", edgecolor="#37474F", linewidth=0.4, zorder=5))
    ax.plot([x - size * 0.26, x - size * 0.12], [y + size * 0.02, y + size * 0.18],
            color="#37474F", linewidth=0.7, zorder=5)
    ax.plot([x + size * 0.20, x + size * 0.33], [y - size * 0.01, y + size * 0.09],
            color="#37474F", linewidth=0.7, zorder=5)


def _draw_sprite_toxic_bubble(ax, x: float, y: float, size: float) -> None:
    """Draw a toxic pus-like blister for poisoned lands."""
    bubbles = [
        (-0.12, -0.06, 0.11, "#8BC34A"),
        (0.09, -0.01, 0.10, "#9CCC65"),
        (-0.02, 0.10, 0.08, "#AED581"),
    ]
    for dx, dy, rr, color in bubbles:
        cx = x + dx * size
        cy = y + dy * size
        r = rr * size
        ax.add_patch(patches.Circle(
            (cx, cy), r,
            facecolor=color, edgecolor="#558B2F", linewidth=0.6, zorder=4,
        ))
        ax.add_patch(patches.Circle(
            (cx - r * 0.25, cy + r * 0.20), r * 0.28,
            facecolor="#E6EE9C", edgecolor="none", alpha=0.85, zorder=5,
        ))


def _draw_sprite_ruined_city(ax, x: float, y: float, size: float) -> None:
    """Draw a ruined multi-story tower silhouette."""
    bx = x - size * 0.14
    by = y - size * 0.28
    bw = size * 0.28
    bh = size * 0.56
    ruins = [
        (bx, by),
        (bx + bw, by),
        (bx + bw, by + bh * 0.72),
        (bx + bw * 0.82, by + bh * 0.95),
        (bx + bw * 0.63, by + bh * 0.78),
        (bx + bw * 0.46, by + bh),
        (bx + bw * 0.30, by + bh * 0.80),
        (bx + bw * 0.15, by + bh * 0.90),
        (bx, by + bh * 0.62),
    ]
    ax.add_patch(patches.Polygon(
        ruins, facecolor="#5D4037", edgecolor="#3E2723", linewidth=0.6, zorder=4
    ))
    for wx in [bx + bw * 0.20, bx + bw * 0.55]:
        for wy in [by + bh * 0.16, by + bh * 0.36, by + bh * 0.54]:
            ax.add_patch(patches.Rectangle(
                (wx, wy), bw * 0.16, bh * 0.08,
                facecolor="#3E2723", edgecolor="none", zorder=5,
            ))


def _draw_sprite_junkyard(ax, x: float, y: float, size: float) -> None:
    """Draw a junk pile sprite for Svaka terrain."""
    ax.add_patch(patches.Polygon(
        [
            (x - size * 0.30, y - size * 0.18),
            (x - size * 0.08, y + size * 0.05),
            (x + size * 0.08, y - size * 0.02),
            (x + size * 0.30, y - size * 0.20),
            (x + size * 0.22, y - size * 0.30),
            (x - size * 0.22, y - size * 0.30),
        ],
        facecolor="#8D6E63", edgecolor="#4E342E", linewidth=0.6, zorder=4,
    ))
    ax.add_patch(patches.Rectangle(
        (x - size * 0.24, y - size * 0.09), size * 0.12, size * 0.05,
        facecolor="#9E9E9E", edgecolor="#616161", linewidth=0.4, zorder=5,
    ))
    ax.add_patch(patches.Rectangle(
        (x + size * 0.02, y - size * 0.15), size * 0.16, size * 0.06,
        facecolor="#B0BEC5", edgecolor="#616161", linewidth=0.4, zorder=5,
    ))
    ax.add_patch(patches.Circle(
        (x - size * 0.02, y - size * 0.14), size * 0.05,
        facecolor="#424242", edgecolor="#212121", linewidth=0.5, zorder=5,
    ))


def _hex_to_rgb(hex_color: str) -> Tuple[float, float, float]:
    hex_color = hex_color.lstrip("#")
    return tuple(int(hex_color[i:i + 2], 16) / 255.0 for i in (0, 2, 4))


def _rgb_to_hex(rgb: Tuple[float, float, float]) -> str:
    return "#{:02X}{:02X}{:02X}".format(
        max(0, min(255, int(rgb[0] * 255))),
        max(0, min(255, int(rgb[1] * 255))),
        max(0, min(255, int(rgb[2] * 255))),
    )


def _lerp_color(c1: str, c2: str, t: float) -> str:
    a = _hex_to_rgb(c1)
    b = _hex_to_rgb(c2)
    return _rgb_to_hex((
        a[0] + (b[0] - a[0]) * t,
        a[1] + (b[1] - a[1]) * t,
        a[2] + (b[2] - a[2]) * t,
    ))


def _draw_sprite_warp_tooth(ax, x: float, y: float, size: float) -> None:
    """Draw a tooth-like warp rock with top-to-bottom gradient (light blue -> purple)."""
    base_y = y - size * 0.34
    tip_y = y + size * 0.42
    left_base = x - size * 0.22
    right_base = x + size * 0.24
    tip_x = x + size * 0.02
    slices = 8

    def x_left(y_val: float) -> float:
        t = (y_val - base_y) / (tip_y - base_y)
        return left_base + (tip_x - left_base) * t

    def x_right(y_val: float) -> float:
        t = (y_val - base_y) / (tip_y - base_y)
        return right_base + (tip_x - right_base) * t

    bottom_color = "#6A1B9A"
    top_color = "#B3E5FC"

    for i in range(slices):
        y0 = base_y + (tip_y - base_y) * (i / slices)
        y1 = base_y + (tip_y - base_y) * ((i + 1) / slices)
        t_mid = ((i + 0.5) / slices)
        c = _lerp_color(bottom_color, top_color, t_mid)
        ax.add_patch(patches.Polygon(
            [
                (x_left(y0), y0),
                (x_right(y0), y0),
                (x_right(y1), y1),
                (x_left(y1), y1),
            ],
            facecolor=c, edgecolor="none", zorder=4,
        ))

    ax.add_patch(patches.Polygon(
        [
            (left_base, base_y),
            (right_base, base_y),
            (tip_x, tip_y),
        ],
        facecolor="none", edgecolor="#311B92", linewidth=0.8, zorder=5,
    ))


def _draw_sprite_imperial_temple(ax, x: float, y: float, size: float) -> None:
    """Draw a WH40k-inspired imperial temple silhouette."""
    # Steps/foundation
    ax.add_patch(patches.Rectangle(
        (x - size * 0.30, y - size * 0.30), size * 0.60, size * 0.10,
        facecolor="#D4AF37", edgecolor="#8D6E00", linewidth=0.6, zorder=4,
    ))
    # Main body
    ax.add_patch(patches.Rectangle(
        (x - size * 0.18, y - size * 0.20), size * 0.36, size * 0.34,
        facecolor="#FBC02D", edgecolor="#8D6E00", linewidth=0.7, zorder=5,
    ))
    # Side buttresses
    ax.add_patch(patches.Rectangle(
        (x - size * 0.28, y - size * 0.20), size * 0.08, size * 0.28,
        facecolor="#F9A825", edgecolor="#8D6E00", linewidth=0.5, zorder=5,
    ))
    ax.add_patch(patches.Rectangle(
        (x + size * 0.20, y - size * 0.20), size * 0.08, size * 0.28,
        facecolor="#F9A825", edgecolor="#8D6E00", linewidth=0.5, zorder=5,
    ))
    # Central spire
    ax.add_patch(patches.Polygon(
        [
            (x - size * 0.06, y + size * 0.14),
            (x + size * 0.06, y + size * 0.14),
            (x, y + size * 0.40),
        ],
        facecolor="#FDD835", edgecolor="#8D6E00", linewidth=0.6, zorder=6,
    ))
    # Aquila-like cross mark
    ax.plot([x - size * 0.05, x + size * 0.05], [y + size * 0.03, y + size * 0.03],
            color="#6D4C41", linewidth=1.0, zorder=7)
    ax.plot([x, x], [y - size * 0.02, y + size * 0.08],
            color="#6D4C41", linewidth=1.0, zorder=7)

    # Arched gate
    ax.add_patch(patches.Rectangle(
        (x - size * 0.05, y - size * 0.20), size * 0.10, size * 0.14,
        facecolor="#6D4C41", edgecolor="#4E342E", linewidth=0.4, zorder=6,
    ))


def _draw_sprite_warehouse(ax, x: float, y: float, size: float) -> None:
    """Draw a small warehouse/storage building sprite centered on (x, y)."""
    bw = size * 0.36
    bh = size * 0.24
    bx = x - bw / 2
    by = y - bh / 2 - size * 0.04

    # Drop shadow
    sd = size * 0.035
    ax.add_patch(patches.Rectangle(
        (bx + sd, by - sd), bw, bh,
        facecolor="#111111", alpha=0.30, linewidth=0, zorder=7,
    ))

    # Main body
    ax.add_patch(patches.Rectangle(
        (bx, by), bw, bh,
        facecolor="#B0BEC5", edgecolor="#263238", linewidth=0.6, zorder=8,
    ))

    # Roof — trapezoid (slightly wider at base, narrower at top)
    roof_overhang = size * 0.03
    roof_h = size * 0.10
    roof_pts = [
        (bx - roof_overhang,       by + bh),
        (bx + bw + roof_overhang,  by + bh),
        (bx + bw - size * 0.04,    by + bh + roof_h),
        (bx + size * 0.04,         by + bh + roof_h),
    ]
    ax.add_patch(patches.Polygon(
        roof_pts, facecolor="#78909C", edgecolor="#263238", linewidth=0.5, zorder=8,
    ))

    # Roller door (bottom-center, wide rectangle)
    dw = bw * 0.48
    dh = bh * 0.52
    dx = bx + (bw - dw) / 2
    dy = by
    ax.add_patch(patches.Rectangle(
        (dx, dy), dw, dh,
        facecolor="#546E7A", edgecolor="#263238", linewidth=0.4, zorder=9,
    ))
    # Horizontal panels on the door
    for i in range(1, 3):
        panel_y = dy + dh * i / 3
        ax.plot([dx, dx + dw], [panel_y, panel_y],
                color="#37474F", linewidth=0.3, zorder=9)


def render_realistic_map_png(
    map_cells: Iterable[Tuple[int, str, Optional[int], int]],
    alliances: Iterable[Tuple[int, str, Optional[str]]],
    terrain_colors: Optional[Dict[str, str]] = None,
) -> bytes:
    """Render full planet hex map to PNG bytes.

    map_cells rows: (id, state, patron, has_warehouse)
    alliances rows: (id, name, color)
    terrain_colors: optional dict name->hex_color from DB (overrides built-in TERRAIN_STYLES)
    """
    ordered_cells = sorted(list(map_cells), key=lambda row: row[0])
    if not ordered_cells:
        raise ValueError("No map data available for export")

    alliance_by_id = {
        row[0]: {"name": row[1], "color": _alliance_color(row[0], row[2])}
        for row in alliances
    }

    # Merge terrain colors: DB values override built-in defaults
    effective_styles: Dict[str, Dict] = {n: dict(v) for n, v in TERRAIN_STYLES.items()}
    if terrain_colors:
        for name, color in terrain_colors.items():
            normalized_name = _normalize_terrain_name(name)
            if normalized_name in effective_styles:
                effective_styles[normalized_name]["fill"] = color
            else:
                effective_styles[normalized_name] = {"fill": color}

    coordinates = _reconstruct_coordinates(len(ordered_cells))

    hex_count = len(ordered_cells)
    # Scale figure size based on number of hexes (min 10, max 24)
    fig_side = max(10, min(24, int(math.sqrt(hex_count) * 2.5)))
    fig, ax = plt.subplots(1, 1, figsize=(fig_side, fig_side))
    hex_size = 1.0

    # --- Pass 1: build coord -> patron/color lookup tables ---
    coord_to_patron: Dict[Tuple[int, int], int] = {}
    coord_to_color: Dict[Tuple[int, int], str] = {}
    for idx, row in enumerate(ordered_cells, start=1):
        _, _, patron, _ = row
        if idx in coordinates:
            q, r = coordinates[idx]
            owner_id = int(patron) if patron is not None else 0
            coord_to_patron[(q, r)] = owner_id
            if owner_id and owner_id in alliance_by_id:
                coord_to_color[(q, r)] = alliance_by_id[owner_id]["color"]
            else:
                coord_to_color[(q, r)] = NEUTRAL_BORDER_COLOR

    terrain_seen: set = set()
    alliances_seen: set = set()

    # --- Pass 2: draw hex fills, pseudo-3D shadows, and terrain sprites ---
    for idx, row in enumerate(ordered_cells, start=1):
        _, state, patron, has_warehouse = row
        q, r = coordinates[idx]
        x, y = _hex_to_pixel(q, r, hex_size)
        normalized_state = _normalize_terrain_name(state)

        style = effective_styles.get(normalized_state, DEFAULT_TERRAIN_STYLE)
        terrain_seen.add(normalized_state)

        angles = np.linspace(0, 2 * np.pi, 7)
        x_coords = x + hex_size * np.cos(angles + np.pi / 6)
        y_coords = y + hex_size * np.sin(angles + np.pi / 6)
        points = list(zip(x_coords, y_coords))

        # Pseudo-3D drop shadow (dark polygon shifted south-east)
        sd = hex_size * 0.055
        shadow_pts = [(px + sd, py - sd) for px, py in points]
        ax.add_patch(patches.Polygon(shadow_pts, facecolor="#111111", alpha=0.20, zorder=1))

        # Terrain fill (clean, no hatch)
        ax.add_patch(patches.Polygon(
            points,
            facecolor=style["fill"],
            edgecolor="#1a1a1a",
            linewidth=0.35,
            zorder=2,
        ))

        # Terrain sprites
        if normalized_state == "Леса":
            _draw_sprite_trees(ax, x, y, hex_size)
        elif normalized_state == "Город":
            _draw_sprite_city(ax, x, y, hex_size, ruined=False)
        elif normalized_state == "Разрушенный город":
            _draw_sprite_ruined_city(ax, x, y, hex_size)
        elif normalized_state == "Завод":
            _draw_sprite_factory(ax, x, y, hex_size)
        elif normalized_state == "Изменённое варпом пространство":
            _draw_sprite_warp_tooth(ax, x, y, hex_size)
        elif normalized_state == "Останки корабля":
            _draw_sprite_ship_wreck(ax, x, y, hex_size)
        elif normalized_state == "Отравленные земли":
            _draw_sprite_toxic_bubble(ax, x, y, hex_size)
        elif normalized_state == "Свалка":
            _draw_sprite_junkyard(ax, x, y, hex_size)
        elif normalized_state == "Храмовый квартал":
            _draw_sprite_imperial_temple(ax, x, y, hex_size)

        owner_id = coord_to_patron.get((q, r), 0)
        if owner_id:
            alliances_seen.add(owner_id)

        if has_warehouse:
            _draw_sprite_warehouse(ax, x, y, hex_size)

    # --- Pass 3: alliance borders (inset inside each hex) ---
    # Batch all border segments per (color, linewidth) into LineCollections to
    # avoid creating thousands of individual matplotlib Artists.
    BORDER_ALPHA = 0.65
    BORDER_INSET = 0.91

    # Collect segments grouped by (color, linewidth)
    border_segments: Dict[Tuple[str, float], List] = {}

    for idx, row in enumerate(ordered_cells, start=1):
        q, r = coordinates[idx]
        x, y = _hex_to_pixel(q, r, hex_size)
        this_patron = coord_to_patron.get((q, r), 0)
        edge_color = coord_to_color.get((q, r), NEUTRAL_BORDER_COLOR)

        # Inset vertices are pulled slightly toward hex center.
        verts = [
            (
                x + (hex_size * BORDER_INSET) * math.cos(math.pi / 6 + k * math.pi / 3),
                y + (hex_size * BORDER_INSET) * math.sin(math.pi / 6 + k * math.pi / 3),
            )
            for k in range(6)
        ]

        for (dq, dr), (vi, vj) in _DIRECTION_EDGE_VERTICES.items():
            neighbor_patron = coord_to_patron.get((q + dq, r + dr))  # None = outside map
            if neighbor_patron == this_patron:
                continue

            lw = 2.1 if this_patron else 0.7
            key = (edge_color, lw)
            if key not in border_segments:
                border_segments[key] = []
            x1, y1 = verts[vi]
            x2, y2 = verts[vj]
            border_segments[key].append([(x1, y1), (x2, y2)])

    for (color, lw), segs in border_segments.items():
        lc = LineCollection(segs, colors=color, linewidths=lw, alpha=BORDER_ALPHA, zorder=5)
        ax.add_collection(lc)

    # --- Pass 4: redraw hex grid above alliance borders ---
    # Batch all hex outlines into a single LineCollection.
    grid_segments = []
    for idx, _row in enumerate(ordered_cells, start=1):
        q, r = coordinates[idx]
        x, y = _hex_to_pixel(q, r, hex_size)
        angles = np.linspace(0, 2 * np.pi, 7)
        x_coords = x + hex_size * np.cos(angles + np.pi / 6)
        y_coords = y + hex_size * np.sin(angles + np.pi / 6)
        # Each hex outline is 6 edges (7 points forming a closed polygon)
        pts = list(zip(x_coords.tolist(), y_coords.tolist()))
        for i in range(6):
            grid_segments.append([pts[i], pts[i + 1]])

    grid_lc = LineCollection(grid_segments, colors="#1a1a1a", linewidths=0.35, alpha=0.85, zorder=6)
    ax.add_collection(grid_lc)

    # Explicitly set axis limits based on actual hex positions (add_patch doesn't autoscale)
    all_x = [_hex_to_pixel(q, r, hex_size)[0] for q, r in coordinates.values()]
    all_y = [_hex_to_pixel(q, r, hex_size)[1] for q, r in coordinates.values()]
    margin = hex_size * 2.0
    ax.set_xlim(min(all_x) - margin, max(all_x) + margin)
    ax.set_ylim(min(all_y) - margin, max(all_y) + margin)

    ax.set_aspect("equal")
    ax.set_title("Planet Control Map", fontsize=20, fontweight="bold")
    ax.set_xticks([])
    ax.set_yticks([])
    for spine in ax.spines.values():
        spine.set_visible(False)

    terrain_handles = []
    for terrain_name in sorted(terrain_seen):
        style = effective_styles.get(terrain_name, DEFAULT_TERRAIN_STYLE)
        terrain_handles.append(
            patches.Patch(
                facecolor=style["fill"],
                edgecolor="#263238",
                label=terrain_name,
            )
        )

    alliance_handles = []
    for alliance_id in sorted(alliances_seen):
        data = alliance_by_id.get(alliance_id)
        if not data:
            continue
        alliance_handles.append(
            patches.Patch(
                facecolor="white",
                edgecolor=data["color"],
                linewidth=2,
                label=data["name"],
            )
        )

    if terrain_handles:
        terrain_legend = ax.legend(
            handles=terrain_handles,
            title="Terrain",
            loc="upper left",
            bbox_to_anchor=(1.02, 1.0),
        )
        ax.add_artist(terrain_legend)

    if alliance_handles:
        ax.legend(
            handles=alliance_handles,
            title="Alliance Borders",
            loc="lower left",
            bbox_to_anchor=(1.02, 0.0),
        )

    plt.tight_layout()
    output = BytesIO()
    # Telegram photo limit: width + height <= 10000 (max ~5000px per side for square).
    # At fig_side=24in, dpi=150 → 3600px/side → sum=7200 — safe.
    # Raspberry Pi: cap at 100 dpi to reduce CPU/RAM load while keeping
    # the image readable in Telegram (max ~2400 px/side at fig_side=24).
    dpi = min(100, int(3000 / fig_side))
    fig.savefig(output, format="png", dpi=dpi, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    return output.getvalue()