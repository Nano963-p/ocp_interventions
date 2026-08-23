# -*- coding: utf-8 -*-
"""
Module d'intelligence d'aide à la décision.

Fournit :
  1. Analyse automatique de la priorité d'une demande (mots-clés + impact + échéance).
  2. Suggestion d'affectation : score de chaque technicien selon compétences,
     disponibilité, charge de travail et proximité de zone.
  3. Alertes intelligentes : risques de rupture de stock, surcharge des
     techniciens, demandes à risque de dépassement d'échéance (SLA).
  4. Prévisions de consommation des pièces détachées.
"""
from datetime import date, datetime, timedelta

from . import db
from .models import (Demande, Intervention, Piece, Technicien,
                     UtilisationPiece)

# ---------------------------------------------------------------------------
# 1. Analyse automatique de la priorité
# ---------------------------------------------------------------------------

MOTS_CLES_URGENCE = {
    'urgence': 30, 'urgent': 30, 'critique': 30, 'danger': 30,
    'arrêt': 28, 'arret': 28, 'sécurité': 28, 'securite': 28,
    'panne': 25, 'fuite': 25, 'explosion': 30, 'incendie': 30,
    'bloqué': 22, 'bloque': 22, 'immobilisé': 22, 'immobilise': 22,
    'production': 15, 'casse': 18, 'cassé': 18, 'défaillance': 18,
    'defaillance': 18, 'vibration': 12, 'surchauffe': 20, 'alarme': 20,
}

SEUILS_PRIORITE = [(70, 'Critique'), (50, 'Haute'), (30, 'Moyenne'), (0, 'Basse')]


def analyser_priorite(titre, description='', impact=3, date_echeance=None):
    """Retourne (priorité, score /100, liste des raisons)."""
    score = 0
    raisons = []
    texte = ((titre or '') + ' ' + (description or '')).lower()

    for mot, pts in MOTS_CLES_URGENCE.items():
        if mot in texte:
            score += pts
            raisons.append(f"Mot-clé « {mot} » détecté (+{pts} pts)")
            break

    pts_impact = int(impact) * 5
    score += pts_impact
    raisons.append(f"Impact métier {impact}/5 (+{pts_impact} pts)")

    if date_echeance:
        jours = (date_echeance - date.today()).days
        if jours < 0:
            score += 30
            raisons.append(f"Échéance dépassée de {-jours} jour(s) (+30 pts)")
        elif jours <= 1:
            score += 30
            raisons.append("Échéance à moins de 24 h (+30 pts)")
        elif jours <= 3:
            score += 20
            raisons.append(f"Échéance dans {jours} jour(s) (+20 pts)")
        elif jours <= 7:
            score += 10
            raisons.append(f"Échéance dans {jours} jour(s) (+10 pts)")

    score = min(score, 100)
    for seuil, prio in SEUILS_PRIORITE:
        if score >= seuil:
            return prio, score, raisons
    return 'Basse', score, raisons


# ---------------------------------------------------------------------------
# 2. Suggestion d'affectation des techniciens (scoring multicritère)
# ---------------------------------------------------------------------------

def scorer_techniciens(demande):
    """
    Classe les techniciens par pertinence pour une demande.
    Score /100 = compétence (40) + disponibilité (25) + charge (25) + zone (10).
    Retourne une liste triée de dicts {technicien, score, details}.
    """
    resultats = []
    type_dem = (demande.type_intervention or '').lower()
    loc_dem = (demande.localisation or '').lower()

    for t in Technicien.query.all():
        score = 0
        details = []

        competences = [c.lower() for c in t.competences()]
        if type_dem and any(type_dem in c or c in type_dem for c in competences):
            score += 40
            details.append(f"Compétence « {demande.type_intervention} » maîtrisée (+40)")
        else:
            details.append(f"Compétence « {demande.type_intervention} » non couverte (+0)")

        if t.statut == 'disponible':
            score += 25
            details.append("Technicien disponible (+25)")
        elif t.statut == 'occupe':
            score += 10
            details.append("Technicien occupé mais joignable (+10)")
        else:
            details.append("Technicien absent (+0)")

        charge = t.charge_active()
        pts_charge = max(0, 25 - charge * 6)
        score += pts_charge
        details.append(f"Charge actuelle : {charge} intervention(s) active(s) (+{pts_charge})")

        zone = (t.zone or '').lower()
        if zone and loc_dem and (zone in loc_dem or loc_dem in zone):
            score += 10
            details.append(f"Zone « {t.zone} » correspondante (+10)")
        elif not loc_dem:
            score += 5
            details.append("Localisation non précisée (+5)")
        else:
            details.append(f"Zone différente ({t.zone}) (+0)")

        resultats.append({'technicien': t, 'score': min(score, 100),
                          'charge': charge, 'details': details})

    resultats.sort(key=lambda r: r['score'], reverse=True)
    return resultats


# ---------------------------------------------------------------------------
# 3. Alertes intelligentes
# ---------------------------------------------------------------------------

