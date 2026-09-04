from datetime import date, timedelta

from app import db, intelligence
from app.models import Demande, Intervention, Technicien, utcnow


def test_rule_based_priority_scoring_is_bounded():
    priority, score, reasons = intelligence.analyser_priorite(
        'Panne urgente de production', impact=5,
        date_echeance=date.today() - timedelta(days=1))
    assert priority == 'Critique'
    assert score == 85
    assert 0 <= score <= 100
    assert reasons


def test_tfidf_retrieval_returns_most_similar_case(app):
    with app.app_context():
        tech = Technicien.query.first()
        matching = Demande(
            titre='Fuite pompe hydraulique', description='joint huile pression',
            client='Démo', localisation='Zone Démo A', type_intervention='Hydraulique',
            impact=3, priorite='Moyenne', statut='Terminée')
        different = Demande(
            titre='Panne réseau informatique', description='switch connexion',
            client='Démo', localisation='Zone Démo A', type_intervention='Informatique',
            impact=2, priorite='Basse', statut='Terminée')
        target = Demande(
            titre='Fuite hydraulique pompe', description='pression huile joint',
            client='Démo', localisation='Zone Démo A', type_intervention='Hydraulique',
            impact=3, priorite='Moyenne', statut='Nouvelle')
        db.session.add_all([matching, different, target])
        db.session.flush()
        for demande, report in ((matching, 'joint hydraulique remplacé'),
                                 (different, 'switch redémarré')):
            db.session.add(Intervention(
                demande_id=demande.id, technicien_id=tech.id,
                date_planifiee=date.today(), statut='Terminée',
                date_debut=utcnow() - timedelta(hours=2),
                date_fin=utcnow(), rapport=report))
        db.session.commit()
        results = intelligence.rechercher_cas_similaires(target, seuil_minimal=0)
        assert results
        assert results[0]['intervention'].demande_id == matching.id


def test_groq_disabled_returns_none_without_external_call(app, monkeypatch):
    monkeypatch.delenv('GROQ_API_KEY', raising=False)
    with app.app_context():
        demande = Demande.query.first()
        fake_cases = [{'intervention': demande.intervention,
                       'score_similarite': 50.0}]
        assert intelligence.synthetiser_recommandation_ia(demande, fake_cases) is None
        assert intelligence.synthetiser_recommandation_ia(demande, []) is None
