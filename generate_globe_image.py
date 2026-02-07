# -*- coding: utf-8 -*-
"""
Визуализация гексагональной карты планеты в виде 3D сферы.
Гексы проецируются на поверхность шара с раскраской по альянсам.
"""
import subprocess
import math
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
from collections import defaultdict

# ── Цвета по типу территории (state) ────────────────────────────
STATE_COLORS = {
    "Forest":               "#1B5E20",
    "Tundra/Snow":          "#B0BEC5",
    "Desert":               "#D4A056",
    "Poisoned Lands":       "#4E6B3A",
    "Factory":              "#616161",
    "City":                 "#546E7A",
    "Ruined City":          "#6D4C41",
    "Underground Systems":  "#37474F",
    "Ship Wreckage":        "#90A4AE",
    "Junkyard":             "#795548",
    "Temple Quarter":       "#C49A2D",
    "Warp-altered Space":   "#7B1FA2",
}

STATE_NAMES_RU = {
    "Forest":               "Леса",
    "Tundra/Snow":          "Тундра / снег",
    "Desert":               "Пустыня",
    "Poisoned Lands":       "Отравленные земли",
    "Factory":              "Завод",
    "City":                 "Город",
    "Ruined City":          "Разрушенный город",
    "Underground Systems":  "Подземные системы",
    "Ship Wreckage":        "Останки корабля",
    "Junkyard":             "Свалка",
    "Temple Quarter":       "Храмовый квартал",
    "Warp-altered Space":   "Изменённое варпом",
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


def hex_to_pixel(q, r, size=1.0):
    """Axial hex → pixel (flat-top)."""
    x = size * (3 / 2 * q)
    y = size * (math.sqrt(3) / 2 * q + math.sqrt(3) * r)
    return x, y


def hex_polygon_vertices(cx, cy, size=1.0):
    """6 вершин гекса в плоских координатах (flat-top)."""
    angles = np.linspace(0, 2 * np.pi, 7)[:-1] + np.pi / 6
    vx = cx + size * 0.92 * np.cos(angles)
    vy = cy + size * 0.92 * np.sin(angles)
    return list(zip(vx, vy))


def reconstruct_coordinates(total_hexes):
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


# ── Проекция на сферу ────────────────────────────────────────────
def flat_to_sphere(fx, fy, max_radius, sphere_radius=1.0):
    """
    Проецирует плоскую точку (fx, fy) на сферу.
    Используется азимутальная равнопромежуточная проекция:
    центр карты → северный полюс, край → немного за экватор.
    """
    d = math.sqrt(fx * fx + fy * fy)
    alpha = math.atan2(fy, fx)

    # Масштаб: покрываем ~160° широты (от полюса почти до южного полюса)
    coverage = np.radians(160)
    phi = np.pi / 2 - (d / max_radius) * (coverage / 2)  # широта
    theta = alpha  # долгота

    # Сферические → декартовы
    x = sphere_radius * math.cos(phi) * math.cos(theta)
    y = sphere_radius * math.cos(phi) * math.sin(theta)
    z = sphere_radius * math.sin(phi)
    return x, y, z


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
    raw = ssh_query("SELECT id, patron, has_warehouse, state FROM map ORDER BY id;")
    hexes = []
    for line in raw.splitlines():
        parts = line.split("|")
        hexes.append({
            "id": int(parts[0]),
            "patron": int(parts[1]) if parts[1] else None,
            "warehouse": int(parts[2]) if parts[2] else 0,
            "state": parts[3] if len(parts) > 3 else None,
        })
    return hexes


def fetch_edges():
    raw = ssh_query("SELECT left_hexagon, right_hexagon FROM edges ORDER BY id;")
    edges = []
    for line in raw.splitlines():
        parts = line.split("|")
        edges.append((int(parts[0]), int(parts[1])))
    return edges


# ── Отрисовка 3D глобуса ────────────────────────────────────────
def draw_globe(hexes, edges, output_path="planet_globe.png"):
    coords = reconstruct_coordinates(len(hexes))

    # Определяем максимальный радиус на плоскости
    max_flat_r = 0
    flat_positions = {}
    for h in hexes:
        hid = h["id"]
        if hid in coords:
            q, r = coords[hid]
            fx, fy = hex_to_pixel(q, r)
            flat_positions[hid] = (fx, fy)
            d = math.sqrt(fx * fx + fy * fy)
            if d > max_flat_r:
                max_flat_r = d
    max_flat_r *= 1.08  # Добавляем чуть запаса

    R = 1.0  # Радиус сферы

    # ── Рисуем сферу-подложку ────────────────────────────────────
    fig = plt.figure(figsize=(22, 22), facecolor='#0a0a1a')

    # 4 ракурса для полного обзора
    views = [
        (30, 45, "Вид спереди-сверху"),
        (30, 225, "Вид сзади-сверху"),
        (-30, 135, "Вид сбоку-снизу"),
        (80, 0, "Вид сверху (полюс)"),
    ]

    for idx, (elev, azim, title) in enumerate(views):
        ax = fig.add_subplot(2, 2, idx + 1, projection='3d', facecolor='#0a0a1a')

        # Wireframe сфера (подложка)
        u = np.linspace(0, 2 * np.pi, 60)
        v = np.linspace(0, np.pi, 40)
        xs = R * 0.98 * np.outer(np.cos(u), np.sin(v))
        ys = R * 0.98 * np.outer(np.sin(u), np.sin(v))
        zs = R * 0.98 * np.outer(np.ones(np.size(u)), np.cos(v))
        ax.plot_surface(xs, ys, zs, color='#15152a', alpha=0.3,
                        edgecolor='#1a1a3a', linewidth=0.1)

        # ── Рисуем гексагональные полигоны на сфере ──────────────
        polys = []
        poly_colors = []
        poly_ids = []

        for h in hexes:
            hid = h["id"]
            patron = h["patron"]
            if hid not in flat_positions:
                continue
            fx, fy = flat_positions[hid]
            state = h.get("state", "")
            color = STATE_COLORS.get(state, "#444444")

            # Вершины гекса в плоскости → на сферу
            flat_verts = hex_polygon_vertices(fx, fy, size=1.0)
            sphere_verts = []
            for vx, vy in flat_verts:
                sx, sy, sz = flat_to_sphere(vx, vy, max_flat_r, R)
                sphere_verts.append((sx, sy, sz))

            polys.append(sphere_verts)
            poly_colors.append(color)
            poly_ids.append(hid)

        # Batch add для скорости
        poly_collection = Poly3DCollection(
            polys, alpha=0.95,
            edgecolors='none', linewidths=0
        )
        poly_collection.set_facecolor(poly_colors)
        ax.add_collection3d(poly_collection)

        # ── Номера гексов (только для вида сверху — полюс) ───────
        if idx == 3:  # Вид сверху — показываем номера центральных гексов
            for h in hexes:
                hid = h["id"]
                if hid not in flat_positions:
                    continue
                fx, fy = flat_positions[hid]
                d = math.sqrt(fx * fx + fy * fy)
                # Показываем номера только для ближних гексов (центр)
                if d < max_flat_r * 0.35:
                    sx, sy, sz = flat_to_sphere(fx, fy, max_flat_r, R)
                    # Немного приподнимаем текст над сферой
                    factor = 1.03
                    ax.text(sx * factor, sy * factor, sz * factor,
                            str(hid), fontsize=3.5, color='white',
                            ha='center', va='center', fontweight='bold',
                            zorder=10)

        # ── Настройки оси ────────────────────────────────────────
        lim = 1.15
        ax.set_xlim([-lim, lim])
        ax.set_ylim([-lim, lim])
        ax.set_zlim([-lim, lim])
        ax.set_box_aspect([1, 1, 1])
        ax.view_init(elev=elev, azim=azim)
        ax.set_axis_off()
        ax.set_title(title, fontsize=13, color='white', pad=5)

    # ── Легенда ──────────────────────────────────────────────────
    state_counts = defaultdict(int)
    for h in hexes:
        state_counts[h.get("state", "")] += 1

    import matplotlib.patches as mpatches

    legend_patches = []
    for state in sorted(STATE_COLORS.keys(), key=lambda s: -state_counts.get(s, 0)):
        count = state_counts.get(state, 0)
        if count == 0:
            continue
        name_ru = STATE_NAMES_RU.get(state, state)
        legend_patches.append(
            mpatches.Patch(facecolor=STATE_COLORS[state],
                           edgecolor='white', linewidth=0.5,
                           label=f"{name_ru}  ({count})")
        )

    fig.legend(
        handles=legend_patches,
        loc='lower center',
        ncol=4,
        fontsize=10,
        framealpha=0.85,
        facecolor='#15152a',
        edgecolor='white',
        labelcolor='white',
        title='Типы территорий',
        title_fontsize=13,
        borderpad=1,
    )

    fig.suptitle('Планета',
                 fontsize=24, fontweight='bold', color='white', y=0.97)

    plt.subplots_adjust(left=0.02, right=0.98, top=0.92, bottom=0.1,
                        wspace=0.05, hspace=0.08)

    plt.savefig(output_path, dpi=180, bbox_inches='tight',
                facecolor='#0a0a1a', edgecolor='none')
    plt.close()
    print(f"✅ Глобус сохранён: {output_path}")
    return output_path


# ── Main ─────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("Загрузка данных с production...")
    alliances = fetch_alliances()
    print(f"  Альянсы: {len(alliances)}")

    hexes = fetch_map()
    print(f"  Гексов: {len(hexes)}")

    edges = fetch_edges()
    print(f"  Рёбер: {len(edges)}")

    print("Рендеринг глобуса (может занять 20-30 секунд)...")
    output = draw_globe(hexes, edges, output_path="planet_globe.png")
