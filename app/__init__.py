
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


def create_app():
    app = Flask(__name__)
    basedir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY') or secrets.token_hex(32)
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get(
        'DATABASE_URL', 'sqlite:///' + os.path.join(basedir, 'interventions.db'))
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

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

    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(demandes_bp)
    app.register_blueprint(interventions_bp)
    app.register_blueprint(techniciens_bp)
    app.register_blueprint(stock_bp)
    app.register_blueprint(rapports_bp)

    @app.errorhandler(403)
    def forbidden(e):
        from flask import render_template
        return render_template('errors/403.html'), 403

    @app.errorhandler(404)
    def not_found(e):
        from flask import render_template
        return render_template('errors/404.html'), 404


    with app.app_context():
        pass
        from .seed import seed_if_empty
        seed_if_empty()

    return app