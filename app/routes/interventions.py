# -*- coding: utf-8 -*-
"""Suivi des interventions : statuts en temps réel, pièces utilisées, messages."""
from datetime import datetime

from flask import (Blueprint, abort, flash, redirect, render_template,
                   request, url_for)
from flask_login import current_user, login_required

from .. import db
from ..models import (Intervention, Message, Piece, STATUTS_INTERVENTION,
                      UtilisationPiece)

bp = Blueprint('interventions', __name__, url_prefix='/interventions')


def _liberer_technicien(technicien):
    """Repasse le technicien en « disponible » s'il n'a plus d'intervention active."""
    if technicien and technicien.statut == 'occupe' and technicien.charge_active() == 0:
        technicien.statut = 'disponible'


def _verifier_acces(iv):
    """Bloque l'accès si un technicien tente d'agir sur une intervention
    qui n'est pas la sienne (protection contre l'IDOR sur les routes POST)."""
    if (current_user.role == 'technicien'
            and current_user.technicien_id != iv.technicien_id):
        abort(403)


@bp.route('/')
@login_required
def liste():
    query = Intervention.query
    statut = request.args.get('statut', '')
    if statut:
        query = query.filter_by(statut=statut)
    if current_user.role == 'technicien' and current_user.technicien_id:
        query = query.filter_by(technicien_id=current_user.technicien_id)
    interventions = query.order_by(Intervention.date_planifiee.desc()).all()
    return render_template('interventions/liste.html', interventions=interventions,
                           statut=statut, statuts=STATUTS_INTERVENTION)


@bp.route('/<int:intervention_id>')
@login_required
def detail(intervention_id):
    iv = Intervention.query.get_or_404(intervention_id)
    if (current_user.role == 'technicien'
            and current_user.technicien_id != iv.technicien_id):
        abort(403)
    pieces = Piece.query.order_by(Piece.nom).all()
    messages = (Message.query.filter_by(intervention_id=iv.id)
                .order_by(Message.date.asc()).all())
    return render_template('interventions/detail.html', iv=iv, pieces=pieces,
                           messages=messages, statuts=STATUTS_INTERVENTION)


@bp.route('/<int:intervention_id>/statut', methods=['POST'])
@login_required
def changer_statut(intervention_id):
    iv = Intervention.query.get_or_404(intervention_id)
    _verifier_acces(iv)
    nouveau = request.form.get('statut')
    if nouveau not in STATUTS_INTERVENTION:
        flash("Statut invalide.", 'danger')
        return redirect(url_for('interventions.detail', intervention_id=iv.id))

    iv.statut = nouveau
    if nouveau == 'En cours':
        if not iv.date_debut:
            iv.date_debut = datetime.utcnow()
        iv.demande.statut = 'En cours'
        if iv.technicien:
            iv.technicien.statut = 'occupe'
    elif nouveau == 'Terminée':
        iv.date_fin = datetime.utcnow()
        iv.demande.statut = 'Terminée'
        _liberer_technicien(iv.technicien)
    elif nouveau == 'Annulée':
        iv.demande.statut = 'Annulée'
        _liberer_technicien(iv.technicien)
    elif nouveau == 'Planifiée':
        iv.demande.statut = 'Planifiée'

    db.session.commit()
    flash(f"Intervention #{iv.id} passée au statut « {nouveau} ».", 'success')
    return redirect(url_for('interventions.detail', intervention_id=iv.id))


@bp.route('/<int:intervention_id>/observations', methods=['POST'])
@login_required
def observations(intervention_id):
    iv = Intervention.query.get_or_404(intervention_id)
    _verifier_acces(iv)
    iv.observations = request.form.get('observations', '').strip()
    iv.rapport = request.form.get('rapport', '').strip()
    db.session.commit()
    flash("Observations et rapport enregistrés.", 'success')
    return redirect(url_for('interventions.detail', intervention_id=iv.id))


@bp.route('/<int:intervention_id>/piece', methods=['POST'])
@login_required
def utiliser_piece(intervention_id):
    iv = Intervention.query.get_or_404(intervention_id)
    _verifier_acces(iv)
    piece = Piece.query.get_or_404(int(request.form['piece_id']))
    quantite = max(1, int(request.form.get('quantite', 1)))

    if piece.quantite < quantite:
        flash(f"Stock insuffisant pour « {piece.nom} » "
              f"(disponible : {piece.quantite}).", 'danger')
        return redirect(url_for('interventions.detail', intervention_id=iv.id))

    piece.quantite -= quantite
    db.session.add(UtilisationPiece(intervention_id=iv.id, piece_id=piece.id,
                                    quantite=quantite))
    db.session.commit()
    flash(f"{quantite} × « {piece.nom} » prélevée(s) du stock.", 'success')
    return redirect(url_for('interventions.detail', intervention_id=iv.id))


@bp.route('/<int:intervention_id>/message', methods=['POST'])
@login_required
def envoyer_message(intervention_id):
    iv = Intervention.query.get_or_404(intervention_id)
    _verifier_acces(iv)
    contenu = request.form.get('contenu', '').strip()
    if contenu:
        db.session.add(Message(intervention_id=iv.id, user_id=current_user.id,
                               contenu=contenu))
        db.session.commit()
        flash("Message envoyé.", 'success')
    return redirect(url_for('interventions.detail', intervention_id=iv.id))