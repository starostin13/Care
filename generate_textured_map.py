# -*- coding: utf-8 -*-
"""
Плоская гексагональная карта с текстурами поверхности.
Каждый гекс заливается цветом state + детали (деревья, здания, варп и т.д.)
Тонкие границы между гексами, номера гексов, легенда.
"""
import subprocess
import math
import numpy as np
import random
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import RegularPolygon, FancyArrowPatch
from matplotlib.colors import to_rgb
from matplotlib.collections import PatchCollection, LineCollection

# ── Цвета территорий ────────────────────────────────────────────
STATE_COLORS = {
    "Forest":               "#4A7A3B",
    "Tundra/Snow":          "#C4B8A8",
    "Desert":               "#C8A054",
    "Poisoned Lands":       "#6B7A42",
    "Factory":              "#7A7060",
    "City":                 "#8A7A6A",
    "Ruined City":          "#7A5A42",
    "Underground Systems":  "#5A4A3A",
    "Ship Wreckage":        "#9A8A7A",
    "Junkyard":             "#8A6A4A",
    "Temple Quarter":       "#B89030",
    "Warp-altered Space":   "#6A3A5A",
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

ALLIANCE_COLORS = {
    4: "#E63946",
    5: "#457B9D",
    6: "#2A9D8F",
    7: "#E9C46A",
    8: "#F4A261",
    9: "#6A4C93",
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


def hex_ring(cq, cr, radius):
    if radius == 0:
        return [(cq, cr)]
    results = []
    q = cq + HEX_DIRECTIONS[4][0] * radius
    r = cr + HEX_DIRECTIONS[4][1] * radius
    for i in range(6):
        for _ in range(radius):
            results.append((q, r))
            dq, dr = HEX_DIRECTIONS[i]
            q += dq
            r += dr
    return results


def hex_to_pixel(q, r, size=1.0):
    x = size * (3 / 2 * q)
    y = size * (math.sqrt(3) / 2 * q + math.sqrt(3) * r)
    return x, y


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


# ── SSH ──────────────────────────────────────────────────────────
SSH_HOST = "ubuntu@192.168.1.125"
CONTAINER = "carebot_production"


def ssh_query(sql):
    cmd = f'ssh {SSH_HOST} "docker exec {CONTAINER} sqlite3 /app/data/game_database.db \\"{sql}\\""'
    result = subprocess.run(cmd, shell=True, capture_output=True, timeout=30)
    if result.returncode != 0:
        raise RuntimeError(result.stderr.decode('utf-8', errors='replace'))
    return result.stdout.decode('utf-8', errors='replace').strip()


def fetch_map():
    raw = ssh_query("SELECT id, patron, has_warehouse, state FROM map ORDER BY id;")
    hexes = []
    for line in raw.splitlines():
        p = line.split("|")
        hexes.append({
            "id": int(p[0]),
            "patron": int(p[1]) if p[1] else None,
            "warehouse": int(p[2]) if p[2] else 0,
            "state": p[3] if len(p) > 3 else None,
        })
    return hexes


def fetch_edges():
    raw = ssh_query("SELECT left_hexagon, right_hexagon FROM edges ORDER BY id;")
    edges = []
    for line in raw.splitlines():
        p = line.split("|")
        edges.append((int(p[0]), int(p[1])))
    return edges


# ── Detail drawing helpers (matplotlib) ──────────────────────────
def _draw_trees(ax, cx, cy, sz, rng):
    """Леса — маленькие треугольники-ёлки."""
    for _ in range(rng.randint(3, 7)):
        dx = rng.uniform(-sz * 0.35, sz * 0.35)
        dy = rng.uniform(-sz * 0.35, sz * 0.35)
        ts = rng.uniform(sz * 0.06, sz * 0.12)
        x, y = cx + dx, cy + dy
        tri = plt.Polygon([(x, y + ts), (x - ts * 0.6, y - ts * 0.3), (x + ts * 0.6, y - ts * 0.3)],
                          color=rng.choice(['#0D3B0D', '#145214', '#1A6B1A', '#0A4A0A']),
                          zorder=3)
        ax.add_patch(tri)
        ax.plot([x, x], [y - ts * 0.3, y - ts * 0.55], color='#4A3520', linewidth=0.5, zorder=2)


def _draw_city(ax, cx, cy, sz, rng):
    """Город — прямоугольники-здания с окнами."""
    for _ in range(rng.randint(3, 6)):
        dx = rng.uniform(-sz * 0.3, sz * 0.3)
        dy = rng.uniform(-sz * 0.3, sz * 0.3)
        bw = rng.uniform(sz * 0.04, sz * 0.08)
        bh = rng.uniform(sz * 0.06, sz * 0.18)
        c = rng.choice(['#4A5568', '#5A6577', '#3D4A5C'])
        rect = plt.Rectangle((cx + dx - bw / 2, cy + dy), bw, bh, color=c, zorder=3)
        ax.add_patch(rect)
        # Окна
        for wy in np.arange(bh * 0.15, bh * 0.85, bh * 0.25):
            for wx in [-bw * 0.2, bw * 0.2]:
                dot = plt.Rectangle((cx + dx + wx - 0.005, cy + dy + wy), 0.01, 0.01,
                                    color='#FFE066', zorder=4)
                ax.add_patch(dot)


def _draw_ruins(ax, cx, cy, sz, rng):
    """Разрушенный город — обломки и трещины."""
    for _ in range(rng.randint(2, 5)):
        dx = rng.uniform(-sz * 0.3, sz * 0.3)
        dy = rng.uniform(-sz * 0.3, sz * 0.3)
        bw = rng.uniform(sz * 0.03, sz * 0.08)
        bh = rng.uniform(sz * 0.04, sz * 0.1)
        c = rng.choice(['#5D4037', '#6D4C41', '#4E3629'])
        rect = plt.Rectangle((cx + dx, cy + dy), bw, bh, color=c, zorder=3)
        ax.add_patch(rect)
    for _ in range(2):
        x0 = cx + rng.uniform(-sz * 0.2, sz * 0.2)
        y0 = cy + rng.uniform(-sz * 0.2, sz * 0.2)
        x1 = x0 + rng.uniform(-sz * 0.15, sz * 0.15)
        y1 = y0 + rng.uniform(-sz * 0.15, sz * 0.15)
        ax.plot([x0, x1], [y0, y1], color='#3E2723', linewidth=0.4, zorder=3)


def _draw_desert(ax, cx, cy, sz, rng):
    """Пустыня — дюны (кривые)."""
    for _ in range(rng.randint(2, 4)):
        dx = rng.uniform(-sz * 0.3, sz * 0.3)
        dy = rng.uniform(-sz * 0.2, sz * 0.2)
        w = rng.uniform(sz * 0.1, sz * 0.25)
        c = rng.choice(['#C49345', '#B8863D', '#DAA96A'])
        arc = matplotlib.patches.Arc((cx + dx, cy + dy), w, w * 0.3, angle=0,
                                     theta1=0, theta2=180, color=c, linewidth=0.8, zorder=3)
        ax.add_patch(arc)


def _draw_warp(ax, cx, cy, sz, rng):
    """Варп — аморфные пятна и спирали."""
    for _ in range(rng.randint(3, 6)):
        dx = rng.uniform(-sz * 0.3, sz * 0.3)
        dy = rng.uniform(-sz * 0.3, sz * 0.3)
        rs = rng.uniform(sz * 0.03, sz * 0.08)
        c = rng.choice(['#AB47BC', '#CE93D8', '#8E24AA', '#BA68C8'])
        circle = plt.Circle((cx + dx, cy + dy), rs, color=c, alpha=0.7, zorder=3)
        ax.add_patch(circle)
    # Спираль
    ang0 = rng.uniform(0, 2 * math.pi)
    pts_x, pts_y = [], []
    for t in range(15):
        a = ang0 + t * 0.45
        r = sz * 0.015 * t
        pts_x.append(cx + r * math.cos(a))
        pts_y.append(cy + r * math.sin(a))
    ax.plot(pts_x, pts_y, color='#CE93D8', linewidth=0.5, alpha=0.6, zorder=3)


def _draw_factory(ax, cx, cy, sz, rng):
    """Завод — коробки и трубы с дымом."""
    for _ in range(rng.randint(2, 4)):
        dx = rng.uniform(-sz * 0.25, sz * 0.25)
        dy = rng.uniform(-sz * 0.25, sz * 0.25)
        bw = rng.uniform(sz * 0.04, sz * 0.08)
        bh = rng.uniform(sz * 0.05, sz * 0.1)
        c = rng.choice(['#555555', '#666666', '#4A4A4A'])
        rect = plt.Rectangle((cx + dx, cy + dy), bw, bh, color=c, zorder=3)
        ax.add_patch(rect)
    # Труба
    tx = cx + rng.uniform(-sz * 0.1, sz * 0.1)
    ty = cy + rng.uniform(-sz * 0.05, sz * 0.15)
    ax.plot([tx, tx], [ty, ty + sz * 0.15], color='#777777', linewidth=1.2, zorder=3)
    for i in range(3):
        smoke = plt.Circle((tx + i * 0.015, ty + sz * 0.15 + i * 0.03),
                           sz * 0.015 + i * 0.01, color='#9E9E9E', alpha=0.4, zorder=3)
        ax.add_patch(smoke)


def _draw_snow(ax, cx, cy, sz, rng):
    """Тундра — снежинки-точки."""
    for _ in range(rng.randint(5, 12)):
        dx = rng.uniform(-sz * 0.35, sz * 0.35)
        dy = rng.uniform(-sz * 0.35, sz * 0.35)
        rs = rng.uniform(sz * 0.008, sz * 0.02)
        c = rng.choice(['#E8EAF6', '#F5F5F5', '#ECEFF1'])
        dot = plt.Circle((cx + dx, cy + dy), rs, color=c, zorder=3)
        ax.add_patch(dot)


def _draw_wreckage(ax, cx, cy, sz, rng):
    """Останки корабля — угловатые обломки."""
    for _ in range(rng.randint(2, 4)):
        n = rng.randint(3, 5)
        dx = rng.uniform(-sz * 0.2, sz * 0.2)
        dy = rng.uniform(-sz * 0.2, sz * 0.2)
        pts = [(cx + dx + rng.uniform(-sz * 0.06, sz * 0.06),
                cy + dy + rng.uniform(-sz * 0.06, sz * 0.06)) for _ in range(n)]
        c = rng.choice(['#78909C', '#90A4AE', '#607D8B'])
        poly = plt.Polygon(pts, color=c, zorder=3)
        ax.add_patch(poly)


def _draw_junkyard(ax, cx, cy, sz, rng):
    """Свалка — мелкие цветные пятна."""
    for _ in range(rng.randint(6, 14)):
        dx = rng.uniform(-sz * 0.35, sz * 0.35)
        dy = rng.uniform(-sz * 0.35, sz * 0.35)
        rs = rng.uniform(sz * 0.008, sz * 0.025)
        c = rng.choice(['#8D6E63', '#6D4C41', '#795548', '#A1887F'])
        dot = plt.Circle((cx + dx, cy + dy), rs, color=c, zorder=3)
        ax.add_patch(dot)


def _draw_temple(ax, cx, cy, sz, rng):
    """Храмовый квартал — шпили и купола."""
    for _ in range(rng.randint(1, 3)):
        dx = rng.uniform(-sz * 0.2, sz * 0.2)
        dy = rng.uniform(-sz * 0.15, sz * 0.15)
        bw = sz * 0.04
        bh = sz * 0.08
        # Здание
        rect = plt.Rectangle((cx + dx - bw / 2, cy + dy - bh / 2), bw, bh,
                              color='#B8860B', zorder=3)
        ax.add_patch(rect)
        # Купол
        dome = plt.Circle((cx + dx, cy + dy + bh / 2), bw * 0.6,
                           color='#DAA520', zorder=4)
        ax.add_patch(dome)
        # Шпиль
        spire = plt.Polygon([(cx + dx, cy + dy + bh / 2 + bw * 1.2),
                              (cx + dx - bw * 0.15, cy + dy + bh / 2 + bw * 0.3),
                              (cx + dx + bw * 0.15, cy + dy + bh / 2 + bw * 0.3)],
                             color='#FFD700', zorder=5)
        ax.add_patch(spire)


def _draw_poison(ax, cx, cy, sz, rng):
    """Отравленные земли — ядовитые лужи."""
    for _ in range(rng.randint(3, 6)):
        dx = rng.uniform(-sz * 0.3, sz * 0.3)
        dy = rng.uniform(-sz * 0.3, sz * 0.3)
        rx = rng.uniform(sz * 0.02, sz * 0.06)
        ry = rng.uniform(sz * 0.015, sz * 0.04)
        c = rng.choice(['#689F38', '#558B2F', '#7CB342'])
        ell = matplotlib.patches.Ellipse((cx + dx, cy + dy), rx * 2, ry * 2,
                                         color=c, alpha=0.7, zorder=3)
        ax.add_patch(ell)


def _draw_underground(ax, cx, cy, sz, rng):
    """Подземные системы — входы в тоннели."""
    for _ in range(rng.randint(1, 3)):
        dx = rng.uniform(-sz * 0.2, sz * 0.2)
        dy = rng.uniform(-sz * 0.2, sz * 0.2)
        rs = rng.uniform(sz * 0.03, sz * 0.06)
        outer = plt.Circle((cx + dx, cy + dy), rs, color='#37474F', zorder=3)
        ax.add_patch(outer)
        inner = plt.Circle((cx + dx, cy + dy), rs * 0.5, color='#1A1F25', zorder=4)
        ax.add_patch(inner)


DETAIL_DRAWERS = {
    "Forest": _draw_trees,
    "City": _draw_city,
    "Ruined City": _draw_ruins,
    "Desert": _draw_desert,
    "Warp-altered Space": _draw_warp,
    "Factory": _draw_factory,
    "Tundra/Snow": _draw_snow,
    "Ship Wreckage": _draw_wreckage,
    "Junkyard": _draw_junkyard,
    "Temple Quarter": _draw_temple,
    "Poisoned Lands": _draw_poison,
    "Underground Systems": _draw_underground,
}


# ── Helpers ──────────────────────────────────────────────────────
def _setup_ax(ax):
    ax.set_aspect('equal')
    ax.autoscale_view()
    m = 2
    xl = ax.get_xlim()
    yl = ax.get_ylim()
    ax.set_xlim(xl[0] - m, xl[1] + m)
    ax.set_ylim(yl[0] - m, yl[1] + m)
    ax.set_xticks([])
    ax.set_yticks([])
    for spine in ax.spines.values():
        spine.set_visible(False)


def _compute_positions(hexes):
    coords = reconstruct_coordinates(len(hexes))
    hex_size = 1.0
    id_to_px = {}
    for h in hexes:
        hid = h["id"]
        if hid in coords:
            q, r = coords[hid]
            px, py = hex_to_pixel(q, r, hex_size)
            id_to_px[hid] = (px, py)
    return id_to_px, hex_size


# ── Карта 1: Альянсы + легенда, без текстур ─────────────────────
def draw_alliance_map(hexes, edges, output_path="planet_alliances.png"):
    id_to_px, hex_size = _compute_positions(hexes)
    from collections import defaultdict

    fig, ax = plt.subplots(1, 1, figsize=(32, 32), facecolor='#0d0d1a')
    ax.set_facecolor('#0d0d1a')

    for h in hexes:
        hid = h["id"]
        patron = h.get("patron")
        warehouse = h.get("warehouse", 0)
        if hid not in id_to_px:
            continue
        px, py = id_to_px[hid]

        color = ALLIANCE_COLORS.get(patron, "#555555")

        hex_patch = RegularPolygon(
            (px, py), numVertices=6, radius=hex_size * 0.95,
            orientation=np.radians(30),
            facecolor=color, edgecolor='#0d0d1a', linewidth=0.5,
            alpha=0.85, zorder=1
        )
        ax.add_patch(hex_patch)

        # Номер гекса
        ax.text(px, py + 0.05, str(hid), ha='center', va='center',
                fontsize=3.2, color='white', fontweight='bold', zorder=3)

        # Склад
        if warehouse:
            ax.plot(px, py - hex_size * 0.28, marker='s', color='#FFD700',
                    markersize=2.5, markeredgecolor='white', markeredgewidth=0.3, zorder=4)

    _setup_ax(ax)
    ax.set_title('Карта Планеты — Территории Альянсов', fontsize=24,
                 fontweight='bold', color='white', pad=20)

    # Легенда альянсов
    patron_counts = defaultdict(int)
    for h in hexes:
        patron_counts[h.get("patron")] += 1

    legend_patches = []
    for aid in sorted(ALLIANCE_COLORS.keys()):
        count = patron_counts.get(aid, 0)
        name = ALLIANCE_NAMES.get(aid, f"#{aid}")
        legend_patches.append(
            mpatches.Patch(facecolor=ALLIANCE_COLORS[aid], edgecolor='white',
                           linewidth=0.5, label=f"{name} ({count} гексов)")
        )

    leg = ax.legend(handles=legend_patches, loc='upper left', bbox_to_anchor=(0.0, 1.0),
                    fontsize=10, framealpha=0.8, facecolor='#1a1a2e', edgecolor='white',
                    labelcolor='white', title='Альянсы', title_fontsize=12)
    leg.get_title().set_color('white')

    plt.tight_layout()
    plt.savefig(output_path, dpi=200, bbox_inches='tight',
                facecolor='#0d0d1a', edgecolor='none')
    plt.close()
    print(f"✅ Карта альянсов: {output_path}")


# ── Карта 2: Текстуры поверхности, без альянсов и границ ────────
def _render_gradient_base(hexes, id_to_px, hex_size, img_size=6000):
    """Рендерит растровую базу с плавным градиентом между гексами (IDW)."""
    from scipy.spatial import cKDTree

    # Рабочие координаты
    positions = []
    colors = []
    rng = random.Random(42)
    for h in hexes:
        hid = h["id"]
        state = h.get("state", "")
        if hid not in id_to_px:
            continue
        px, py = id_to_px[hid]
        positions.append((px, py))
        base = STATE_COLORS.get(state, "#444444")
        br, bg, bb = to_rgb(base)
        vr = max(0.0, min(1.0, br + rng.uniform(-0.03, 0.03)))
        vg = max(0.0, min(1.0, bg + rng.uniform(-0.03, 0.03)))
        vb = max(0.0, min(1.0, bb + rng.uniform(-0.03, 0.03)))
        colors.append((vr, vg, vb))

    positions = np.array(positions)
    colors = np.array(colors)

    # Bounding box
    xmin, xmax = positions[:, 0].min() - 1.5, positions[:, 0].max() + 1.5
    ymin, ymax = positions[:, 1].min() - 1.5, positions[:, 1].max() + 1.5

    # Пиксельная сетка
    aspect = (xmax - xmin) / (ymax - ymin)
    if aspect > 1:
        w = img_size
        h = int(img_size / aspect)
    else:
        h = img_size
        w = int(img_size * aspect)

    xs = np.linspace(xmin, xmax, w)
    ys = np.linspace(ymin, ymax, h)
    grid_x, grid_y = np.meshgrid(xs, ys)
    grid_pts = np.column_stack([grid_x.ravel(), grid_y.ravel()])

    # KD-tree: для каждого пикселя находим 3 ближайших гекса
    tree = cKDTree(positions)
    dists, idxs = tree.query(grid_pts, k=6)

    # IDW интерполяция: мягкий градиент на границах
    power = 2.0
    weights = 1.0 / (dists ** power + 1e-10)
    weights_sum = weights.sum(axis=1, keepdims=True)
    weights /= weights_sum

    # Смешиваем цвета
    pixel_colors = np.zeros((len(grid_pts), 3))
    for ki in range(6):
        w_k = weights[:, ki:ki+1]
        c_k = colors[idxs[:, ki]]
        pixel_colors += w_k * c_k

    pixel_colors = np.clip(pixel_colors, 0, 1)
    img_arr = pixel_colors.reshape(h, w, 3)

    # Gaussian blur для сглаживания артефактов IDW
    from scipy.ndimage import gaussian_filter
    for ch in range(3):
        img_arr[:, :, ch] = gaussian_filter(img_arr[:, :, ch], sigma=3.0)

    # За пределами карты — тёплый тёмный фон
    bg_color = np.array([0.12, 0.08, 0.05])  # тёплый тёмно-коричневый
    # Маска: пиксели дальше 1.2 от ближайшего гекса → фон
    far_mask = dists[:, 0] > 1.2
    img_arr_flat = img_arr.reshape(-1, 3)
    img_arr_flat[far_mask] = bg_color
    img_arr = img_arr_flat.reshape(h, w, 3)

    return img_arr, (xmin, xmax, ymin, ymax)


def draw_terrain_map(hexes, edges, output_path="planet_terrain.png"):
    id_to_px, hex_size = _compute_positions(hexes)
    from collections import defaultdict

    print("  Рендеринг градиентной базы (IDW)...")
    img_arr, (xmin, xmax, ymin, ymax) = _render_gradient_base(hexes, id_to_px, hex_size)

    fig, ax = plt.subplots(1, 1, figsize=(32, 32), facecolor='#1F1408')
    ax.set_facecolor('#1F1408')

    # Рисуем растровую базу
    ax.imshow(img_arr, extent=[xmin, xmax, ymin, ymax], origin='lower',
              aspect='equal', interpolation='bilinear', zorder=0)

    # Детали поверхности поверх
    rng = random.Random(42)
    # Прокручиваем rng чтобы совпадал с seed из _render_gradient_base
    rng2 = random.Random(42)
    for h in hexes:
        # Пропускаем rng.uniform вызовы чтобы синхронизировать
        _ = rng2.uniform(-0.03, 0.03)
        _ = rng2.uniform(-0.03, 0.03)
        _ = rng2.uniform(-0.03, 0.03)

    rng = random.Random(123)  # Отдельный seed для деталей

    for h in hexes:
        hid = h["id"]
        state = h.get("state", "")
        warehouse = h.get("warehouse", 0)
        if hid not in id_to_px:
            continue
        px, py = id_to_px[hid]

        # Детали поверхности
        drawer = DETAIL_DRAWERS.get(state)
        if drawer:
            drawer(ax, px, py, hex_size, rng)

        # Номер гекса
        ax.text(px, py - hex_size * 0.35, str(hid), ha='center', va='center',
                fontsize=2.8, color='white', fontweight='bold', alpha=0.8, zorder=6)

        # Склад
        if warehouse:
            ax.plot(px, py + hex_size * 0.25, marker='s', color='#FFD700',
                    markersize=2.5, markeredgecolor='white', markeredgewidth=0.3, zorder=7)

    _setup_ax(ax)
    ax.set_title('Карта Планеты — Поверхность', fontsize=24,
                 fontweight='bold', color='white', pad=20)

    # Легенда типов территорий
    state_counts = defaultdict(int)
    for h in hexes:
        state_counts[h.get("state", "")] += 1

    terrain_patches = []
    for state in sorted(STATE_COLORS.keys(), key=lambda s: -state_counts.get(s, 0)):
        count = state_counts.get(state, 0)
        if count == 0:
            continue
        name_ru = STATE_NAMES_RU.get(state, state)
        terrain_patches.append(
            mpatches.Patch(facecolor=STATE_COLORS[state], edgecolor='white',
                           linewidth=0.5, label=f"{name_ru} ({count})")
        )

    leg = ax.legend(handles=terrain_patches, loc='upper left', bbox_to_anchor=(0.0, 1.0),
                    fontsize=8, framealpha=0.8, facecolor='#2A1A0A', edgecolor='#8A7A6A',
                    labelcolor='white', title='Типы территорий', title_fontsize=10,
                    ncol=2)
    leg.get_title().set_color('white')

    plt.tight_layout()
    plt.savefig(output_path, dpi=200, bbox_inches='tight',
                facecolor='#1F1408', edgecolor='none')
    plt.close()
    print(f"✅ Карта поверхности: {output_path}")


# ── Main ─────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("Загрузка данных с production...")
    hexes = fetch_map()
    print(f"  Гексов: {len(hexes)}")
    edges = fetch_edges()
    print(f"  Рёбер: {len(edges)}")

    print("\nРендеринг карты альянсов...")
    draw_alliance_map(hexes, edges, output_path="planet_alliances.png")

    print("\nРендеринг карты поверхности...")
    draw_terrain_map(hexes, edges, output_path="planet_terrain.png")
