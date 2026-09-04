# -*- coding: utf-8 -*-
"""Gestion du stock de pièces détachées."""
from flask import (Blueprint, flash, redirect, render_template, request,
                   url_for)

from .. import db
from ..models import Piece
from .auth import role_required
from ..validation import (flash_errors, float_value, int_value, text_value)

bp = Blueprint('stock', __name__, url_prefix='/stock')


def _parse_piece_form(form):
    """Valide et convertit les champs numériques du formulaire pièce.

    Retourne (valeurs: dict, erreurs: list[str]).
    N'ajoute rien à la session — c'est à l'appelant de créer/modifier l'objet.
    """
    erreurs = []
    valeurs = {}

    valeurs['quantite'], new_errors = int_value(
        form, 'quantite', 'La quantité', minimum=0, maximum=1000000, default=0)
    erreurs += new_errors
    valeurs['seuil_alerte'], new_errors = int_value(
        form, 'seuil_alerte', "Le seuil d'alerte", minimum=0,
        maximum=1000000, default=5)
    erreurs += new_errors
    valeurs['prix_unitaire'], new_errors = float_value(
        form, 'prix_unitaire', 'Le prix unitaire', minimum=0,
        maximum=1000000000, default=0)
    erreurs += new_errors

    return valeurs, erreurs


@bp.route('/')
@role_required('admin', 'planificateur')
def liste():
    pieces = Piece.query.order_by(Piece.nom).all()
    nb_alertes = sum(1 for p in pieces if p.en_alerte)
    return render_template('stock/liste.html', pieces=pieces, nb_alertes=nb_alertes)


@bp.route('/nouvelle', methods=['GET', 'POST'])
@role_required('admin', 'planificateur')
def nouvelle():
    if request.method == 'POST':
        valeurs, erreurs = _parse_piece_form(request.form)
        nom, new_errors = text_value(request.form, 'nom', 'La désignation',
                                     required=True, max_length=150)
        erreurs += new_errors
        reference, new_errors = text_value(request.form, 'reference', 'La référence',
                                           required=True, max_length=60)
        erreurs += new_errors
        if reference and Piece.query.filter_by(reference=reference).first():
            erreurs.append("Cette référence existe déjà.")

        if erreurs:
            for e in erreurs:
                flash(e, 'danger')
            return render_template('stock/form.html', p=None), 400

        p = Piece(
            nom=nom,
            reference=reference,
            quantite=valeurs['quantite'],
            seuil_alerte=valeurs['seuil_alerte'],
            prix_unitaire=valeurs['prix_unitaire'],
        )
        db.session.add(p)
        db.session.commit()
        flash(f"Pièce « {p.nom} » ajoutée au stock.", 'success')
        return redirect(url_for('stock.liste'))
    return render_template('stock/form.html', p=None)


@bp.route('/<int:piece_id>/modifier', methods=['GET', 'POST'])
@role_required('admin', 'planificateur')
def modifier(piece_id):
    p = db.get_or_404(Piece, piece_id)
    if request.method == 'POST':
        valeurs, erreurs = _parse_piece_form(request.form)
        nom, new_errors = text_value(request.form, 'nom', 'La désignation',
                                     required=True, max_length=150)
        erreurs += new_errors

        if erreurs:
            for e in erreurs:
                flash(e, 'danger')
            return render_template('stock/form.html', p=p), 400

        p.nom = nom
        p.quantite = valeurs['quantite']
        p.seuil_alerte = valeurs['seuil_alerte']
        p.prix_unitaire = valeurs['prix_unitaire']
        db.session.commit()
        flash(f"Pièce « {p.nom} » mise à jour.", 'success')
        return redirect(url_for('stock.liste'))
    return render_template('stock/form.html', p=p)


@bp.route('/<int:piece_id>/ajuster', methods=['POST'])
@role_required('admin', 'planificateur')
def ajuster(piece_id):
    """Ajustement rapide de quantité (réapprovisionnement)."""
    p = db.get_or_404(Piece, piece_id)
    delta, errors = int_value(request.form, 'delta', "La quantité d'ajustement",
                              minimum=1, maximum=1000000)
    if errors:
        flash_errors(flash, errors)
        return redirect(url_for('stock.liste'))
    if p.quantite + delta > 1000000:
        flash("Le stock total ne peut pas dépasser 1000000 unités.", 'danger')
        return redirect(url_for('stock.liste'))
    p.quantite += delta
    db.session.commit()
    flash(f"Stock de « {p.nom} » ajusté : {p.quantite} unité(s).", 'success')
    return redirect(url_for('stock.liste'))


@bp.route('/<int:piece_id>/supprimer', methods=['POST'])
@role_required('admin')
def supprimer(piece_id):
    p = db.get_or_404(Piece, piece_id)
    db.session.delete(p)
    db.session.commit()
    flash(f"Pièce « {p.nom} » supprimée.", 'info')
    return redirect(url_for('stock.liste'))
