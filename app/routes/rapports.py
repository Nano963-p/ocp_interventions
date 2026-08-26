# -*- coding: utf-8 -*-
"""Génération des rapports : global et par intervention (web + PDF)."""
from datetime import datetime
from io import BytesIO

from flask import Blueprint, Response, flash, redirect, render_template, url_for
from flask_login import login_required
from xhtml2pdf import pisa

from .. import intelligence
from ..models import Intervention

bp = Blueprint('rapports', __name__, url_prefix='/rapports')


def _generer_pdf(template_name, **context):
    """Rend un template Jinja en PDF. Retourne les octets du PDF, ou None en cas d'échec."""
    html = render_template(template_name, **context)
    resultat = BytesIO()
    pdf = pisa.CreatePDF(html, dest=resultat, encoding='utf-8')
    if pdf.err:
        return None
    return resultat.getvalue()


@bp.route('/')
@login_required
def global_report():
    terminees = (Intervention.query.filter_by(statut='Terminée')
                 .order_by(Intervention.date_fin.desc()).all())
    kpis = intelligence.calculer_kpis()
    cout_total = sum(iv.cout_pieces() for iv in terminees)
    return render_template('rapports/global.html', interventions=terminees,
                           kpis=kpis, cout_total=cout_total)


@bp.route('/pdf')
@login_required
def global_report_pdf():
    terminees = (Intervention.query.filter_by(statut='Terminée')
                 .order_by(Intervention.date_fin.desc()).all())
    kpis = intelligence.calculer_kpis()
    cout_total = sum(iv.cout_pieces() for iv in terminees)
    pdf_bytes = _generer_pdf('rapports/global_pdf.html', interventions=terminees,
                             kpis=kpis, cout_total=cout_total,
                             date_generation=datetime.now().strftime('%d/%m/%Y %H:%M'))
    if pdf_bytes is None:
        flash("Erreur lors de la génération du PDF.", 'danger')
        return redirect(url_for('rapports.global_report'))
    return Response(pdf_bytes, mimetype='application/pdf', headers={
        'Content-Disposition': 'inline; filename=rapport_global_interventions.pdf'
    })


@bp.route('/intervention/<int:intervention_id>')
@login_required
def intervention_report(intervention_id):
    iv = Intervention.query.get_or_404(intervention_id)
    return render_template('rapports/intervention.html', iv=iv)


@bp.route('/intervention/<int:intervention_id>/pdf')
@login_required
def intervention_report_pdf(intervention_id):
    iv = Intervention.query.get_or_404(intervention_id)
    pdf_bytes = _generer_pdf('rapports/intervention_pdf.html', iv=iv)
    if pdf_bytes is None:
        flash("Erreur lors de la génération du PDF.", 'danger')
        return redirect(url_for('rapports.intervention_report', intervention_id=iv.id))
    return Response(pdf_bytes, mimetype='application/pdf', headers={
        'Content-Disposition': f'inline; filename=rapport_intervention_{iv.id}.pdf'
    })