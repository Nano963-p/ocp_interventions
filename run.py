# -*- coding: utf-8 -*-
import os
from app import create_app

app = create_app()

if __name__ == '__main__':
    # debug=True active le débogueur interactif Werkzeug, qui permet
    # d'exécuter du code Python arbitraire depuis le navigateur si le
    # serveur est joignable depuis l'extérieur. À n'activer QUE via la
    # variable d'environnement FLASK_DEBUG=1 sur un poste de dev local,
    # jamais par défaut ni en démo/production.
    debug_mode = os.environ.get('FLASK_DEBUG', '0') == '1'
    app.run(host='0.0.0.0', port=5000, debug=debug_mode)