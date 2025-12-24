# -*- coding: utf-8 -*-
"""
Constants for hexagonal map generation and expansion.
Used by both generate_planet.py and sqllite_helper.py
"""

# Planet identifier
PLANET_ID = 1

# Possible terrain states for hexes
STATES = [
    "Леса",
    "Тундра/снег",
    "Пустыня",
    "Отравленные земли",
    "Завод",
    "Город",
    "Разрушенный город",
    "Подземные системы",
    "Останки корабля",
    "Свалка",
    "Храмовый квартал",
    "Изменённое варпом пространство"
]

# Hexagonal grid direction vectors
# Used to navigate between adjacent hexes in a hexagonal grid
HEX_DIRECTIONS = [
    (1, 0), (1, -1), (0, -1),
    (-1, 0), (-1, 1), (0, 1)
]
