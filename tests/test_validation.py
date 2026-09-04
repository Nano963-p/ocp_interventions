from app import db
from app.models import Demande, Intervention
from tests.conftest import login


def test_invalid_request_fields_return_controlled_error(client, app):
    login(client)
    before = None
    with app.app_context():
        before = Demande.query.count()
    response = client.post('/demandes/nouvelle', data={
        'titre': '', 'description': 'x', 'client': '', 'localisation': '',
        'type_intervention': 'Type inventé', 'impact': '99',
        'date_echeance': 'not-a-date', 'priorite': 'inconnue',
    })
    assert response.status_code == 400
    with app.app_context():
        assert Demande.query.count() == before


def test_invalid_planning_and_piece_ids_do_not_raise_500(client, app):
    login(client, 'planner', 'planner-pass')
    request_id = app.config['IDS']['request_a']
    response = client.post(f'/demandes/{request_id}/planifier', data={
        'technicien_id': 'not-an-id', 'date_planifiee': 'bad-date'})
    assert response.status_code == 302

    client.post('/logout')
    login(client)
    intervention_id = app.config['IDS']['intervention_a']
    client.post(f'/interventions/{intervention_id}/statut', data={'statut': 'En cours'})
    response = client.post(f'/interventions/{intervention_id}/piece', data={
        'piece_id': 'missing', 'quantite': '-5'})
    assert response.status_code == 302


def test_invalid_gps_is_rejected(client, app):
    login(client)
    assert client.post('/techniciens/ma-position', data={
        'latitude': 'NaN', 'longitude': '0'}).status_code == 302
    assert client.post('/techniciens/ma-position', data={
        'latitude': '91', 'longitude': '-181'}).status_code == 302


def test_invalid_stock_values_return_controlled_error(client):
    login(client, 'planner', 'planner-pass')
    response = client.post('/stock/nouvelle', data={
        'nom': '', 'reference': '', 'quantite': '-1',
        'seuil_alerte': 'bad', 'prix_unitaire': 'NaN'})
    assert response.status_code == 400
