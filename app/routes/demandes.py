# -*- coding: utf-8 -*-
"""Gestion des demandes (création, score de priorité par règles, planification)."""
from flask import (Blueprint, abort, flash, redirect, render_template, request,
                   url_for)
from flask_login import current_user, login_required
from sqlalchemy import or_

from .. import db, intelligence
from ..models import Demande, Intervention, Technicien, TYPES_INTERVENTION
from .auth import can_access_demande, role_required
from ..validation import (choice_value, date_value, flash_errors, int_value,
                          text_value)

bp = Blueprint('demandes', __name__, url_prefix='/demandes')


@bp.route('/')
@login_required
def liste():
    query = Demande.query
    statut = request.args.get('statut', '')
    priorite = request.args.get('priorite', '')
    if current_user.role == 'technicien':
        if not current_user.technicien_id:
            query = query.filter(Demande.createur_id == current_user.id)
        else:
            query = query.outerjoin(Intervention).filter(or_(
                Demande.createur_id == current_user.id,
                Intervention.technicien_id == current_user.technicien_id))
    if statut in ('Nouvelle', 'Planifiée', 'En cours', 'Terminée', 'Annulée'):
        query = query.filter(Demande.statut == statut)
    if priorite in ('Basse', 'Moyenne', 'Haute', 'Critique'):
        query = query.filter(Demande.priorite == priorite)
    demandes = query.order_by(Demande.date_creation.desc()).all()
    return render_template('demandes/liste.html', demandes=demandes,
                           statut=statut, priorite=priorite)


@bp.route('/nouvelle', methods=['GET', 'POST'])
@login_required
def nouvelle():
    if request.method == 'POST':
        titre, errors = text_value(request.form, 'titre', 'Le titre', required=True,
                                   max_length=200)
        description, new_errors = text_value(
            request.form, 'description', 'La description', max_length=5000)
        errors += new_errors
        client, new_errors = text_value(request.form, 'client', 'Le client/service',
                                        required=True, max_length=120)
        errors += new_errors
        localisation, new_errors = text_value(
            request.form, 'localisation', 'La localisation', required=True,
            max_length=120)
        errors += new_errors
        date_echeance, new_errors = date_value(
            request.form, 'date_echeance', "La date d'échéance")
        errors += new_errors
        impact, new_errors = int_value(request.form, 'impact', "L'impact",
                                       minimum=1, maximum=5, default=3)
        errors += new_errors
        priorite, new_errors = choice_value(
            request.form, 'priorite', 'La priorité',
            ('auto', 'Basse', 'Moyenne', 'Haute', 'Critique'), default='auto')
        errors += new_errors
        type_intervention, new_errors = choice_value(
            request.form, 'type_intervention', "Le type d'intervention",
            TYPES_INTERVENTION, default='Mécanique')
        errors += new_errors
        if errors:
            flash_errors(flash, errors)
            return render_template('demandes/form.html', types=TYPES_INTERVENTION), 400

        analyse = None
        if priorite == 'auto':
            priorite, score, raisons = intelligence.analyser_priorite(
                titre, description, impact, date_echeance)
            analyse = (priorite, score, raisons)

        d = Demande(
            titre=titre,
            description=description,
            client=client,
            localisation=localisation,
            type_intervention=type_intervention,
            impact=impact,
            priorite=priorite,
            date_echeance=date_echeance,
            createur_id=current_user.id,
        )
        db.session.add(d)
        db.session.commit()
        if analyse:
            flash(f"Priorité calculée automatiquement : « {analyse[0]} » "
                  f"(score {analyse[1]}/100).", 'info')
        flash(f"Demande #{d.id} créée avec succès.", 'success')
        return redirect(url_for('demandes.detail', demande_id=d.id))

    return render_template('demandes/form.html', types=TYPES_INTERVENTION)


@bp.route('/<int:demande_id>')
@login_required
def detail(demande_id):
    d = db.get_or_404(Demande, demande_id)
    if not can_access_demande(d):
        abort(403)
    suggestions = []
    analyse = None
    cas_similaires = []
    if d.statut == 'Nouvelle' and current_user.is_planificateur:
        suggestions = intelligence.scorer_techniciens(d)
        prio, score, raisons = intelligence.analyser_priorite(
            d.titre, d.description, d.impact, d.date_echeance)
        analyse = {'priorite': prio, 'score': score, 'raisons': raisons}
        cas_similaires = intelligence.rechercher_cas_similaires(d)
    return render_template('demandes/detail.html', demande=d,
                           suggestions=suggestions, analyse=analyse,
                           cas_similaires=cas_similaires, synthese_ia=None)


@bp.route('/<int:demande_id>/planifier', methods=['POST'])
@role_required('admin', 'planificateur')
def planifier(demande_id):
    d = db.get_or_404(Demande, demande_id)
    if d.intervention:
        flash("Cette demande est déjà planifiée.", 'warning')
        return redirect(url_for('demandes.detail', demande_id=d.id))

    technicien_id, errors = int_value(
        request.form, 'technicien_id', 'Le technicien', minimum=1)
    date_planifiee, new_errors = date_value(
        request.form, 'date_planifiee', 'La date planifiée', required=True)
    errors += new_errors
    technicien = db.session.get(Technicien, technicien_id) if technicien_id else None
    if technicien_id and technicien is None:
        errors.append("Le technicien sélectionné n'existe pas.")
    if d.statut != 'Nouvelle':
        errors.append("Seule une demande nouvelle peut être planifiée.")
    if errors:
        flash_errors(flash, errors)
        return redirect(url_for('demandes.detail', demande_id=d.id))

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
    d = db.get_or_404(Demande, demande_id)
    d.statut = 'Annulée'
    if d.intervention:
        d.intervention.statut = 'Annulée'
    db.session.commit()
    flash(f"Demande #{d.id} annulée.", 'info')
    return redirect(url_for('demandes.liste'))


@bp.route('/<int:demande_id>/synthese-ia', methods=['POST'])
@role_required('admin', 'planificateur')
def synthese_ia(demande_id):
    d = db.get_or_404(Demande, demande_id)
    cas_similaires = intelligence.rechercher_cas_similaires(d)
    synthese = intelligence.synthetiser_recommandation_ia(d, cas_similaires)

    suggestions = intelligence.scorer_techniciens(d) if d.statut == 'Nouvelle' else []
    prio, score, raisons = intelligence.analyser_priorite(
        d.titre, d.description, d.impact, d.date_echeance)
    analyse = {'priorite': prio, 'score': score, 'raisons': raisons}

    if synthese is None:
        flash("La synthèse IA n'est pas disponible pour le moment "
              "(aucun cas suffisamment proche, ou service indisponible). "
              "Les cas similaires bruts restent consultables ci-dessous.", 'warning')
    else:
        flash("Synthèse générée à partir des cas similaires trouvés.", 'success')

    return render_template('demandes/detail.html', demande=d,
                           suggestions=suggestions, analyse=analyse,
                           cas_similaires=cas_similaires, synthese_ia=synthese)
