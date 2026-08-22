# -*- coding: utf-8 -*-
"""Authentification et contrôle des rôles."""
from functools import wraps

from flask import (Blueprint, abort, flash, redirect, render_template,
                   request, url_for)
from flask_login import current_user, login_required, login_user, logout_user

from ..models import User

bp = Blueprint('auth', __name__)


def role_required(*roles):
    """Décorateur : restreint l'accès à certains rôles."""
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            if not current_user.is_authenticated:
                return redirect(url_for('auth.login'))
            if current_user.role not in roles:
                abort(403)
            return f(*args, **kwargs)
        return wrapper
    return decorator


@bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            login_user(user)
            flash(f"Bienvenue, {user.nom} !", 'success')
            return redirect(request.args.get('next') or url_for('main.dashboard'))
        flash("Identifiants incorrects.", 'danger')
    return render_template('login.html')


@bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash("Vous êtes déconnecté.", 'info')
    return redirect(url_for('auth.login'))