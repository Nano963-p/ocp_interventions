# -*- coding: utf-8 -*-
"""Gestion des techniciens."""
from flask import (Blueprint, flash, redirect, render_template, request,
                   url_for)

from .. import db
from ..models import Technicien, TYPES_INTERVENTION, utcnow
from .auth import role_required
from flask_login import current_user
from ..validation import (choice_value, flash_errors, float_value, text_value)

bp = Blueprint('techniciens', __name__, url_prefix='/techniciens')
STATUTS_TECHNICIEN = ('disponible', 'occupe', 'absent')


def _parse_technicien_form(form, existing=None):
    nom, errors = text_value(form, 'nom', 'Le nom', required=True, max_length=120)
    zone, new_errors = text_value(form, 'zone', "La zone d'affectation",
                                  required=True, max_length=120)
    errors += new_errors
    telephone, new_errors = text_value(form, 'telephone', 'Le téléphone',
                                       max_length=30)
    errors += new_errors
    statut, new_errors = choice_value(
        form, 'statut', 'La disponibilité', STATUTS_TECHNICIEN,
        default=existing.statut if existing else 'disponible')
    errors += new_errors
    raw_specialites = [item.strip() for item in form.get('specialite', '').split(',')
                       if item.strip()]
    invalides = [item for item in raw_specialites if item not in TYPES_INTERVENTION]
    if not raw_specialites:
        errors.append("Au moins une spécialité reconnue est obligatoire.")
    if invalides:
        errors.append("Spécialité invalide. Utilisez uniquement les types proposés.")
    specialite = ', '.join(raw_specialites)
    if len(specialite) > 200:
        errors.append("Les spécialités ne peuvent pas dépasser 200 caractères.")
    return {'nom': nom, 'zone': zone, 'telephone': telephone,
            'statut': statut, 'specialite': specialite}, errors


@bp.route('/')
@role_required('admin', 'planificateur')
def liste():
    techniciens = Technicien.query.order_by(Technicien.nom).all()
    return render_template('techniciens/liste.html', techniciens=techniciens)


@bp.route('/nouveau', methods=['GET', 'POST'])
@role_required('admin', 'planificateur')
def nouveau():
    if request.method == 'POST':
        values, errors = _parse_technicien_form(request.form)
        if errors:
            flash_errors(flash, errors)
            return render_template('techniciens/form.html', t=None,
                                   types=TYPES_INTERVENTION), 400
        t = Technicien(
            **values,
        )
        db.session.add(t)
        db.session.commit()
        flash(f"Technicien « {t.nom} » ajouté.", 'success')
        return redirect(url_for('techniciens.liste'))
    return render_template('techniciens/form.html', t=None, types=TYPES_INTERVENTION)


@bp.route('/<int:technicien_id>/modifier', methods=['GET', 'POST'])
@role_required('admin', 'planificateur')
def modifier(technicien_id):
    t = db.get_or_404(Technicien, technicien_id)
    if request.method == 'POST':
        values, errors = _parse_technicien_form(request.form, t)
        if errors:
            flash_errors(flash, errors)
            return render_template('techniciens/form.html', t=t,
                                   types=TYPES_INTERVENTION), 400
        for key, value in values.items():
            setattr(t, key, value)
        db.session.commit()
        flash(f"Technicien « {t.nom} » mis à jour.", 'success')
        return redirect(url_for('techniciens.liste'))
    return render_template('techniciens/form.html', t=t, types=TYPES_INTERVENTION)


@bp.route('/<int:technicien_id>/supprimer', methods=['POST'])
@role_required('admin')
def supprimer(technicien_id):
    t = db.get_or_404(Technicien, technicien_id)
    if t.charge_active() > 0:
        flash(f"Impossible de supprimer « {t.nom} » : interventions actives.", 'danger')
        return redirect(url_for('techniciens.liste'))
    db.session.delete(t)
    db.session.commit()
    flash(f"Technicien « {t.nom} » supprimé.", 'info')
    return redirect(url_for('techniciens.liste'))

@bp.route('/ma-position', methods=['POST'])
@role_required('technicien')
def maj_position():
    """Le technicien connecté met à jour sa position GPS (via géolocalisation navigateur)."""
    if not current_user.technicien_id:
        flash("Aucune fiche technicien associée à ce compte.", 'danger')
        return redirect(url_for('main.dashboard'))
    t = db.get_or_404(Technicien, current_user.technicien_id)
    latitude, errors = float_value(request.form, 'latitude', 'La latitude',
                                   minimum=-90, maximum=90)
    longitude, new_errors = float_value(request.form, 'longitude', 'La longitude',
                                        minimum=-180, maximum=180)
    errors += new_errors
    if errors:
        flash_errors(flash, errors)
        return redirect(url_for('main.dashboard'))
    t.latitude = latitude
    t.longitude = longitude
    t.derniere_position = utcnow()
    db.session.commit()
    flash("Position mise à jour.", 'success')
    return redirect(url_for('main.dashboard'))


@bp.route('/carte')
@role_required('admin', 'planificateur')
def carte():
    techniciens = Technicien.query.filter(
        Technicien.latitude.isnot(None), Technicien.longitude.isnot(None)).all()
    return render_template('techniciens/carte.html', techniciens=techniciens)
