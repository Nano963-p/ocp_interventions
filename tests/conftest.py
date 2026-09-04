from datetime import date

import pytest
from werkzeug.security import generate_password_hash

from app import create_app, db
from app.models import Demande, Intervention, Technicien, User, utcnow


@pytest.fixture()
def app():
    application = create_app({
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
        'WTF_CSRF_ENABLED': False,
        'SECRET_KEY': 'test-only-secret',
        'DEMO_MODE': False,
    })
    with application.app_context():
        db.create_all()
        tech_a = Technicien(nom='Technicien A', specialite='Mécanique',
                            zone='Zone Démo A', telephone='0000000001')
        tech_b = Technicien(nom='Technicien B', specialite='Électrique',
                            zone='Zone Démo B', telephone='0000000002')
        db.session.add_all([tech_a, tech_b])
        db.session.flush()

        planner = User(username='planner', nom='Planificateur', role='planificateur')
        planner.password_hash = generate_password_hash('planner-pass', method='pbkdf2:sha256:1')
        user_a = User(username='tech-a', nom='Technicien A', role='technicien',
                      technicien_id=tech_a.id)
        user_a.password_hash = generate_password_hash('tech-pass', method='pbkdf2:sha256:1')
        user_b = User(username='tech-b', nom='Technicien B', role='technicien',
                      technicien_id=tech_b.id)
        user_b.password_hash = generate_password_hash('tech-pass', method='pbkdf2:sha256:1')
        db.session.add_all([planner, user_a, user_b])
        db.session.flush()

        request_a = Demande(
            titre='Demande visible A', description='Description client A',
            client='Client fictif A', localisation='Zone Démo A',
            type_intervention='Mécanique', impact=3, priorite='Moyenne',
            statut='Planifiée', createur_id=user_a.id)
        request_b = Demande(
            titre='Demande privée B', description='DESCRIPTION_CONFIDENTIELLE_B',
            client='Client fictif B', localisation='Zone Démo B',
            type_intervention='Électrique', impact=4, priorite='Haute',
            statut='Planifiée', createur_id=user_b.id)
        db.session.add_all([request_a, request_b])
        db.session.flush()
        intervention_a = Intervention(
            demande_id=request_a.id, technicien_id=tech_a.id,
            date_planifiee=date.today(), statut='Planifiée')
        intervention_b = Intervention(
            demande_id=request_b.id, technicien_id=tech_b.id,
            date_planifiee=date.today(), statut='Planifiée',
            observations='OBSERVATIONS_CONFIDENTIELLES_B',
            rapport='RAPPORT_CONFIDENTIEL_B', date_debut=utcnow())
        db.session.add_all([intervention_a, intervention_b])
        db.session.commit()
        application.config['IDS'] = {
            'request_a': request_a.id, 'request_b': request_b.id,
            'intervention_a': intervention_a.id,
            'intervention_b': intervention_b.id,
            'tech_a': tech_a.id, 'tech_b': tech_b.id,
        }
        yield application
        db.session.remove()
        db.drop_all()


@pytest.fixture()
def client(app):
    return app.test_client()


def login(client, username='tech-a', password='tech-pass', next_url=None):
    path = '/login'
    if next_url is not None:
        path += f'?next={next_url}'
    return client.post(path, data={'username': username, 'password': password})
