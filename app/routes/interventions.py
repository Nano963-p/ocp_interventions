# -*- coding: utf-8 -*-
"""Suivi opérationnel des interventions, pièces utilisées et messages."""
from flask import (Blueprint, abort, flash, redirect, render_template,
                   request, url_for)
from flask_login import current_user, login_required
from sqlalchemy import update

from .. import db
from ..models import (Intervention, Message, Piece, Technicien,
                      STATUTS_INTERVENTION, UtilisationPiece, utcnow)

from .auth import can_access_intervention, role_required
from ..validation import flash_errors, int_value, text_value

bp = Blueprint('interventions', __name__, url_prefix='/interventions')


def _liberer_technicien(technicien):
    """Repasse le technicien en « disponible » s'il n'a plus d'intervention active."""
    if technicien and technicien.statut == 'occupe' and technicien.charge_active() == 0:
        technicien.statut = 'disponible'


def _verifier_acces(iv):
    """Bloque l'accès si un technicien tente d'agir sur une intervention
    qui n'est pas la sienne (protection contre l'IDOR sur les routes POST)."""
    if not can_access_intervention(iv):
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
    iv = db.get_or_404(Intervention, intervention_id)
    if not can_access_intervention(iv):
        abort(403)
    pieces = (Piece.query.order_by(Piece.nom).all()
              if current_user.is_planificateur or iv.statut == 'En cours' else [])
    techniciens = (Technicien.query.order_by(Technicien.nom).all()
                   if current_user.is_planificateur else [])
    messages = (Message.query.filter_by(intervention_id=iv.id)
                .order_by(Message.date.asc()).all())
    return render_template('interventions/detail.html', iv=iv, pieces=pieces,
                           techniciens=techniciens, messages=messages,
                           statuts=STATUTS_INTERVENTION)


@bp.route('/<int:intervention_id>/statut', methods=['POST'])
@login_required
def changer_statut(intervention_id):
    iv = db.get_or_404(Intervention, intervention_id)
    _verifier_acces(iv)
    nouveau = request.form.get('statut', '')
    if nouveau not in STATUTS_INTERVENTION:
        flash("Statut invalide.", 'danger')
        return redirect(url_for('interventions.detail', intervention_id=iv.id))

    transitions = {
        'Planifiée': {'En cours', 'Annulée'},
        'En cours': {'Terminée', 'Annulée'},
        'Terminée': set(),
        'Annulée': set(),
    }
    if nouveau != iv.statut and nouveau not in transitions.get(iv.statut, set()):
        flash(f"Transition de « {iv.statut} » vers « {nouveau} » interdite.", 'danger')
        return redirect(url_for('interventions.detail', intervention_id=iv.id))
    if nouveau == iv.statut:
        flash("L'intervention a déjà ce statut.", 'info')
        return redirect(url_for('interventions.detail', intervention_id=iv.id))

    iv.statut = nouveau
    if nouveau == 'En cours':
        if not iv.date_debut:
            iv.date_debut = utcnow()
        iv.demande.statut = 'En cours'
        if iv.technicien:
            iv.technicien.statut = 'occupe'
    elif nouveau == 'Terminée':
        iv.date_fin = utcnow()
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


@bp.route('/<int:intervention_id>/reaffecter', methods=['POST'])
@role_required('admin', 'planificateur')
def reaffecter(intervention_id):
    iv = db.get_or_404(Intervention, intervention_id)
    if iv.statut in ('Terminée', 'Annulée'):
        flash("Impossible de réaffecter une intervention terminée ou annulée.", 'danger')
        return redirect(url_for('interventions.detail', intervention_id=iv.id))

    technicien_id, errors = int_value(
        request.form, 'technicien_id', 'Le technicien', minimum=1)
    nouveau_technicien = (db.session.get(Technicien, technicien_id)
                          if technicien_id else None)
    if technicien_id and nouveau_technicien is None:
        errors.append("Le technicien sélectionné n'existe pas.")
    if errors:
        flash_errors(flash, errors)
        return redirect(url_for('interventions.detail', intervention_id=iv.id))
    if nouveau_technicien.id == iv.technicien_id:
        flash("Cette intervention est déjà affectée à ce technicien.", 'warning')
        return redirect(url_for('interventions.detail', intervention_id=iv.id))

    ancien_technicien = iv.technicien
    iv.technicien_id = nouveau_technicien.id
    db.session.commit()

    # Libère l'ancien technicien s'il n'a plus de charge active,
    # marque le nouveau comme occupé si l'intervention est déjà en cours.
    _liberer_technicien(ancien_technicien)
    if iv.statut == 'En cours':
        nouveau_technicien.statut = 'occupe'
    db.session.commit()

    flash(f"Intervention #{iv.id} réaffectée de "
          f"{ancien_technicien.nom if ancien_technicien else '—'} à {nouveau_technicien.nom}.", 'success')
    return redirect(url_for('interventions.detail', intervention_id=iv.id))



