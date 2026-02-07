# -*- coding: utf-8 -*-
"""
Генерация визуальной карты планеты с гексами, раскрашенными по альянсам.
Данные загружаются с production через SSH.
"""
import subprocess
import math
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.patches import RegularPolygon
from collections import defaultdict

# ── Цвета альянсов ──────────────────────────────────────────────
ALLIANCE_COLORS = {
    4: "#E63946",   # Щит Молот и Пламя — красный
    5: "#457B9D",   # Эвакуация — синий
    6: "#2A9D8F",   # Вектор Нургла — бирюзовый
    7: "#E9C46A",   # Идея — жёлтый
    8: "#F4A261",   # Очищение — оранжевый
    9: "#6A4C93",   # Синдикат реконструкции — фиолетовый
}

ALLIANCE_NAMES = {
    4: "Щит Молот и Пламя",
    5: "Эвакуация",
    6: "Вектор Нургла",
    7: "Идея",
    8: "Очищение",
    9: "Синдикат реконструкции",
}

# ── Hex geometry ─────────────────────────────────────────────────
HEX_DIRECTIONS = [
    (1, 0), (1, -1), (0, -1),
    (-1, 0), (-1, 1), (0, 1)
]


def hex_ring(center_q, center_r, radius):
    if radius == 0:
        return [(center_q, center_r)]
    results = []
    q = center_q + HEX_DIRECTIONS[4][0] * radius
    r = center_r + HEX_DIRECTIONS[4][1] * radius
    for i in range(6):
        for _ in range(radius):
            results.append((q, r))
            dq, dr = HEX_DIRECTIONS[i]
            q += dq
            r += dr
    return results


def hex_to_pixel(q, r, size):
    """Axial hex → pixel (flat-top orientation)."""
    x = size * (3 / 2 * q)
    y = size * (math.sqrt(3) / 2 * q + math.sqrt(3) * r)
    return x, y


def reconstruct_coordinates(total_hexes):
    """Return dict  hex_id → (q, r)  using the same ring-walk as generate_planet.py."""
    coords = {1: (0, 0)}
    current_id = 2
    radius = 1
    while current_id <= total_hexes:
        for q, r in hex_ring(0, 0, radius):
            if current_id > total_hexes:
                break
            coords[current_id] = (q, r)
            current_id += 1
        radius += 1
        if radius > 50:
            break
    return coords


# ── SSH helpers ──────────────────────────────────────────────────
SSH_HOST = "ubuntu@192.168.1.125"
CONTAINER = "carebot_production"


def ssh_query(sql):
    cmd = f'ssh {SSH_HOST} "docker exec {CONTAINER} sqlite3 /app/data/game_database.db \\"{sql}\\""'
    result = subprocess.run(cmd, shell=True, capture_output=True, timeout=30)
    if result.returncode != 0:
        raise RuntimeError(f"SSH query failed: {result.stderr.decode('utf-8', errors='replace')}")
    return result.stdout.decode('utf-8', errors='replace').strip()


def fetch_alliances():
    raw = ssh_query("SELECT id, name FROM alliances ORDER BY id;")
    alliances = {}
    for line in raw.splitlines():
        parts = line.split("|")
        alliances[int(parts[0])] = parts[1]
    return alliances


def fetch_map():
    raw = ssh_query("SELECT id, patron, has_warehouse FROM map ORDER BY id;")
    hexes = []
    for line in raw.splitlines():
        parts = line.split("|")
        hexes.append({
            "id": int(parts[0]),
            "patron": int(parts[1]) if parts[1] else None,
            "warehouse": int(parts[2]) if parts[2] else 0,
        })
    return hexes


def fetch_edges():
    raw = ssh_query("SELECT left_hexagon, right_hexagon FROM edges ORDER BY id;")
    edges = []
    for line in raw.splitlines():
        parts = line.split("|")
        edges.append((int(parts[0]), int(parts[1])))
    return edges


