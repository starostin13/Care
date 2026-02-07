# -*- coding: utf-8 -*-
"""
Визуализация гексагональной карты как полусферы планеты.
1. Рисуем плоскую текстуру с деталями (деревья, здания, варп-спирали и т.д.)
2. Натягиваем на полусферу через азимутальную проекцию.
"""
import subprocess
import math
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import to_rgb
from PIL import Image, ImageDraw, ImageFont
import random
import io

# ── Цвета территорий ────────────────────────────────────────────
STATE_COLORS = {
    "Forest":               "#1B5E20",
    "Tundra/Snow":          "#CFD8DC",
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


# ── SSH helpers ──────────────────────────────────────────────────
SSH_HOST = "ubuntu@192.168.1.125"
CONTAINER = "carebot_production"


def ssh_query(sql):
    cmd = f'ssh {SSH_HOST} "docker exec {CONTAINER} sqlite3 /app/data/game_database.db \\"{sql}\\""'
    result = subprocess.run(cmd, shell=True, capture_output=True, timeout=30)
    if result.returncode != 0:
        raise RuntimeError(f"SSH failed: {result.stderr.decode('utf-8', errors='replace')}")
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


# ── Flat texture with terrain details ────────────────────────────

def _hex_color(state):
    """Возвращает RGB tuple 0-255 для state."""
    c = STATE_COLORS.get(state, "#444444")
    r, g, b = to_rgb(c)
    return (int(r * 255), int(g * 255), int(b * 255))


def _vary_color(rgb, amount=18):
    """Слегка варьирует цвет для естественности."""
    return tuple(max(0, min(255, c + random.randint(-amount, amount))) for c in rgb)


def _draw_hex_polygon(draw, cx, cy, size, color):
    """Рисует один заполненный гексагон на PIL Image."""
    pts = []
    for i in range(6):
        angle = math.radians(60 * i + 30)
        pts.append((cx + size * math.cos(angle), cy + size * math.sin(angle)))
    draw.polygon(pts, fill=color, outline=None)


def _draw_detail(draw, cx, cy, size, state, rng):
    """Рисует мелкие детали внутри гекса в зависимости от state."""
    s = size * 0.3

    if state == "Forest":
        # Деревья — маленькие треугольники
        for _ in range(rng.randint(3, 6)):
            dx = rng.uniform(-s * 1.5, s * 1.5)
            dy = rng.uniform(-s * 1.5, s * 1.5)
            ts = rng.uniform(s * 0.3, s * 0.7)
            x, y = cx + dx, cy + dy
            tri = [(x, y - ts), (x - ts * 0.6, y + ts * 0.4), (x + ts * 0.6, y + ts * 0.4)]
            c = rng.choice([(20, 80, 20), (10, 100, 30), (30, 120, 15), (15, 70, 10)])
            draw.polygon(tri, fill=c)
            # Ствол
            draw.rectangle([x - 1, y + ts * 0.3, x + 1, y + ts * 0.7], fill=(80, 50, 20))

    elif state == "City":
        # Здания — прямоугольники
        for _ in range(rng.randint(3, 6)):
            dx = rng.uniform(-s * 1.2, s * 1.2)
            dy = rng.uniform(-s * 1.2, s * 1.2)
            bw = rng.uniform(s * 0.2, s * 0.5)
            bh = rng.uniform(s * 0.3, s * 0.8)
            c = rng.choice([(80, 90, 110), (100, 105, 120), (60, 70, 85)])
            draw.rectangle([cx + dx - bw, cy + dy - bh, cx + dx + bw, cy + dy], fill=c)
            # Окна
            for wy in range(int(bh / 3)):
                wx = cx + dx - bw * 0.5
                draw.rectangle([wx, cy + dy - bh + wy * 3, wx + 1.5, cy + dy - bh + wy * 3 + 1],
                               fill=(255, 230, 100))

    elif state == "Ruined City":
        # Обломки зданий — неровные прямоугольники
        for _ in range(rng.randint(2, 5)):
            dx = rng.uniform(-s * 1.2, s * 1.2)
            dy = rng.uniform(-s * 1.2, s * 1.2)
            bw = rng.uniform(s * 0.15, s * 0.4)
            bh = rng.uniform(s * 0.2, s * 0.5)
            c = rng.choice([(90, 60, 40), (100, 70, 50), (80, 55, 35)])
            draw.rectangle([cx + dx, cy + dy, cx + dx + bw, cy + dy + bh], fill=c)
        # Трещины
        for _ in range(2):
            x0 = cx + rng.uniform(-s, s)
            y0 = cy + rng.uniform(-s, s)
            x1 = x0 + rng.uniform(-s * 0.8, s * 0.8)
            y1 = y0 + rng.uniform(-s * 0.8, s * 0.8)
            draw.line([(x0, y0), (x1, y1)], fill=(50, 30, 20), width=1)

    elif state == "Desert":
        # Дюны — кривые линии и точки
        for _ in range(rng.randint(2, 4)):
            dx = rng.uniform(-s * 1.5, s * 1.5)
            dy = rng.uniform(-s, s)
            c = rng.choice([(200, 170, 90), (180, 150, 75), (220, 185, 100)])
            draw.arc([cx + dx - s * 0.5, cy + dy - s * 0.2,
                      cx + dx + s * 0.5, cy + dy + s * 0.2],
                     start=0, end=180, fill=c, width=1)

    elif state == "Warp-altered Space":
        # Варп — спирали и аморфные пятна
        for _ in range(rng.randint(3, 7)):
            dx = rng.uniform(-s * 1.3, s * 1.3)
            dy = rng.uniform(-s * 1.3, s * 1.3)
            rs = rng.uniform(s * 0.15, s * 0.4)
            c = rng.choice([(160, 30, 200), (200, 50, 255), (130, 0, 180), (180, 80, 220)])
            draw.ellipse([cx + dx - rs, cy + dy - rs, cx + dx + rs, cy + dy + rs],
                         fill=c, outline=None)
        # Тонкие спиральные линии
        for _ in range(2):
            pts = []
            ang0 = rng.uniform(0, 2 * math.pi)
            for t in range(12):
                a = ang0 + t * 0.5
                r = s * 0.15 * t
                pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
            if len(pts) > 1:
                draw.line(pts, fill=(200, 100, 255), width=1)

    elif state == "Factory":
        # Трубы и коробки
        for _ in range(rng.randint(2, 4)):
            dx = rng.uniform(-s, s)
            dy = rng.uniform(-s, s)
            c = rng.choice([(80, 80, 80), (100, 100, 100), (70, 70, 75)])
            bw = rng.uniform(s * 0.2, s * 0.4)
            bh = rng.uniform(s * 0.3, s * 0.6)
            draw.rectangle([cx + dx, cy + dy, cx + dx + bw, cy + dy + bh], fill=c)
        # Трубы / дымовые столбы
        for _ in range(rng.randint(1, 3)):
            dx = rng.uniform(-s * 0.5, s * 0.5)
            dy = rng.uniform(-s, 0)
            draw.rectangle([cx + dx, cy + dy - s * 0.6, cx + dx + 2, cy + dy], fill=(90, 90, 95))
            # Дым
            for dd in range(3):
                draw.ellipse([cx + dx - dd * 2, cy + dy - s * 0.6 - dd * 3 - 3,
                              cx + dx + dd * 2 + 3, cy + dy - s * 0.6 - dd * 3],
                             fill=(140, 140, 140, 120))

    elif state == "Tundra/Snow":
        # Снежинки / точки
        for _ in range(rng.randint(5, 12)):
            dx = rng.uniform(-s * 1.5, s * 1.5)
            dy = rng.uniform(-s * 1.5, s * 1.5)
            rs = rng.uniform(0.5, 2)
            c = rng.choice([(240, 245, 255), (220, 230, 245), (255, 255, 255)])
            draw.ellipse([cx + dx - rs, cy + dy - rs, cx + dx + rs, cy + dy + rs], fill=c)

    elif state == "Ship Wreckage":
        # Обломки — угловатые фигуры
        for _ in range(rng.randint(2, 4)):
            dx = rng.uniform(-s, s)
            dy = rng.uniform(-s, s)
            pts = []
            for _ in range(rng.randint(3, 5)):
                pts.append((cx + dx + rng.uniform(-s * 0.3, s * 0.3),
                            cy + dy + rng.uniform(-s * 0.3, s * 0.3)))
            c = rng.choice([(130, 135, 140), (150, 155, 165), (110, 115, 120)])
            if len(pts) >= 3:
                draw.polygon(pts, fill=c)

    elif state == "Junkyard":
        # Куча мусора — мелкие разноцветные точки и палки
        for _ in range(rng.randint(6, 15)):
            dx = rng.uniform(-s * 1.3, s * 1.3)
            dy = rng.uniform(-s * 1.3, s * 1.3)
            rs = rng.uniform(0.5, 2.5)
            c = rng.choice([(140, 110, 80), (100, 80, 60), (120, 100, 70), (90, 70, 50)])
            draw.ellipse([cx + dx - rs, cy + dy - rs, cx + dx + rs, cy + dy + rs], fill=c)

    elif state == "Temple Quarter":
        # Храмы — шпили / купола
        for _ in range(rng.randint(1, 3)):
            dx = rng.uniform(-s * 0.8, s * 0.8)
            dy = rng.uniform(-s * 0.5, s * 0.5)
            bw = rng.uniform(s * 0.2, s * 0.4)
            draw.rectangle([cx + dx - bw, cy + dy, cx + dx + bw, cy + dy + s * 0.5],
                           fill=(170, 140, 40))
            # Купол
            draw.ellipse([cx + dx - bw * 0.7, cy + dy - bw * 0.5,
                          cx + dx + bw * 0.7, cy + dy + bw * 0.2],
                         fill=(200, 170, 50))
            # Шпиль
            tri = [(cx + dx, cy + dy - bw), (cx + dx - 2, cy + dy), (cx + dx + 2, cy + dy)]
            draw.polygon(tri, fill=(220, 190, 60))

    elif state == "Poisoned Lands":
        # Ядовитые лужи / пузыри
        for _ in range(rng.randint(3, 6)):
            dx = rng.uniform(-s * 1.3, s * 1.3)
            dy = rng.uniform(-s * 1.3, s * 1.3)
            rs = rng.uniform(s * 0.1, s * 0.35)
            c = rng.choice([(100, 140, 50), (80, 120, 40), (120, 150, 60)])
            draw.ellipse([cx + dx - rs, cy + dy - rs, cx + dx + rs, cy + dy + rs], fill=c)

    elif state == "Underground Systems":
        # Входы в тоннели — кружки с тёмным центром
        for _ in range(rng.randint(1, 3)):
            dx = rng.uniform(-s * 0.8, s * 0.8)
            dy = rng.uniform(-s * 0.8, s * 0.8)
            rs = rng.uniform(s * 0.15, s * 0.3)
            draw.ellipse([cx + dx - rs, cy + dy - rs, cx + dx + rs, cy + dy + rs],
                         fill=(45, 55, 65), outline=(70, 80, 90))
            draw.ellipse([cx + dx - rs * 0.5, cy + dy - rs * 0.5,
                          cx + dx + rs * 0.5, cy + dy + rs * 0.5],
                         fill=(20, 25, 30))


def render_flat_texture(hexes, tex_size=4096):
    """Render the hex map as a circular PIL image."""
    coords = reconstruct_coordinates(len(hexes))

    # Вычисляем пиксельные позиции и масштаб
    positions = {}
    max_d = 0
    for h in hexes:
        hid = h["id"]
        if hid in coords:
            q, r = coords[hid]
            fx, fy = hex_to_pixel(q, r)
            positions[hid] = (fx, fy)
            d = math.sqrt(fx * fx + fy * fy)
            if d > max_d:
                max_d = d

    hex_pixel_size = 1.0  # логический размер гекса
    pad = hex_pixel_size * 1.5
    world_radius = max_d + pad

    # Масштаб: world → image pixels
    margin = 80
    usable = tex_size - 2 * margin
    scale = usable / (2 * world_radius)

    def w2p(fx, fy):
        """World coord → image pixel."""
        px = margin + (fx + world_radius) * scale
        py = margin + (fy + world_radius) * scale  # fy → вниз
        return px, py

    img = Image.new("RGB", (tex_size, tex_size), (10, 10, 26))
    draw = ImageDraw.Draw(img)

    # Рисуем фоновый круг (океан / пустота)
    center = tex_size / 2
    cr = usable / 2
    draw.ellipse([center - cr, center - cr, center + cr, center + cr],
                 fill=(15, 15, 30))

    rng = random.Random(42)  # фиксированный seed для воспроизводимости

    # Рисуем гексагоны
    hex_px_size = hex_pixel_size * scale

    for h in hexes:
        hid = h["id"]
        state = h.get("state", "")
        if hid not in positions:
            continue

        fx, fy = positions[hid]
        cx, cy = w2p(fx, fy)

        base_color = _hex_color(state)
        fill_color = _vary_color(base_color, 12)

        _draw_hex_polygon(draw, cx, cy, hex_px_size * 1.04, fill_color)

    # Второй проход — детали поверх
    for h in hexes:
        hid = h["id"]
        state = h.get("state", "")
        if hid not in positions:
            continue
        fx, fy = positions[hid]
        cx, cy = w2p(fx, fy)
        _draw_detail(draw, cx, cy, hex_px_size, state, rng)

    # Заливаем оставшиеся тёмные щели размытой версией
    from PIL import ImageFilter
    arr = np.array(img)
    bg_color = np.array([10, 10, 26])
    # Маска тёмных пикселей (щели между гексами внутри круга)
    dark_mask = np.all(np.abs(arr.astype(int) - bg_color.astype(int)) < 20, axis=2)
    # Создаём размытую копию
    blurred = img.filter(ImageFilter.GaussianBlur(radius=6))
    blurred_arr = np.array(blurred)
    # Подставляем размытые пиксели вместо тёмных щелей
    arr[dark_mask] = blurred_arr[dark_mask]
    img = Image.fromarray(arr)

    # Мягкая круговая маска (fade-to-black по краям)
    mask = Image.new("L", (tex_size, tex_size), 0)
    mask_draw = ImageDraw.Draw(mask)
    mask_draw.ellipse([center - cr, center - cr, center + cr, center + cr], fill=255)
    # Применяем маску
    bg_img = Image.new("RGB", (tex_size, tex_size), (10, 10, 26))
    img = Image.composite(img, bg_img, mask)

    return img, world_radius, positions


# ── Hemisphere rendering ─────────────────────────────────────────
def render_hemisphere(flat_img, output_path="planet_hemisphere.png"):
    """Натягиваем плоскую текстуру на полусферу."""
    tex = np.array(flat_img)
    tex_h, tex_w = tex.shape[:2]
    center = tex_w / 2

    R = 1.0  # радиус сферы

    # Mesh полусферы
    n_phi = 200    # разрешение по долготе
    n_theta = 100  # разрешение по широте (от полюса до экватора)

    phi = np.linspace(0, 2 * np.pi, n_phi)
    theta = np.linspace(0, np.pi / 2, n_theta)  # полусфера — от полюса до экватора

    Phi, Theta = np.meshgrid(phi, theta)

    X = R * np.sin(Theta) * np.cos(Phi)
    Y = R * np.sin(Theta) * np.sin(Phi)
    Z = R * np.cos(Theta)

    # Для каждой точки поверхности → координата на текстуре
    # Азимутальная проекция: θ=0 (полюс) → центр текстуры, θ=π/2 (экватор) → край
    facecolors = np.zeros((n_theta, n_phi, 3), dtype=float)

    max_r = center * 0.95  # радиус текстуры в пикселях

    for i in range(n_theta):
        for j in range(n_phi):
            th = Theta[i, j]
            ph = Phi[i, j]
            # Расстояние от центра на текстуре пропорционально θ
            r_tex = (th / (np.pi / 2)) * max_r
            tx = int(center + r_tex * np.cos(ph))
            ty = int(center + r_tex * np.sin(ph))
            tx = np.clip(tx, 0, tex_w - 1)
            ty = np.clip(ty, 0, tex_h - 1)
            facecolors[i, j] = tex[ty, tx, :3] / 255.0

    # Простое освещение (Ламбертово) для объёма
    light_dir = np.array([0.4, 0.5, 0.8])
    light_dir = light_dir / np.linalg.norm(light_dir)

    normals_x = np.sin(Theta) * np.cos(Phi)
    normals_y = np.sin(Theta) * np.sin(Phi)
    normals_z = np.cos(Theta)

    dot = normals_x * light_dir[0] + normals_y * light_dir[1] + normals_z * light_dir[2]
    shade = np.clip(dot * 0.5 + 0.6, 0.3, 1.0)  # ambient + diffuse

    for c in range(3):
        facecolors[:, :, c] *= shade

    facecolors = np.clip(facecolors, 0, 1)

    # Рисуем
    fig = plt.figure(figsize=(20, 20), facecolor='#0a0a1a')

    views = [
        (25, 45,  "Вид 1"),
        (25, 165, "Вид 2"),
        (25, 285, "Вид 3"),
        (80, 0,   "Вид сверху"),
    ]

    for idx, (elev, azim, title) in enumerate(views):
        ax = fig.add_subplot(2, 2, idx + 1, projection='3d', facecolor='#0a0a1a')

        # facecolors для plot_surface: shape (n_theta-1, n_phi-1, 3) → cell centers
        fc = np.zeros((n_theta - 1, n_phi - 1, 3))
        for i in range(n_theta - 1):
            for j in range(n_phi - 1):
                fc[i, j] = (facecolors[i, j] + facecolors[i + 1, j] +
                            facecolors[i, j + 1] + facecolors[i + 1, j + 1]) / 4.0

        ax.plot_surface(X, Y, Z, facecolors=fc,
                        rstride=1, cstride=1,
                        antialiased=True, shade=False,
                        linewidth=0, edgecolor='none')

        # Атмосферный ореол (полупрозрачный эллипс на «экваторе»)
        glow_th = np.linspace(0, 2 * np.pi, 100)
        glow_r = R * 1.04
        gx = glow_r * np.cos(glow_th)
        gy = glow_r * np.sin(glow_th)
        gz = np.zeros_like(glow_th)
        ax.plot(gx, gy, gz, color=(0.3, 0.5, 0.8, 0.25), linewidth=3)

        lim = 1.15
        ax.set_xlim([-lim, lim])
        ax.set_ylim([-lim, lim])
        ax.set_zlim([-0.15, lim])
        ax.set_box_aspect([1, 1, 0.55])
        ax.view_init(elev=elev, azim=azim)
        ax.set_axis_off()
        ax.set_title(title, fontsize=13, color='white', pad=5)

    # Легенда
    import matplotlib.patches as mpatches
    legend_patches = []
    for state in sorted(STATE_COLORS.keys()):
        name_ru = STATE_NAMES_RU.get(state, state)
        legend_patches.append(
            mpatches.Patch(facecolor=STATE_COLORS[state],
                           edgecolor='white', linewidth=0.5,
                           label=name_ru)
        )

    fig.legend(
        handles=legend_patches, loc='lower center', ncol=4,
        fontsize=10, framealpha=0.85, facecolor='#15152a',
        edgecolor='white', labelcolor='white',
        title='Типы территорий', title_fontsize=12, borderpad=1,
    )

    fig.suptitle('Планета — вид полусферы',
                 fontsize=22, fontweight='bold', color='white', y=0.97)

    plt.subplots_adjust(left=0.02, right=0.98, top=0.92, bottom=0.1,
                        wspace=0.05, hspace=0.08)

    plt.savefig(output_path, dpi=180, bbox_inches='tight',
                facecolor='#0a0a1a', edgecolor='none')
    plt.close()
    print(f"✅ Полусфера сохранена: {output_path}")

    return output_path


# ── Main ─────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("Загрузка данных с production...")
    hexes = fetch_map()
    print(f"  Гексов: {len(hexes)}")

    print("Рендеринг плоской текстуры...")
    flat_img, world_radius, positions = render_flat_texture(hexes, tex_size=4096)
    flat_img.save("planet_flat_texture.png")
    print("  Текстура: planet_flat_texture.png")

    print("Натягиваем на полусферу (30–60 секунд)...")
    render_hemisphere(flat_img, output_path="planet_hemisphere.png")
