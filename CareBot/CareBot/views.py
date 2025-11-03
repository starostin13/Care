"""
Routes and views for the flask application.
"""

from datetime import datetime
from flask import render_template, jsonify
from . import app
import os

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

@app.route('/health')
def health():
    """Health check endpoint for monitoring."""
    try:
        # Check if database file exists
        db_path = os.environ.get('DATABASE_PATH', '/app/data/game_database.db')
        db_exists = os.path.exists(db_path)
        
        return jsonify({
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'database': 'available' if db_exists else 'missing',
            'version': '1.0.0'
        }), 200
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'timestamp': datetime.now().isoformat(),
            'error': str(e),
            'version': '1.0.0'
        }), 500
