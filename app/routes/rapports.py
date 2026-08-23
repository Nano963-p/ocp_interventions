# -*- coding: utf-8 -*-
"""Génération des rapports : global et par intervention."""
from flask import Blueprint, render_template
from flask_login import login_required

from .. import intelligence
from ..models import Intervention

bp = Blueprint('rapports', __name__, url_prefix='/rapports')


@bp.route('/')
@login_required
def global_report():
    terminees = (Intervention.query.filter_by(statut='Terminée')
                 .order_by(Intervention.date_fin.desc()).all())
    kpis = intelligence.calculer_kpis()
    cout_total = sum(iv.cout_pieces() for iv in terminees)
    return render_template('rapports/global.html', interventions=terminees,
                           kpis=kpis, cout_total=cout_total)


@bp.route('/intervention/<int:intervention_id>')
@login_required
def intervention_report(intervention_id):
    iv = Intervention.query.get_or_404(intervention_id)
    return render_template('rapports/intervention.html', iv=iv)