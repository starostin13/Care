#!/usr/bin/env python3
"""Quick standalone test: generates a sample planet map PNG and opens it."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "CareBot", "CareBot"))

from map_exporter import render_realistic_map_png

# ---- Mock data ----
TERRAINS = [
    "Леса", "Тундра/снег", "Пустыня", "Отравленные земли",
    "Завод", "Город", "Разрушенный город", "Подземные системы",
    "Останки корабля", "Свалка", "Храмовый квартал",
    "Изменённое варпом пространство",
]

# 37 hexes: ring 0 (1) + ring 1 (6) + ring 2 (12) + ring 3 (18)
map_cells = []
alliances = [
    (1, "Космические Волки",  "#1565C0"),
    (2, "Дети Императора",   "#B71C1C"),
    (3, "Железные Руки",     "#37474F"),
    (4, "Саламандры",        "#2E7D32"),
]

PATRON_MAP = {
    # ring 0 (hex 1) — neutral
    1: 0,
    # ring 1 (hexes 2-7) — alliance 1
    2: 1, 3: 1, 4: 2, 5: 2, 6: 3, 7: 3,
    # ring 2 (hexes 8-19) — alliances 1,2,3,4
    8: 1, 9: 1, 10: 1, 11: 2, 12: 2, 13: 2,
    14: 3, 15: 3, 16: 4, 17: 4, 18: 4, 19: 4,
    # ring 3 (hexes 20-37) — split between alliances + some neutral
    20: 1, 21: 1, 22: 1, 23: 0, 24: 2, 25: 2, 26: 2, 27: 0,
    28: 3, 29: 3, 30: 3, 31: 0, 32: 4, 33: 4, 34: 4, 35: 0,
    36: 1, 37: 2,
}

WAREHOUSES = {5, 11, 19, 27}

for i in range(1, 38):
    terrain = TERRAINS[(i - 1) % len(TERRAINS)]
    patron = PATRON_MAP.get(i, 0)
    has_wh = 1 if i in WAREHOUSES else 0
    map_cells.append((i, terrain, patron if patron else None, has_wh))

# ---- Render ----
print("Rendering map...")
png_bytes = render_realistic_map_png(map_cells, alliances)

out_path = os.path.join(os.path.dirname(__file__), "test_map_output.png")
with open(out_path, "wb") as f:
    f.write(png_bytes)

print(f"Saved to: {out_path}  ({len(png_bytes) // 1024} KB)")

# Open with default viewer
import subprocess, platform
if platform.system() == "Windows":
    os.startfile(out_path)
elif platform.system() == "Darwin":
    subprocess.run(["open", out_path])
else:
    subprocess.run(["xdg-open", out_path])
