import re

from app import db
from app.models import Demande, Intervention
from tests.conftest import login


def test_technician_only_sees_owned_requests(client, app):
    login(client)
    response = client.get('/demandes/')
    assert response.status_code == 200
    assert b'Demande visible A' in response.data
    assert b'Demande priv\xc3\xa9e B' not in response.data
    response = client.get(f"/demandes/{app.config['IDS']['request_b']}")
    assert response.status_code == 403


def test_technician_cannot_access_other_intervention_or_reports(client, app):
    login(client)
    other = app.config['IDS']['intervention_b']
    assert client.get(f'/interventions/{other}').status_code == 403
    assert client.get(f'/rapports/intervention/{other}').status_code == 403
    assert client.get(f'/rapports/intervention/{other}/pdf').status_code == 403
    assert client.get('/rapports/').status_code == 403
    assert client.get('/rapports/pdf').status_code == 403
    assert client.get('/intelligence').status_code == 403


def test_technician_dashboard_is_scoped(client):
    login(client)
    response = client.get('/')
    assert response.status_code == 200
    assert b'Demande visible A' in response.data
    assert b'Demande priv\xc3\xa9e B' not in response.data
    assert b'Alertes stock' not in response.data


def test_login_next_redirect_is_same_origin_only(client):
    external = login(client, next_url='https://evil.example/phish')
    assert external.headers['Location'].endswith('/')
    client.post('/logout')
    internal = login(client, next_url='/demandes/')
    assert internal.headers['Location'].endswith('/demandes/')


def test_logout_and_ai_generation_are_post_only(client, app, monkeypatch):
    login(client)
    assert client.get('/logout').status_code == 405
    request_id = app.config['IDS']['request_a']
    assert client.get(f'/demandes/{request_id}/synthese-ia').status_code == 405
    assert client.post(f'/demandes/{request_id}/synthese-ia').status_code == 403


def test_planner_can_post_ai_generation_when_provider_is_disabled(client, app,
                                                                   monkeypatch):
    monkeypatch.delenv('GROQ_API_KEY', raising=False)
    login(client, 'planner', 'planner-pass')
    request_id = app.config['IDS']['request_a']
    response = client.post(f'/demandes/{request_id}/synthese-ia')
    assert response.status_code == 200


def test_csrf_is_required_for_logout(client, app):
    app.config['WTF_CSRF_ENABLED'] = True
    login_page = client.get('/login')
    token = re.search(rb'name="csrf_token" value="([^"]+)"', login_page.data).group(1)
    response = client.post('/login', data={
        'csrf_token': token.decode(), 'username': 'tech-a', 'password': 'tech-pass'})
    assert response.status_code == 302
    assert client.post('/logout').status_code == 400
    dashboard = client.get('/')
    token = re.search(rb'name="csrf_token" value="([^"]+)"', dashboard.data).group(1)
    assert client.post('/logout', data={'csrf_token': token.decode()}).status_code == 302


def test_repeated_failed_logins_are_throttled(client):
    for _ in range(5):
        assert client.post('/login', data={
            'username': 'rate-limit-test', 'password': 'wrong'}).status_code == 200
    assert client.post('/login', data={
        'username': 'rate-limit-test', 'password': 'wrong'}).status_code == 429


def test_public_tracking_is_minimal_and_not_cached(client, app):
    with app.app_context():
        demande = db.session.get(Demande, app.config['IDS']['request_b'])
        token = demande.token_suivi
    response = client.get(f'/suivi/{token}')
    assert response.status_code == 200
    assert b'Demande priv\xc3\xa9e B' in response.data
    for private_value in (
        b'DESCRIPTION_CONFIDENTIELLE_B', b'OBSERVATIONS_CONFIDENTIELLES_B',
        b'RAPPORT_CONFIDENTIEL_B', b'Technicien B', b'0000000002', b'MAD'):
        assert private_value not in response.data
    assert response.headers['Cache-Control'].startswith('no-store')
    assert response.headers['Referrer-Policy'] == 'no-referrer'
    assert response.headers['X-Robots-Tag'] == 'noindex, nofollow, noarchive'


def test_forbidden_status_transition_is_not_persisted(client, app):
    login(client)
    intervention_id = app.config['IDS']['intervention_a']
    response = client.post(f'/interventions/{intervention_id}/statut',
                           data={'statut': 'Terminée'})
    assert response.status_code == 302
    with app.app_context():
        assert db.session.get(Intervention, intervention_id).statut == 'Planifiée'


def test_valid_status_transitions_are_persisted(client, app):
    login(client)
    intervention_id = app.config['IDS']['intervention_a']
    client.post(f'/interventions/{intervention_id}/statut', data={'statut': 'En cours'})
    client.post(f'/interventions/{intervention_id}/statut', data={'statut': 'Terminée'})
    with app.app_context():
        intervention = db.session.get(Intervention, intervention_id)
        assert intervention.statut == 'Terminée'
        assert intervention.date_debut is not None
        assert intervention.date_fin is not None
