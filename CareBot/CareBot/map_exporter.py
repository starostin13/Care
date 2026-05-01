"""Utilities for rendering a realistic hex map export as PNG bytes."""

from io import BytesIO
import math
from typing import Dict, Iterable, List, Optional, Tuple

import matplotlib.patches as patches
import matplotlib.pyplot as plt
import numpy as np


TERRAIN_STYLES: Dict[str, Dict[str, str]] = {
    "Леса": {"fill": "#2E7D32", "hatch": "..."},
    "Тундра/снег": {"fill": "#E3F2FD", "hatch": "//"},
    "Пустыня": {"fill": "#D4A373", "hatch": ".."},
    "Отравленные земли": {"fill": "#6B8E23", "hatch": "xx"},
    "Завод": {"fill": "#6C757D", "hatch": "++"},
    "Город": {"fill": "#5C6BC0", "hatch": "||"},
    "Разрушенный город": {"fill": "#8D6E63", "hatch": "//"},
    "Подземные системы": {"fill": "#37474F", "hatch": "\\\\"},
    "Останки корабля": {"fill": "#B0BEC5", "hatch": "--"},
    "Свалка": {"fill": "#8D6E63", "hatch": "xx"},
    "Храовый квартал": {"fill": "#FBC02D", "hatch": "oo"},
    "Изменённое варпом пространство": {"fill": "#6A1B9A", "hatch": "**"},
}

DEFAULT_TERRAIN_STYLE = {"fill": "#CFD8DC", "hatch": ""}
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


def render_realistic_map_png(
    map_cells: Iterable[Tuple[int, str, Optional[int], int]],
    alliances: Iterable[Tuple[int, str, Optional[str]]],
) -> bytes:
    """Render full planet hex map to PNG bytes.

    map_cells rows: (id, state, patron, has_warehouse)
    alliances rows: (id, name, color)
    """
    ordered_cells = sorted(list(map_cells), key=lambda row: row[0])
    if not ordered_cells:
        raise ValueError("No map data available for export")

    alliance_by_id = {
        row[0]: {"name": row[1], "color": _alliance_color(row[0], row[2])}
        for row in alliances
    }

    coordinates = _reconstruct_coordinates(len(ordered_cells))

    hex_count = len(ordered_cells)
    # Scale figure size based on number of hexes (min 10, max 24)
    fig_side = max(10, min(24, int(math.sqrt(hex_count) * 2.5)))
    fig, ax = plt.subplots(1, 1, figsize=(fig_side, fig_side))
    hex_size = 1.0

    terrain_seen = set()
    alliances_seen = set()

    for idx, row in enumerate(ordered_cells, start=1):
        _, state, patron, has_warehouse = row
        q, r = coordinates[idx]
        x, y = _hex_to_pixel(q, r, hex_size)

        style = TERRAIN_STYLES.get(state, DEFAULT_TERRAIN_STYLE)
        terrain_seen.add(state)

        angles = np.linspace(0, 2 * np.pi, 7)
        x_coords = x + hex_size * np.cos(angles + np.pi / 6)
        y_coords = y + hex_size * np.sin(angles + np.pi / 6)
        points = list(zip(x_coords, y_coords))

        fill_hex = patches.Polygon(
            points,
            facecolor=style["fill"],
            edgecolor="#263238",
            linewidth=0.6,
            hatch=style["hatch"],
        )
        ax.add_patch(fill_hex)

        owner_id = int(patron) if patron is not None else 0
        owner_color = NEUTRAL_BORDER_COLOR
        if owner_id and owner_id in alliance_by_id:
            owner_color = alliance_by_id[owner_id]["color"]
            alliances_seen.add(owner_id)
        elif owner_id:
            owner_color = _alliance_color(owner_id, None)

        border_hex = patches.Polygon(
            points,
            facecolor="none",
            edgecolor=owner_color,
            linewidth=2.1 if owner_id else 0.9,
        )
        ax.add_patch(border_hex)

        if has_warehouse:
            warehouse_marker = patches.Circle((x, y), radius=0.18, color="#212121", zorder=5)
            ax.add_patch(warehouse_marker)

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
        style = TERRAIN_STYLES.get(terrain_name, DEFAULT_TERRAIN_STYLE)
        terrain_handles.append(
            patches.Patch(
                facecolor=style["fill"],
                edgecolor="#263238",
                hatch=style["hatch"],
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
    dpi = min(150, int(4500 / fig_side))
    fig.savefig(output, format="png", dpi=dpi, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    return output.getvalue()