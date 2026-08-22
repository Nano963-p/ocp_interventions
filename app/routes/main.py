# -*- coding: utf-8 -*-
"""Tableau de bord et page d'aide à la décision."""
from datetime import date

from flask import Blueprint, render_template
from flask_login import login_required

from .. import db, intelligence
from ..models import Demande, Intervention, Piece, Technicien

bp = Blueprint('main', __name__)


@bp.route('/')
@login_required
def dashboard():
    stats = {
        'nb_demandes': Demande.query.count(),
        'nb_nouvelles': Demande.query.filter_by(statut='Nouvelle').count(),
        'nb_actives': Intervention.query.filter(
            Intervention.statut.in_(['Planifiée', 'En cours'])).count(),
        'nb_terminees': Intervention.query.filter_by(statut='Terminée').count(),
        'nb_techniciens': Technicien.query.count(),
        'nb_pieces_alerte': Piece.query.filter(Piece.quantite <= Piece.seuil_alerte).count(),
    }

    statuts = ['Planifiée', 'En cours', 'Terminée', 'Annulée']
    par_statut = [Intervention.query.filter_by(statut=s).count() for s in statuts]

    today = date.today()
    mois_labels, mois_data = [], []
    for i in range(5, -1, -1):
        mm, yy = today.month - i, today.year
        while mm <= 0:
            mm += 12
            yy -= 1
        count = Intervention.query.filter(
            db.extract('year', Intervention.date_planifiee) == yy,
            db.extract('month', Intervention.date_planifiee) == mm).count()
        mois_labels.append(f"{mm:02d}/{yy}")
        mois_data.append(count)

    alertes = intelligence.generer_alertes()[:6]
    kpis = intelligence.calculer_kpis()
    demandes_recentes = Demande.query.order_by(Demande.date_creation.desc()).limit(6).all()

    return render_template('dashboard.html', stats=stats, kpis=kpis,
                           statuts=statuts, par_statut=par_statut,
                           mois_labels=mois_labels, mois_data=mois_data,
                           alertes=alertes, demandes_recentes=demandes_recentes)


@bp.route('/intelligence')
@login_required
def intelligence_page():
    """Centre d'aide à la décision : recommandations, alertes, prévisions."""
    return render_template(
        'intelligence.html',
        alertes=intelligence.generer_alertes(),
        recommandations=intelligence.recommandations_affectation(),
        previsions=intelligence.previsions_stock(),
        kpis=intelligence.calculer_kpis(),
    )