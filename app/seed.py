# -*- coding: utf-8 -*-
"""Données de démonstration chargées au premier démarrage."""
from datetime import date, datetime, timedelta

from . import db
from .models import (Demande, Intervention, Message, Piece, Technicien, User,
                     UtilisationPiece)


def seed_if_empty():
    if User.query.count() > 0:
        return

    today = date.today()

    # ---------- Techniciens ----------
    t1 = Technicien(nom='Ahmed Hakim', specialite='Mécanique, Hydraulique',
                    zone='Zone Nord', telephone='0601-111111', statut='disponible')
    t2 = Technicien(nom='Youssef Idrissi', specialite='Électrique, Instrumentation',
                    zone='Zone Sud', telephone='0602-222222', statut='disponible')
    t3 = Technicien(nom='Karim Alaoui', specialite='Informatique',
                    zone='Site Khouribga', telephone='0603-333333', statut='disponible')
    t4 = Technicien(nom='Said Tazi', specialite='Mécanique',
                    zone='Zone Nord', telephone='0604-444444', statut='occupe')
    t5 = Technicien(nom='Fatima Zahra Amar', specialite='Hydraulique, Instrumentation',
                    zone='Zone Sud', telephone='0605-555555', statut='disponible')
    db.session.add_all([t1, t2, t3, t4, t5])
    db.session.flush()

    # ---------- Utilisateurs ----------
    admin = User(username='admin', nom='Administrateur', role='admin')
    admin.set_password('admin123')
    planif = User(username='planif', nom='Planificateur OCP', role='planificateur')
    planif.set_password('planif123')
    tech = User(username='ahmed', nom='Ahmed Hakim', role='technicien', technicien_id=t1.id)
    tech.set_password('tech123')
    db.session.add_all([admin, planif, tech])

    # ---------- Pièces détachées ----------
    p1 = Piece(nom='Roulement SKF 6208', reference='RLT-6208', quantite=40,
               seuil_alerte=10, prix_unitaire=180.0)
    p2 = Piece(nom='Joint hydraulique DN50', reference='JNT-DN50', quantite=6,
               seuil_alerte=8, prix_unitaire=95.0)
    p3 = Piece(nom='Disjoncteur 32A', reference='DSJ-32A', quantite=25,
               seuil_alerte=5, prix_unitaire=240.0)
    p4 = Piece(nom='Courroie de transmission B-1800', reference='CRB-1800', quantite=12,
               seuil_alerte=4, prix_unitaire=320.0)
    p5 = Piece(nom='Capteur de pression 4-20mA', reference='CPT-420', quantite=3,
               seuil_alerte=4, prix_unitaire=750.0)
    db.session.add_all([p1, p2, p3, p4, p5])
    db.session.flush()

    # ---------- Demandes + interventions ----------
    def mk_demande(titre, desc, client, loc, type_i, impact, prio, statut,
                   cree_il_y_a, echeance_dans=None):
        d = Demande(titre=titre, description=desc, client=client, localisation=loc,
                    type_intervention=type_i, impact=impact, priorite=prio,
                    statut=statut, date_creation=datetime.utcnow() - timedelta(days=cree_il_y_a),
                    date_echeance=(today + timedelta(days=echeance_dans)) if echeance_dans is not None else None)
        db.session.add(d)
        db.session.flush()
        return d

    def mk_intervention(demande, technicien, planifiee_il_y_a, statut, duree_h=None):
        iv = Intervention(demande_id=demande.id, technicien_id=technicien.id,
                          date_planifiee=today - timedelta(days=planifiee_il_y_a),
                          statut=statut)
        if statut in ('En cours', 'Terminée'):
            iv.date_debut = datetime.utcnow() - timedelta(days=planifiee_il_y_a, hours=2)
        if statut == 'Terminée':
            iv.date_fin = iv.date_debut + timedelta(hours=duree_h or 3)
            iv.observations = 'Intervention réalisée conformément au planning.'
            iv.rapport = 'Diagnostic effectué, pièce remplacée, essais concluants.'
        db.session.add(iv)
        db.session.flush()
        return iv

    # Terminées (historique pour les graphiques et le rapport global)
    d1 = mk_demande('Panne convoyeur bande CV-12', 'Arrêt complet du convoyeur, panne moteur détectée.',
                    'Atelier Lavage', 'Zone Nord', 'Mécanique', 5, 'Critique', 'Terminée', 75)
    iv1 = mk_intervention(d1, t1, 74, 'Terminée', 5)
    db.session.add_all([UtilisationPiece(intervention_id=iv1.id, piece_id=p1.id, quantite=2,
                                         date=iv1.date_fin),
                        UtilisationPiece(intervention_id=iv1.id, piece_id=p4.id, quantite=1,
                                         date=iv1.date_fin)])

    d2 = mk_demande('Remplacement disjoncteur armoire T2', 'Disjoncteur défaillant, coupures répétées.',
                    'Poste Électrique', 'Zone Sud', 'Électrique', 4, 'Haute', 'Terminée', 55)
    iv2 = mk_intervention(d2, t2, 54, 'Terminée', 2)
    db.session.add(UtilisationPiece(intervention_id=iv2.id, piece_id=p3.id, quantite=1,
                                    date=iv2.date_fin))

    d3 = mk_demande('Fuite circuit hydraulique presse P-07', 'Fuite détectée sur le vérin principal.',
                    'Atelier Presses', 'Zone Sud', 'Hydraulique', 4, 'Haute', 'Terminée', 40)
    iv3 = mk_intervention(d3, t5, 39, 'Terminée', 4)
    db.session.add(UtilisationPiece(intervention_id=iv3.id, piece_id=p2.id, quantite=3,
                                    date=iv3.date_fin))

    d4 = mk_demande('Mise à jour poste de supervision', 'Migration du logiciel de supervision salle contrôle.',
                    'Salle de Contrôle', 'Site Khouribga', 'Informatique', 2, 'Basse', 'Terminée', 30)
    mk_intervention(d4, t3, 29, 'Terminée', 3)

    d5 = mk_demande('Vibration anormale broyeur BR-3', 'Vibration excessive sur le palier côté moteur.',
                    'Atelier Broyage', 'Zone Nord', 'Mécanique', 4, 'Haute', 'Terminée', 18)
    iv5 = mk_intervention(d5, t4, 17, 'Terminée', 6)
    db.session.add_all([UtilisationPiece(intervention_id=iv5.id, piece_id=p1.id, quantite=2,
                                         date=iv5.date_fin),
                        UtilisationPiece(intervention_id=iv5.id, piece_id=p2.id, quantite=1,
                                         date=iv5.date_fin)])

    d6 = mk_demande('Capteur pression ligne L-9 HS', 'Signal 4-20mA instable, capteur défaillance probable.',
                    'Unité Granulation', 'Zone Sud', 'Instrumentation', 3, 'Moyenne', 'Terminée', 10)
    iv6 = mk_intervention(d6, t2, 9, 'Terminée', 2)
    db.session.add(UtilisationPiece(intervention_id=iv6.id, piece_id=p5.id, quantite=1,
                                    date=iv6.date_fin))

    # En cours / planifiées
    d7 = mk_demande('Surchauffe moteur pompe P-114', 'Surchauffe alarme thermique moteur principal.',
                    'Station Pompage', 'Zone Nord', 'Électrique', 5, 'Critique', 'En cours', 3, 2)
    mk_intervention(d7, t2, 1, 'En cours')

    d8 = mk_demande('Maintenance préventive convoyeur CV-20', 'Graissage et contrôle des roulements.',
                    'Atelier Lavage', 'Zone Nord', 'Mécanique', 2, 'Moyenne', 'Planifiée', 2, 6)
    mk_intervention(d8, t1, -1, 'Planifiée')  # demain

    d9 = mk_demande('Contrôle réseau atelier sud', 'Latences réseau signalées par les opérateurs.',
                    'Atelier Sud', 'Zone Sud', 'Informatique', 3, 'Moyenne', 'Planifiée', 1, 5)
    mk_intervention(d9, t3, -2, 'Planifiée')  # après-demain

    # Nouvelles (pour tester l'aide à la décision)
    mk_demande('Panne urgente ventilateur tour refroidissement',
               'Arrêt urgent du ventilateur principal, risque pour la production.',
               'Tour Refroidissement', 'Zone Nord', 'Mécanique', 5, 'Haute', 'Nouvelle', 0, 2)
    mk_demande('Alarme capteur niveau bac B-22',
               'Alarme niveau bas persistante, capteur pression suspect.',
               'Unité Granulation', 'Zone Sud', 'Instrumentation', 4, 'Moyenne', 'Nouvelle', 0, 4)
    mk_demande('Fuite hydraulique presse P-11',
               'Fuite hydraulique détectée au niveau du distributeur.',
               'Atelier Presses', 'Zone Sud', 'Hydraulique', 4, 'Moyenne', 'Nouvelle', 1, 3)
    mk_demande('Lenteur application GMAO poste accueil',
               'Application lente au démarrage depuis la dernière mise à jour.',
               'Bureau Accueil', 'Site Khouribga', 'Informatique', 1, 'Basse', 'Nouvelle', 1, 12)

    # Messages de démonstration
    db.session.add_all([
        Message(intervention_id=iv1.id, user_id=2,
                contenu="Merci de vérifier l'alignement avant remise en route.",
                date=datetime.utcnow() - timedelta(days=73, hours=5)),
        Message(intervention_id=iv1.id, user_id=3,
                contenu="Alignement contrôlé, essai de rotation OK. Intervention terminée.",
                date=datetime.utcnow() - timedelta(days=73, hours=3)),
    ])

    db.session.commit()
    