"""
Routes and views for the flask application.
"""

from datetime import datetime
from flask import render_template, jsonify
from CareBot import app
import asyncio
import sqllite_helper

@app.route('/')
@app.route('/home')
def home():
    """Renders the home page."""
    return render_template(
        'index.html',
        title='Home Page',
        year=datetime.now().year,
    )

@app.route('/contact')
def contact():
    """Renders the contact page."""
    return render_template(
        'contact.html',
        title='Contact',
        year=datetime.now().year,
        message='Your contact page.'
    )

@app.route('/about')
def about():
    """Renders the about page."""
    return render_template(
        'about.html',
        title='About',
        year=datetime.now().year,
        message='Your application description page.'
    )

@app.route('/map')
def map_view():
    """Renders the map page for Telegram Mini App."""
    return render_template(
        'map.html',
        title='Crusade Map',
        year=datetime.now().year,
    )

@app.route('/api/map-data')
def get_map_data():
    """Returns map data as JSON."""
    async def fetch_map_data():
        return await sqllite_helper.get_all_map_cells()
    
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        map_data = loop.run_until_complete(fetch_map_data())
        loop.close()
        
        # Преобразуем данные в нужный формат
        formatted_data = []
        for cell in map_data:
            formatted_data.append({
                'id': cell[0],
                'planet_id': cell[1],
                'state': cell[2],
                'patron': cell[3],
                'has_warehouse': bool(cell[4]) if len(cell) > 4 else False
            })
        
        return jsonify(formatted_data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/hex-info/<int:hex_id>')
def get_hex_info(hex_id):
    """Returns detailed information about a specific hex."""
    async def fetch_hex_info():
        # Получаем информацию о hex
        cell_info = await sqllite_helper.get_cell_info(hex_id)
        history = await sqllite_helper.get_cell_histrory(hex_id)
        
        # Получаем имя альянса-патрона
        patron_name = None
        if cell_info and cell_info[3]:  # patron field
            patron_info = await sqllite_helper.get_alliance_name(cell_info[3])
            patron_name = patron_info[0] if patron_info else None
        
        return {
            'cell_info': cell_info,
            'history': [h[0] for h in history] if history else [],
            'patron_name': patron_name
        }
    
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        hex_data = loop.run_until_complete(fetch_hex_info())
        loop.close()
        
        return jsonify(hex_data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500