# ── Drawing ──────────────────────────────────────────────────────
def draw_map(hexes, edges, output_path="planet_map.png"):
    coords = reconstruct_coordinates(len(hexes))

    hex_size = 1.0
    fig, ax = plt.subplots(1, 1, figsize=(28, 28), facecolor='#1a1a2e')
    ax.set_facecolor('#1a1a2e')

    # Собираем pixel-координаты для edges
    id_to_pixel = {}
    for h in hexes:
        hid = h["id"]
        if hid in coords:
            q, r = coords[hid]
            px, py = hex_to_pixel(q, r, hex_size)
            id_to_pixel[hid] = (px, py)

    # Рисуем рёбра (связи)
    for left, right in edges:
        if left in id_to_pixel and right in id_to_pixel:
            x0, y0 = id_to_pixel[left]
            x1, y1 = id_to_pixel[right]
            ax.plot([x0, x1], [y0, y1], color='#2a2a4a', linewidth=0.3, zorder=0)

    # Рисуем гексы
    for h in hexes:
        hid = h["id"]
        patron = h["patron"]
        warehouse = h["warehouse"]

        if hid not in coords:
            continue

        q, r = coords[hid]
        px, py = hex_to_pixel(q, r, hex_size)

        color = ALLIANCE_COLORS.get(patron, "#555555")

        # Рисуем гекс
        hex_patch = RegularPolygon(
            (px, py), numVertices=6, radius=hex_size * 0.95,
            orientation=np.radians(30),
            facecolor=color, edgecolor='#0d0d1a', linewidth=0.6,
            alpha=0.85, zorder=1
        )
        ax.add_patch(hex_patch)

        # Номер гекса
        ax.text(px, py + 0.05, str(hid), ha='center', va='center',
                fontsize=4.0, color='white', fontweight='bold', zorder=3)

        # Маркер склада
        if warehouse:
            ax.plot(px, py - 0.3, marker='s', color='#FFD700', markersize=3,
                    markeredgecolor='white', markeredgewidth=0.3, zorder=4)

    # Настройки
    ax.set_aspect('equal')
    ax.autoscale_view()
    margin = 2
    xlims = ax.get_xlim()
    ylims = ax.get_ylim()
    ax.set_xlim(xlims[0] - margin, xlims[1] + margin)
    ax.set_ylim(ylims[0] - margin, ylims[1] + margin)
    ax.set_xticks([])
    ax.set_yticks([])
    for spine in ax.spines.values():
        spine.set_visible(False)

    # Заголовок
    ax.set_title('Карта Планеты — Территории Альянсов', fontsize=22,
                 fontweight='bold', color='white', pad=20)

    # Легенда
    legend_patches = []
    # Считаем территории
    territory_counts = defaultdict(int)
    for h in hexes:
        territory_counts[h["patron"]] += 1

    for aid in sorted(ALLIANCE_COLORS.keys()):
        name = ALLIANCE_NAMES.get(aid, f"Alliance {aid}")
        count = territory_counts.get(aid, 0)
        legend_patches.append(
            patches.Patch(
                facecolor=ALLIANCE_COLORS[aid],
                edgecolor='white',
                label=f"{name} ({count} гексов)"
            )
        )

    legend = ax.legend(
        handles=legend_patches,
        loc='upper left',
        bbox_to_anchor=(0.0, 1.0),
        fontsize=10,
        framealpha=0.8,
        facecolor='#1a1a2e',
        edgecolor='white',
        labelcolor='white',
        title='Альянсы',
        title_fontsize=12,
    )
    legend.get_title().set_color('white')

    plt.tight_layout()
    plt.savefig(output_path, dpi=200, bbox_inches='tight',
                facecolor='#1a1a2e', edgecolor='none')
    plt.close()
    print(f"✅ Карта сохранена: {output_path}")
    return output_path


# ── Main ─────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("Загрузка данных с production...")
    alliances = fetch_alliances()
    print(f"  Альянсы: {len(alliances)}")
    for aid, name in alliances.items():
        print(f"    {aid}: {name}")

    hexes = fetch_map()
    print(f"  Гексов: {len(hexes)}")

    edges = fetch_edges()
    print(f"  Рёбер: {len(edges)}")

    output = draw_map(hexes, edges, output_path="planet_map.png")
