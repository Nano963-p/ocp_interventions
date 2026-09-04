# -*- coding: utf-8 -*-
"""Suivi public d'une demande par le client, via lien à token (sans compte)."""
from flask import Blueprint, abort, make_response, render_template

from ..models import Demande

bp = Blueprint('suivi', __name__, url_prefix='/suivi')


@bp.route('/<uuid:token>')
def public(token):
    d = Demande.query.filter_by(token_suivi=str(token)).first()
    if not d:
        abort(404)
    intervention = d.intervention
    public_data = {
        'titre': d.titre,
        'priorite': d.priorite,
        'statut': d.statut,
        'date_creation': d.date_creation,
        'date_planifiee': intervention.date_planifiee if intervention else None,
        'date_fin': intervention.date_fin if intervention else None,
    }
    response = make_response(render_template('suivi/public.html', demande=public_data))
    response.headers['Cache-Control'] = 'no-store, private, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Referrer-Policy'] = 'no-referrer'
    response.headers['X-Robots-Tag'] = 'noindex, nofollow, noarchive'
    return response