@bp.route('/<int:intervention_id>/observations', methods=['POST'])
@login_required
def observations(intervention_id):
    iv = db.get_or_404(Intervention, intervention_id)
    _verifier_acces(iv)
    observations, errors = text_value(
        request.form, 'observations', 'Les observations', max_length=10000)
    rapport, new_errors = text_value(
        request.form, 'rapport', 'Le rapport', max_length=10000)
    errors += new_errors
    if errors:
        flash_errors(flash, errors)
        return redirect(url_for('interventions.detail', intervention_id=iv.id))
    iv.observations = observations
    iv.rapport = rapport
    db.session.commit()
    flash("Observations et rapport enregistrés.", 'success')
    return redirect(url_for('interventions.detail', intervention_id=iv.id))


@bp.route('/<int:intervention_id>/piece', methods=['POST'])
@login_required
def utiliser_piece(intervention_id):
    iv = db.get_or_404(Intervention, intervention_id)
    _verifier_acces(iv)

    if iv.statut != 'En cours':
        flash("Le prélèvement de pièces n'est possible que sur une intervention "
              "en cours.", 'warning')
        return redirect(url_for('interventions.detail', intervention_id=iv.id))

    piece_id, errors = int_value(request.form, 'piece_id', 'La pièce', minimum=1)
    quantite, new_errors = int_value(
        request.form, 'quantite', 'La quantité', minimum=1, maximum=100000,
        default=1)
    errors += new_errors
    piece = db.session.get(Piece, piece_id) if piece_id else None
    if piece_id and piece is None:
        errors.append("La pièce sélectionnée n'existe pas.")
    if errors:
        flash_errors(flash, errors)
        return redirect(url_for('interventions.detail', intervention_id=iv.id))

    result = db.session.execute(
        update(Piece)
        .where(Piece.id == piece.id, Piece.quantite >= quantite)
        .values(quantite=Piece.quantite - quantite)
    )
    if result.rowcount != 1:
        db.session.rollback()
        flash(f"Stock insuffisant pour « {piece.nom} » "
              f"(disponible : {piece.quantite}).", 'danger')
        return redirect(url_for('interventions.detail', intervention_id=iv.id))

    db.session.add(UtilisationPiece(intervention_id=iv.id, piece_id=piece.id,
                                    quantite=quantite))
    db.session.commit()
    flash(f"{quantite} × « {piece.nom} » prélevée(s) du stock.", 'success')
    return redirect(url_for('interventions.detail', intervention_id=iv.id))


@bp.route('/<int:intervention_id>/piece/<int:utilisation_id>/annuler', methods=['POST'])
@login_required
def annuler_piece(intervention_id, utilisation_id):
    iv = db.get_or_404(Intervention, intervention_id)
    _verifier_acces(iv)

    if iv.statut != 'En cours':
        flash("Un prélèvement ne peut être annulé que pendant une intervention en cours. "
              "Ajustez le stock manuellement si nécessaire.", 'danger')
        return redirect(url_for('interventions.detail', intervention_id=iv.id))

    utilisation = db.get_or_404(UtilisationPiece, utilisation_id)
    if utilisation.intervention_id != iv.id:
        abort(404)

    # Restitue la quantité au stock et supprime la trace
    utilisation.piece.quantite += utilisation.quantite
    nom_piece = utilisation.piece.nom
    qte = utilisation.quantite
    db.session.delete(utilisation)
    db.session.commit()

    flash(f"Prélèvement annulé : {qte} × « {nom_piece} » remise(s) en stock.", 'success')
    return redirect(url_for('interventions.detail', intervention_id=iv.id))


@bp.route('/<int:intervention_id>/message', methods=['POST'])
@login_required
def envoyer_message(intervention_id):
    iv = db.get_or_404(Intervention, intervention_id)
    _verifier_acces(iv)
    contenu, errors = text_value(request.form, 'contenu', 'Le message',
                                 required=True, max_length=2000)
    if errors:
        flash_errors(flash, errors)
        return redirect(url_for('interventions.detail', intervention_id=iv.id))
    db.session.add(Message(intervention_id=iv.id, user_id=current_user.id,
                           contenu=contenu))
    db.session.commit()
    flash("Message envoyé.", 'success')
    return redirect(url_for('interventions.detail', intervention_id=iv.id))
