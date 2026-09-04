# -*- coding: utf-8 -*-
"""Tableau de bord et page d'aide à la décision."""
from datetime import date

from flask import Blueprint, render_template
from flask_login import current_user, login_required
from sqlalchemy import or_

from .. import intelligence
from ..models import Demande, Intervention, Piece, Technicien
from .auth import role_required


def _kpis_for(interventions, demandes):
    terminees = [iv for iv in interventions if iv.statut == 'Terminée']
    durations = [iv.duree_heures() for iv in terminees if iv.duree_heures() is not None]
    late = sum(1 for demande in demandes if demande.en_retard)
    return {
        'taux_resolution': round(100 * len(terminees) / len(interventions), 1)
        if interventions else 0,
        'duree_moyenne': round(sum(durations) / len(durations), 1) if durations else 0,
        'taux_retard': round(100 * late / len(demandes), 1) if demandes else 0,
        'nb_demandes_retard': late,
    }

bp = Blueprint('main', __name__)


@bp.route('/')
@login_required
def dashboard():
    if current_user.role == 'technicien':
        intervention_query = Intervention.query.filter_by(
            technicien_id=current_user.technicien_id) if current_user.technicien_id else Intervention.query.filter(False)
        interventions = intervention_query.all()
        demande_query = Demande.query.filter(Demande.createur_id == current_user.id)
        if current_user.technicien_id:
            demande_query = Demande.query.outerjoin(Intervention).filter(or_(
                Demande.createur_id == current_user.id,
                Intervention.technicien_id == current_user.technicien_id))
        demandes = demande_query.distinct().all()
        stats = {
            'nb_demandes': len(demandes),
            'nb_nouvelles': sum(d.statut == 'Nouvelle' for d in demandes),
            'nb_actives': sum(iv.statut in ('Planifiée', 'En cours') for iv in interventions),
            'nb_terminees': sum(iv.statut == 'Terminée' for iv in interventions),
            'nb_techniciens': 0,
            'nb_pieces_alerte': 0,
        }
        kpis = _kpis_for(interventions, demandes)
        alertes = []
        demandes_recentes = sorted(
            demandes, key=lambda d: d.date_creation, reverse=True)[:6]
    else:
        interventions = Intervention.query.all()
        demandes = Demande.query.all()
        stats = {
            'nb_demandes': len(demandes),
            'nb_nouvelles': Demande.query.filter_by(statut='Nouvelle').count(),
            'nb_actives': Intervention.query.filter(
                Intervention.statut.in_(['Planifiée', 'En cours'])).count(),
            'nb_terminees': Intervention.query.filter_by(statut='Terminée').count(),
            'nb_techniciens': Technicien.query.count(),
            'nb_pieces_alerte': Piece.query.filter(Piece.quantite <= Piece.seuil_alerte).count(),
        }
        kpis = intelligence.calculer_kpis()
        alertes = intelligence.generer_alertes()[:6]
        demandes_recentes = Demande.query.order_by(Demande.date_creation.desc()).limit(6).all()

    statuts = ['Planifiée', 'En cours', 'Terminée', 'Annulée']
    par_statut = [sum(iv.statut == s for iv in interventions) for s in statuts]

    today = date.today()
    mois_labels, mois_data = [], []
    for i in range(5, -1, -1):
        mm, yy = today.month - i, today.year
        while mm <= 0:
            mm += 12
            yy -= 1
        count = sum(iv.date_planifiee.year == yy and iv.date_planifiee.month == mm
                    for iv in interventions)
        mois_labels.append(f"{mm:02d}/{yy}")
        mois_data.append(count)

    return render_template('dashboard.html', stats=stats, kpis=kpis,
                           statuts=statuts, par_statut=par_statut,
                           mois_labels=mois_labels, mois_data=mois_data,
                           alertes=alertes, demandes_recentes=demandes_recentes)


@bp.route('/intelligence')
@role_required('admin', 'planificateur')
def intelligence_page():
    """Centre d'aide à la décision : recommandations, alertes, prévisions."""
    return render_template(
        'intelligence.html',
        alertes=intelligence.generer_alertes(),
        recommandations=intelligence.recommandations_affectation(),
        previsions=intelligence.previsions_stock(),
        kpis=intelligence.calculer_kpis(),
    )
