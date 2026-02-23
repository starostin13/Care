#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Authentication module for admin panel
Uses Flask-Login and integrates with warmasters table
"""

import asyncio
import hashlib
from functools import wraps
from flask import Blueprint, request, render_template, redirect, url_for, flash, session
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import check_password_hash, generate_password_hash
import sqllite_helper

# Create Blueprint for auth routes
auth_bp = Blueprint('auth', __name__)

# Login manager will be initialized in server_app.py
login_manager = None


class AdminUser(UserMixin):
    """
    User class for Flask-Login
    Represents an authenticated admin user
    """
    def __init__(self, warmaster_id, nickname, alliance=None):
        self.id = warmaster_id  # Flask-Login requires 'id' attribute
        self.warmaster_id = warmaster_id
        self.nickname = nickname
        self.alliance = alliance
    
    def get_id(self):
        """Required by Flask-Login - returns user ID as string"""
        return str(self.warmaster_id)
    
    @property
    def is_authenticated(self):
        """Required by Flask-Login"""
        return True
    
    @property
    def is_active(self):
        """Required by Flask-Login"""
        return True
    
    @property
    def is_anonymous(self):
        """Required by Flask-Login"""
        return False


async def _load_user_async(warmaster_id: int):
    """Async helper to load user from database"""
    # Check if user is an admin
    is_admin = await sqllite_helper.check_admin_exists(int(warmaster_id))
    if not is_admin:
        return None
    
    # Get warmaster information
    warmaster_info = await sqllite_helper.get_settings(str(warmaster_id))
    if not warmaster_info:
        return None
    
    nickname = warmaster_info[0] if warmaster_info else f"User {warmaster_id}"
    
    # Get alliance if available
    alliance_id = await sqllite_helper.get_alliance_of_warmaster(str(warmaster_id))
    alliance_name = None
    if alliance_id:
        alliances = await sqllite_helper.get_all_alliances()
        alliance_name = next((a[1] for a in alliances if a[0] == alliance_id), None)
    
    return AdminUser(warmaster_id, nickname, alliance_name)


@login_manager.user_loader
def load_user(warmaster_id):
    """
    User loader callback for Flask-Login
    Loads user from database by warmaster_id
    """
    if not warmaster_id:
        return None
    
    try:
        # Run async function in sync context
        user = asyncio.run(_load_user_async(int(warmaster_id)))
        return user
    except Exception as e:
        print(f"Error loading user {warmaster_id}: {e}")
        return None


async def _verify_login_async(warmaster_id: int, password: str):
    """Async helper to verify login credentials"""
    # Get admin user from database
    admin_info = await sqllite_helper.get_admin_by_warmaster_id(warmaster_id)
    
    if not admin_info:
        return None
    
    admin_id, wm_id, created_at, last_login, is_active = admin_info
    
    # Check if admin is active
    if not is_active:
        return None
    
    # Get password hash from database
    # In production, password_hash should be stored in admin_users table
    # For now, we'll use a simple hash comparison
    # TODO: Update to use proper bcrypt password hashing
    
    password_hash = hashlib.sha256(password.encode()).hexdigest()
    
    # Verify credentials
    is_valid = await sqllite_helper.verify_admin_credentials(warmaster_id, password_hash)
    
    if not is_valid:
        return None
    
    # Update last login
    await sqllite_helper.update_admin_last_login(warmaster_id)
    
    return await _load_user_async(warmaster_id)


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Login page and handler"""
    if current_user.is_authenticated:
        return redirect(url_for('admin_dashboard'))
    
    if request.method == 'POST':
        warmaster_id = request.form.get('warmaster_id')
        password = request.form.get('password')
        remember = request.form.get('remember', False) == 'on'
        
        if not warmaster_id or not password:
            flash('Пожалуйста, заполните все поля', 'error')
            return render_template('login.html')
        
        try:
            warmaster_id = int(warmaster_id)
        except ValueError:
            flash('Неверный ID warmaster', 'error')
            return render_template('login.html')
        
        # Verify credentials
        user = asyncio.run(_verify_login_async(warmaster_id, password))
        
        if user is None:
            flash('Неверные учетные данные или нет прав администратора', 'error')
            return render_template('login.html')
        
        # Log user in
        login_user(user, remember=remember)
        session.permanent = remember
        
        flash(f'Добро пожаловать, {user.nickname}!', 'success')
        
        # Redirect to next page or admin dashboard
        next_page = request.args.get('next')
        if next_page:
            return redirect(next_page)
        return redirect(url_for('admin_dashboard'))
    
    # GET request - show login form
    # Get list of warmasters for dropdown
    warmasters = asyncio.run(sqllite_helper.get_all_warmasters())
    
    return render_template('login.html', warmasters=warmasters)


@auth_bp.route('/logout')
@login_required
def logout():
    """Logout handler"""
    nickname = current_user.nickname if current_user.is_authenticated else "User"
    logout_user()
    flash(f'До свидания, {nickname}!', 'info')
    return redirect(url_for('auth.login'))


async def _get_all_warmasters_async():
    """Get all warmasters for dropdown"""
    warmasters = await sqllite_helper.get_all_warmasters()
    admins = await sqllite_helper.get_all_admin_users()
    admin_warmaster_ids = {admin[1] for admin in admins}  # Set of warmaster IDs that are admins
    
    return [
        {
            'id': wm[0],
            'nickname': wm[3],
            'alliance': wm[2],
            'is_admin': wm[0] in admin_warmaster_ids
        }
        for wm in warmasters
    ]


async def _create_first_admin_async(warmaster_id: int, password: str):
    """Create the first admin user"""
    password_hash = hashlib.sha256(password.encode()).hexdigest()
    await sqllite_helper.create_admin_user(warmaster_id, password_hash)


def create_first_admin(warmaster_id: int, password: str):
    """
    Utility function to create the first admin user
    Usage: Run this once to set up the first admin
    """
    asyncio.run(_create_first_admin_async(warmaster_id, password))
    print(f"✅ Admin user created for warmaster_id: {warmaster_id}")


def init_login_manager(app):
    """
    Initialize Flask-Login manager
    Call this from server_app.py
    """
    global login_manager
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Пожалуйста, войдите для доступа к этой странице'
    login_manager.login_message_category = 'warning'
    
    # Set up user loader
    login_manager.user_loader(load_user)
    
    return login_manager


def admin_required(f):
    """
    Decorator to require admin authentication
    Combines @login_required with admin check
    """
    @wraps(f)
    @login_required
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('auth.login'))
        
        # Additional admin checks can go here
        # For now, being logged in means you're an admin
        
        return f(*args, **kwargs)
    return decorated_function
