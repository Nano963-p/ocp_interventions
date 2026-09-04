# -*- coding: utf-8 -*-
"""Point d'entrée de l'application OCP Khouribga – Gestion des Interventions."""
import os
from app import create_app

app = create_app()

if __name__ == '__main__':
    if app.config['DEMO_MODE']:
        with app.app_context():
            from app.seed import seed_if_empty
            seed_if_empty()

    debug_mode = os.environ.get('FLASK_DEBUG', '0') == '1'
    app.run(host='0.0.0.0', port=5000, debug=debug_mode)
