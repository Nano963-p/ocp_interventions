# -*- coding: utf-8 -*-
"""Gestion des demandes d'intervention (création, priorisation IA, planification)."""
from datetime import datetime

from flask import (Blueprint, flash, redirect, render_template, request,
                   url_for)
from flask_login import login_required

from .. import db, intelligence
from ..models import Demande, Intervention, Technicien, TYPES_INTERVENTION
from .auth import role_required

bp = Blueprint('demandes', __name__, url_prefix='/demandes')


@bp.route('/')
@login_required
def liste():
    query = Demande.query
    statut = request.args.get('statut', '')
    priorite = request.args.get('priorite', '')
    if statut:
        query = query.filter_by(statut=statut)
    if priorite:
        query = query.filter_by(priorite=priorite)
    demandes = query.order_by(Demande.date_creation.desc()).all()
    return render_template('demandes/liste.html', demandes=demandes,
                           statut=statut, priorite=priorite)


@bp.route('/nouvelle', methods=['GET', 'POST'])
@login_required
def nouvelle():
    if request.method == 'POST':
        titre = request.form.get('titre', '').strip()
        if not titre:
            flash("Le titre est obligatoire.", 'danger')
            return redirect(url_for('demandes.nouvelle'))

        date_echeance = None
        if request.form.get('date_echeance'):
            date_echeance = datetime.strptime(request.form['date_echeance'], '%Y-%m-%d').date()

        impact = int(request.form.get('impact', 3))
        priorite = request.form.get('priorite', 'auto')
        analyse = None
        if priorite == 'auto':
            priorite, score, raisons = intelligence.analyser_priorite(
                titre, request.form.get('description', ''), impact, date_echeance)
            analyse = (priorite, score, raisons)

        d = Demande(
            titre=titre,
            description=request.form.get('description', '').strip(),
            client=request.form.get('client', '').strip(),
            localisation=request.form.get('localisation', '').strip(),
            type_intervention=request.form.get('type_intervention', 'Mécanique'),
            impact=impact,
            priorite=priorite,
            date_echeance=date_echeance,
        )
        db.session.add(d)
        db.session.commit()
        if analyse:
            flash(f"Priorité calculée automatiquement : « {analyse[0]} » "
                  f"(score IA {analyse[1]}/100).", 'info')
        flash(f"Demande #{d.id} créée avec succès.", 'success')
        return redirect(url_for('demandes.detail', demande_id=d.id))

    return render_template('demandes/form.html', types=TYPES_INTERVENTION)


@bp.route('/<int:demande_id>')
@login_required
def detail(demande_id):
    d = Demande.query.get_or_404(demande_id)
    suggestions = []
    analyse = None
    if d.statut == 'Nouvelle':
        suggestions = intelligence.scorer_techniciens(d)
        prio, score, raisons = intelligence.analyser_priorite(
            d.titre, d.description, d.impact, d.date_echeance)
        analyse = {'priorite': prio, 'score': score, 'raisons': raisons}
    return render_template('demandes/detail.html', demande=d,
                           suggestions=suggestions, analyse=analyse)


@bp.route('/<int:demande_id>/planifier', methods=['POST'])
@role_required('admin', 'planificateur')
def planifier(demande_id):
    d = Demande.query.get_or_404(demande_id)
    if d.intervention:
        flash("Cette demande est déjà planifiée.", 'warning')
        return redirect(url_for('demandes.detail', demande_id=d.id))

    technicien = Technicien.query.get_or_404(int(request.form['technicien_id']))
    date_planifiee = datetime.strptime(request.form['date_planifiee'], '%Y-%m-%d').date()

    iv = Intervention(demande_id=d.id, technicien_id=technicien.id,
                      date_planifiee=date_planifiee, statut='Planifiée')
    d.statut = 'Planifiée'
    db.session.add(iv)
    db.session.commit()
    flash(f"Intervention #{iv.id} planifiée pour {technicien.nom} "
          f"le {date_planifiee.strftime('%d/%m/%Y')}.", 'success')
    return redirect(url_for('interventions.detail', intervention_id=iv.id))


@bp.route('/<int:demande_id>/annuler', methods=['POST'])
@role_required('admin', 'planificateur')
def annuler(demande_id):
    d = Demande.query.get_or_404(demande_id)
    d.statut = 'Annulée'
    if d.intervention:
        d.intervention.statut = 'Annulée'
    db.session.commit()
    flash(f"Demande #{d.id} annulée.", 'info')
    return redirect(url_for('demandes.liste'))