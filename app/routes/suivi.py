# -*- coding: utf-8 -*-
"""Suivi public d'une demande par le client, via lien à token (sans compte)."""
from flask import Blueprint, abort, render_template

from ..models import Demande

bp = Blueprint('suivi', __name__, url_prefix='/suivi')


@bp.route('/<token>')
def public(token):
    d = Demande.query.filter_by(token_suivi=token).first()
    if not d:
        abort(404)
    return render_template('suivi/public.html', demande=d)