# -*- coding: utf-8 -*-
"""Gestion des techniciens."""
from flask import (Blueprint, flash, redirect, render_template, request,
                   url_for)

from .. import db
from ..models import Technicien, TYPES_INTERVENTION
from .auth import role_required

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