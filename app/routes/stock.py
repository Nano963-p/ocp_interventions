# -*- coding: utf-8 -*-
"""Gestion du stock de pièces détachées."""
from flask import (Blueprint, flash, redirect, render_template, request,
                   url_for)

from .. import db
from ..models import Piece
from .auth import role_required

bp = Blueprint('stock', __name__, url_prefix='/stock')


def _parse_piece_form(form):
    """Valide et convertit les champs numériques du formulaire pièce.

    Retourne (valeurs: dict, erreurs: list[str]).
    N'ajoute rien à la session — c'est à l'appelant de créer/modifier l'objet.
    """
    erreurs = []
    valeurs = {}

    quantite_brut = form.get('quantite', '0')
    try:
        valeurs['quantite'] = int(quantite_brut)
        if valeurs['quantite'] < 0:
            erreurs.append("La quantité ne peut pas être négative.")
    except ValueError:
        erreurs.append(f"Quantité invalide : « {quantite_brut} » n'est pas un nombre entier.")

    seuil_brut = form.get('seuil_alerte', '5')
    try:
        valeurs['seuil_alerte'] = int(seuil_brut)
        if valeurs['seuil_alerte'] < 0:
            erreurs.append("Le seuil d'alerte ne peut pas être négatif.")
    except ValueError:
        erreurs.append(f"Seuil d'alerte invalide : « {seuil_brut} » n'est pas un nombre entier.")

    prix_brut = form.get('prix_unitaire', '0')
    try:
        valeurs['prix_unitaire'] = float(prix_brut) if prix_brut else 0.0
        if valeurs['prix_unitaire'] < 0:
            erreurs.append("Le prix unitaire ne peut pas être négatif.")
    except ValueError:
        erreurs.append(f"Prix unitaire invalide : « {prix_brut} » n'est pas un nombre.")

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
        reference = request.form.get('reference', '').strip()

        if not reference:
            erreurs.append("La référence est obligatoire.")
        elif Piece.query.filter_by(reference=reference).first():
            erreurs.append("Cette référence existe déjà.")

        if erreurs:
            for e in erreurs:
                flash(e, 'danger')
            return render_template('stock/form.html', p=None)

        p = Piece(
            nom=request.form.get('nom', '').strip(),
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
    p = Piece.query.get_or_404(piece_id)
    if request.method == 'POST':
        valeurs, erreurs = _parse_piece_form(request.form)

        if erreurs:
            for e in erreurs:
                flash(e, 'danger')
            return render_template('stock/form.html', p=p)

        p.nom = request.form.get('nom', p.nom).strip()
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
    p = Piece.query.get_or_404(piece_id)
    delta_brut = request.form.get('delta', '0')
    try:
        delta = int(delta_brut)
    except ValueError:
        flash(f"Valeur d'ajustement invalide : « {delta_brut} » n'est pas un nombre entier.", 'danger')
        return redirect(url_for('stock.liste'))

    p.quantite = max(0, p.quantite + delta)
    db.session.commit()
    flash(f"Stock de « {p.nom} » ajusté : {p.quantite} unité(s).", 'success')
    return redirect(url_for('stock.liste'))


@bp.route('/<int:piece_id>/supprimer', methods=['POST'])
@role_required('admin')
def supprimer(piece_id):
    p = Piece.query.get_or_404(piece_id)
    db.session.delete(p)
    db.session.commit()
    flash(f"Pièce « {p.nom} » supprimée.", 'info')
    return redirect(url_for('stock.liste'))