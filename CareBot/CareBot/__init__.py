"""
The flask application package.
Imports the configured Flask app from server_app.py
"""

# Import the properly configured Flask app from server_app
from .server_app import app

__all__ = ['app']
