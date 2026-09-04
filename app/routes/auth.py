# -*- coding: utf-8 -*-
"""Authentification et contrôle des rôles."""
from functools import wraps
from collections import defaultdict, deque
from threading import Lock
import time
from urllib.parse import urljoin, urlsplit

from flask import (Blueprint, abort, flash, redirect, render_template,
                   request, url_for)
from flask_login import current_user, login_required, login_user, logout_user

from ..models import User

bp = Blueprint('auth', __name__)
_login_attempts = defaultdict(deque)
_login_attempts_lock = Lock()
_LOGIN_WINDOW_SECONDS = 5 * 60
_LOGIN_MAX_FAILURES = 5


def _login_key(username):
    return request.remote_addr or 'unknown', username[:64].casefold()


def _is_login_limited(key):
    cutoff = time.monotonic() - _LOGIN_WINDOW_SECONDS
    with _login_attempts_lock:
        attempts = _login_attempts[key]
        while attempts and attempts[0] < cutoff:
            attempts.popleft()
        return len(attempts) >= _LOGIN_MAX_FAILURES


def _record_login_failure(key):
    with _login_attempts_lock:
        _login_attempts[key].append(time.monotonic())


def _clear_login_failures(key):
    with _login_attempts_lock:
        _login_attempts.pop(key, None)


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


def _is_safe_next_url(target):
    """Only allow redirects that stay on this application's origin."""
    if (not target or not target.startswith('/') or target.startswith('//')
            or '\\' in target or any(ord(char) < 32 for char in target)):
        return False
    host = urlsplit(request.host_url)
    destination = urlsplit(urljoin(request.host_url, target))
    return (destination.scheme in ('http', 'https')
            and destination.scheme == host.scheme
            and destination.netloc == host.netloc)


def can_access_demande(demande):
    if current_user.is_planificateur:
        return True
    if current_user.role != 'technicien':
        return False
    owns_request = demande.createur_id == current_user.id
    assigned = (demande.intervention is not None
                and current_user.technicien_id == demande.intervention.technicien_id)
    return owns_request or assigned


def can_access_intervention(intervention):
    return (current_user.is_planificateur
            or (current_user.role == 'technicien'
                and current_user.technicien_id == intervention.technicien_id))


@bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        if len(username) > 64 or len(password) > 1024:
            flash("Identifiants incorrects.", 'danger')
            return render_template('login.html'), 400
        key = _login_key(username)
        if _is_login_limited(key):
            flash("Trop de tentatives. Réessayez dans quelques minutes.", 'danger')
            return render_template('login.html'), 429
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            _clear_login_failures(key)
            login_user(user)
            flash(f"Bienvenue, {user.nom} !", 'success')
            next_url = request.args.get('next')
            return redirect(next_url if _is_safe_next_url(next_url)
                            else url_for('main.dashboard'))
        _record_login_failure(key)
        flash("Identifiants incorrects.", 'danger')
    return render_template('login.html')


@bp.route('/logout', methods=['POST'])
@login_required
def logout():
    logout_user()
    flash("Vous êtes déconnecté.", 'info')
    return redirect(url_for('auth.login'))
