# -*- coding: utf-8 -*-
"""
Скрипт для визуализации карты планеты в виде гексагональной сетки
"""
import sqlite3
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np
import math
import os

# Цвета для разных типов территорий
TERRITORY_COLORS = {
    "Леса": "#228B22",                    # Зелёный
    "Тундра/снег": "#F0F8FF",            # Светло-голубой/белый
    "Пустыня": "#F4A460",                # Песочный
    "Отравленные земли": "#556B2F",      # Тёмно-оливковый
    "Завод": "#708090",                  # Серый сланцевый
    "Город": "#4682B4",                  # Стальной синий
    "Разрушенный город": "#8B4513",      # Коричневый седло
    "Подземные системы": "#2F4F4F",      # Тёмно-серый сланцевый
    "Останки корабля": "#C0C0C0",        # Серебряный
    "Свалка": "#8B7D6B",                 # Тёмно-серый
    "Храовый квартал": "#FFD700",        # Золотой
    "Изменённое варпом пространство": "#800080"  # Фиолетовый
}

def hex_to_pixel(q, r, size):
    """Конвертирует hex координаты в пиксельные"""
    x = size * (3/2 * q)
    y = size * (math.sqrt(3)/2 * q + math.sqrt(3) * r)
    return x, y

def draw_hexagon(ax, center_x, center_y, size, color):
    """Рисует один гексагон"""
    angles = np.linspace(0, 2*np.pi, 7)  # 7 точек для замкнутого гексагона
    x_coords = center_x + size * np.cos(angles + np.pi/6)  # Поворот на 30 градусов
    y_coords = center_y + size * np.sin(angles + np.pi/6)
    
    hexagon = patches.Polygon(list(zip(x_coords, y_coords)), 
                             facecolor=color, edgecolor='black', linewidth=0.5)
    ax.add_patch(hexagon)

def reconstruct_coordinates(hex_map_data):
    """Восстанавливает hex координаты из структуры колец"""
    
    # Создаём словарь для быстрого поиска
    id_to_data = {item['id']: item for item in hex_map_data}
    
    # Центральный гекс (ID 1) всегда в центре
    coordinates = {1: (0, 0)}
    used_ids = {1}
    
    # Функция для генерации кольца
    def hex_ring(center_q, center_r, radius):
        if radius == 0:
            return [(center_q, center_r)]
        results = []
        # Направления для гексагональной сетки
        directions = [(1, 0), (1, -1), (0, -1), (-1, 0), (-1, 1), (0, 1)]
        
        # Начинаем с точки на расстоянии radius в направлении 4 (вниз-влево)
        q, r = center_q + directions[4][0] * radius, center_r + directions[4][1] * radius
        
        for i in range(6):
            for _ in range(radius):
                results.append((q, r))
                dq, dr = directions[i]
                q += dq
                r += dr
        return results
    
    # Распределяем по кольцам
    current_id = 2
    radius = 1
    
    while current_id <= len(hex_map_data):
        ring_coords = hex_ring(0, 0, radius)
        
        for coord in ring_coords:
            if current_id <= len(hex_map_data):
                coordinates[current_id] = coord
                current_id += 1
            else:
                break
        
        radius += 1
        
        # Защита от бесконечного цикла
        if radius > 20:
            break
    
    return coordinates

def visualize_planet_map(db_path=None, output_path=None):
    """Создаёт визуализацию карты планеты"""
    
    # Определяем путь к базе данных
    if db_path is None:
        if os.path.exists('/app/data/game_database.db'):
            db_path = '/app/data/game_database.db'
        elif os.path.exists('game_database.db'):
            db_path = 'game_database.db'
        else:
            raise FileNotFoundError("База данных не найдена")
    
    # Подключаемся к базе данных
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Получаем данные о картах
    cursor.execute("SELECT id, state FROM map ORDER BY id")
    map_data = cursor.fetchall()
    
    if not map_data:
        raise ValueError("Нет данных в таблице map")
    
    print(f"Загружено {len(map_data)} гексов")
    
    # Преобразуем в список словарей
    hex_data = [{'id': row[0], 'state': row[1]} for row in map_data]
    
    # Восстанавливаем координаты
    coordinates = reconstruct_coordinates(hex_data)
    
    # Создаём фигуру
    fig, ax = plt.subplots(1, 1, figsize=(20, 20))
    
    hex_size = 1.0
    
    # Рисуем каждый гекс
    for hex_info in hex_data:
        hex_id = hex_info['id']
        state = hex_info['state']
        
        if hex_id in coordinates:
            q, r = coordinates[hex_id]
            x, y = hex_to_pixel(q, r, hex_size)
            
            # Получаем цвет для территории
            color = TERRITORY_COLORS.get(state, '#CCCCCC')  # Серый по умолчанию
            
            # Рисуем гексагон
            draw_hexagon(ax, x, y, hex_size, color)
    
    # Настройки графика
    ax.set_aspect('equal')
    ax.set_title('Карта Планеты', fontsize=24, fontweight='bold')
    
    # Убираем оси
    ax.set_xticks([])
    ax.set_yticks([])
    
    # Создаём легенду
    legend_elements = []
    for state, color in TERRITORY_COLORS.items():
        # Проверяем, есть ли такой тип территории на карте
        if any(hex_info['state'] == state for hex_info in hex_data):
            legend_elements.append(patches.Patch(color=color, label=state))
    
    ax.legend(handles=legend_elements, loc='upper right', bbox_to_anchor=(1.15, 1))
    
    # Убираем границы
    for spine in ax.spines.values():
        spine.set_visible(False)
    
    plt.tight_layout()
    
    # Сохраняем файл
    if output_path is None:
        output_path = '/app/planet_map.png'
    
    plt.savefig(output_path, dpi=300, bbox_inches='tight', 
                facecolor='white', edgecolor='none')
    
    print(f"Карта сохранена: {output_path}")
    
    conn.close()
    return output_path

if __name__ == "__main__":
    try:
        output_file = visualize_planet_map()
        print(f"Визуализация завершена: {output_file}")
    except Exception as e:
        print(f"Ошибка: {e}")