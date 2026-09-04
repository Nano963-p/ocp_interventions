
import os
import secrets
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_wtf import CSRFProtect
from flask_migrate import Migrate

db = SQLAlchemy()
login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.login_message = "Veuillez vous connecter pour accéder à cette page."
login_manager.login_message_category = "warning"
csrf = CSRFProtect()
migrate = Migrate()


def create_app(test_config=None):
    app = Flask(__name__)
    basedir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    app.config.from_mapping(
        SECRET_KEY=os.environ.get('SECRET_KEY') or secrets.token_hex(32),
        SQLALCHEMY_DATABASE_URI=os.environ.get(
            'DATABASE_URL', 'sqlite:///' + os.path.join(basedir, 'interventions.db')),
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        DEMO_MODE=os.environ.get('DEMO_MODE', '0') == '1',
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE='Lax',
        SESSION_COOKIE_SECURE=os.environ.get('SESSION_COOKIE_SECURE', '0') == '1',
        MAX_CONTENT_LENGTH=1 * 1024 * 1024,
    )
    if test_config:
        app.config.update(test_config)

    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)
    migrate.init_app(app, db) 

    from . import models 

    from .routes.auth import bp as auth_bp
    from .routes.main import bp as main_bp
    from .routes.demandes import bp as demandes_bp
    from .routes.interventions import bp as interventions_bp
    from .routes.techniciens import bp as techniciens_bp
    from .routes.stock import bp as stock_bp
    from .routes.rapports import bp as rapports_bp
    from .routes.suivi import bp as suivi_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(demandes_bp)
    app.register_blueprint(interventions_bp)
    app.register_blueprint(techniciens_bp)
    app.register_blueprint(stock_bp)
    app.register_blueprint(rapports_bp)
    app.register_blueprint(suivi_bp)

    @app.after_request
    def security_headers(response):
        response.headers.setdefault('X-Content-Type-Options', 'nosniff')
        response.headers.setdefault('X-Frame-Options', 'DENY')
        response.headers.setdefault('Referrer-Policy', 'strict-origin-when-cross-origin')
        response.headers.setdefault(
            'Content-Security-Policy',
            "default-src 'self'; img-src 'self' data: https://unpkg.com "
            "https://*.tile.openstreetmap.org; style-src 'self' 'unsafe-inline' "
            "https://cdn.jsdelivr.net https://unpkg.com https://fonts.googleapis.com; "
            "font-src 'self' https://cdn.jsdelivr.net https://fonts.gstatic.com; "
            "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://unpkg.com; "
            "connect-src 'self'; frame-ancestors 'none'; base-uri 'self'; form-action 'self'"
        )
        return response

    @app.errorhandler(403)
    def forbidden(e):
        from flask import render_template
        return render_template('errors/403.html'), 403

    @app.errorhandler(404)
    def not_found(e):
        from flask import render_template
        return render_template('errors/404.html'), 404

    return app
