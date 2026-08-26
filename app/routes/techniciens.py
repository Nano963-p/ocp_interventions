# -*- coding: utf-8 -*-
"""Gestion des techniciens."""
from flask import (Blueprint, flash, redirect, render_template, request,
                   url_for)

from .. import db
from ..models import Technicien, TYPES_INTERVENTION
from .auth import role_required
from datetime import datetime
from flask_login import current_user

bp = Blueprint('techniciens', __name__, url_prefix='/techniciens')


@bp.route('/')
@role_required('admin', 'planificateur')
def liste():
    techniciens = Technicien.query.order_by(Technicien.nom).all()
    return render_template('techniciens/liste.html', techniciens=techniciens)


@bp.route('/nouveau', methods=['GET', 'POST'])
@role_required('admin', 'planificateur')
def nouveau():
    if request.method == 'POST':
        t = Technicien(
            nom=request.form.get('nom', '').strip(),
            specialite=request.form.get('specialite', '').strip(),
            zone=request.form.get('zone', 'Site Khouribga').strip(),
            telephone=request.form.get('telephone', '').strip(),
            statut=request.form.get('statut', 'disponible'),
        )
        db.session.add(t)
        db.session.commit()
        flash(f"Technicien « {t.nom} » ajouté.", 'success')
        return redirect(url_for('techniciens.liste'))
    return render_template('techniciens/form.html', t=None, types=TYPES_INTERVENTION)


@bp.route('/<int:technicien_id>/modifier', methods=['GET', 'POST'])
@role_required('admin', 'planificateur')
def modifier(technicien_id):
    t = Technicien.query.get_or_404(technicien_id)
    if request.method == 'POST':
        t.nom = request.form.get('nom', t.nom).strip()
        t.specialite = request.form.get('specialite', t.specialite).strip()
        t.zone = request.form.get('zone', t.zone).strip()
        t.telephone = request.form.get('telephone', '').strip()
        t.statut = request.form.get('statut', t.statut)
        db.session.commit()
        flash(f"Technicien « {t.nom} » mis à jour.", 'success')
        return redirect(url_for('techniciens.liste'))
    return render_template('techniciens/form.html', t=t, types=TYPES_INTERVENTION)


@bp.route('/<int:technicien_id>/supprimer', methods=['POST'])
@role_required('admin')
def supprimer(technicien_id):
    t = Technicien.query.get_or_404(technicien_id)
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
    t = Technicien.query.get_or_404(current_user.technicien_id)
    try:
        t.latitude = float(request.form['latitude'])
        t.longitude = float(request.form['longitude'])
        t.derniere_position = datetime.utcnow()
        db.session.commit()
        flash("Position mise à jour.", 'success')
    except (KeyError, ValueError):
        flash("Position invalide, réessayez.", 'danger')
    return redirect(url_for('main.dashboard'))


@bp.route('/carte')
@role_required('admin', 'planificateur')
def carte():
    techniciens = Technicien.query.filter(
        Technicien.latitude.isnot(None), Technicien.longitude.isnot(None)).all()
    return render_template('techniciens/carte.html', techniciens=techniciens)