def generer_alertes():
    """Génère la liste des alertes décisionnelles (dicts {niveau, titre, message, lien})."""
    alertes = []
    today = date.today()

    for p in Piece.query.filter(Piece.quantite <= Piece.seuil_alerte).all():
        niveau = 'danger' if p.quantite <= max(1, p.seuil_alerte // 2) else 'warning'
        alertes.append({
            'niveau': niveau,
            'titre': f"Stock critique : {p.nom}",
            'message': f"Quantité restante : {p.quantite} (seuil : {p.seuil_alerte}). "
                       f"Réapprovisionnement recommandé.",
            'lien': '/stock',
        })

    for d in Demande.query.filter(Demande.statut == 'Nouvelle',
                                  Demande.date_echeance != None).all():  # noqa: E711
        jours = d.jours_restants
        if jours is not None and jours <= 3:
            alertes.append({
                'niveau': 'danger' if jours < 0 else 'warning',
                'titre': f"Risque SLA : demande #{d.id}",
                'message': f"« {d.titre} » non planifiée, échéance "
                           f"{'dépassée' if jours < 0 else 'dans ' + str(jours) + ' j'}.",
                'lien': f"/demandes/{d.id}",
            })

    for t in Technicien.query.all():
        charge = t.charge_active()
        if charge >= 4:
            alertes.append({
                'niveau': 'warning',
                'titre': f"Surcharge : {t.nom}",
                'message': f"{charge} interventions actives. Envisager une réaffectation.",
                'lien': '/techniciens',
            })

    for iv in Intervention.query.filter(
            Intervention.statut == 'Planifiée',
            Intervention.date_planifiee < today).all():
        alertes.append({
            'niveau': 'danger',
            'titre': f"Intervention #{iv.id} en retard",
            'message': f"Planifiée le {iv.date_planifiee.strftime('%d/%m/%Y')} "
                       f"pour « {iv.demande.titre} » et toujours non démarrée.",
            'lien': f"/interventions/{iv.id}",
        })

    ordre = {'danger': 0, 'warning': 1, 'info': 2}
    alertes.sort(key=lambda a: ordre.get(a['niveau'], 3))
    return alertes


# ---------------------------------------------------------------------------
# 4. Prévisions de consommation des pièces
# ---------------------------------------------------------------------------

def previsions_stock():
    """
    Pour chaque pièce : consommation moyenne par intervention (30 derniers jours)
    et estimation du nombre d'interventions encore couvertes par le stock.
    """
    previsions = []
    limite = datetime.utcnow() - timedelta(days=30)
    nb_interv = max(Intervention.query.filter(Intervention.date_debut >= limite).count(), 1)

    for p in Piece.query.all():
        conso_30j = (db.session.query(db.func.coalesce(db.func.sum(UtilisationPiece.quantite), 0))
                     .filter(UtilisationPiece.piece_id == p.id,
                             UtilisationPiece.date >= limite).scalar())
        conso_par_interv = round(conso_30j / nb_interv, 2)
        if conso_par_interv > 0:
            interv_couvertes = int(p.quantite / conso_par_interv)
        else:
            interv_couvertes = None
        risque = 'Élevé' if (interv_couvertes is not None and interv_couvertes < 5) else \
                 ('Moyen' if (interv_couvertes is not None and interv_couvertes < 15) else 'Faible')
        previsions.append({
            'piece': p,
            'conso_30j': int(conso_30j),
            'conso_par_interv': conso_par_interv,
            'interv_couvertes': interv_couvertes,
            'risque': risque,
        })
    previsions.sort(key=lambda x: (x['interv_couvertes'] is None,
                                   x['interv_couvertes'] or 9999))
    return previsions


# ---------------------------------------------------------------------------
# 5. Recommandations d'affectation automatiques
# ---------------------------------------------------------------------------

def recommandations_affectation():
    """Pour chaque demande « Nouvelle », propose le meilleur technicien disponible."""
    recos = []
    for d in Demande.query.filter_by(statut='Nouvelle') \
                          .order_by(Demande.date_echeance.asc().nullslast(),
                                    Demande.date_creation.asc()).all():
        scores = scorer_techniciens(d)
        if scores:
            prio_auto, score_prio, _ = analyser_priorite(
                d.titre, d.description, d.impact, d.date_echeance)
            recos.append({
                'demande': d,
                'meilleur': scores[0],
                'alternatives': scores[1:3],
                'priorite_suggeree': prio_auto,
                'score_priorite': score_prio,
            })
    recos.sort(key=lambda r: r['score_priorite'], reverse=True)
    return recos


# ---------------------------------------------------------------------------
# 6. Indicateurs clés (KPI)
# ---------------------------------------------------------------------------

def calculer_kpis():
    total = Intervention.query.count()
    terminees = Intervention.query.filter_by(statut='Terminée').count()
    taux_resolution = round(100 * terminees / total, 1) if total else 0

    durees = [iv.duree_heures() for iv in Intervention.query.filter_by(statut='Terminée').all()
              if iv.duree_heures() is not None]
    duree_moyenne = round(sum(durees) / len(durees), 1) if durees else 0

    demandes_retard = sum(1 for d in Demande.query.all() if d.en_retard)
    nb_demandes = Demande.query.count()
    taux_retard = round(100 * demandes_retard / nb_demandes, 1) if nb_demandes else 0

    return {
        'taux_resolution': taux_resolution,
        'duree_moyenne': duree_moyenne,
        'taux_retard': taux_retard,
        'nb_demandes_retard': demandes_retard,
    }