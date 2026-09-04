# -*- coding: utf-8 -*-
"""Jeu entièrement fictif/synthétique, réservé au mode de démonstration local.

Les noms, téléphones, lieux, équipements, interventions et rapports ci-dessous
ne décrivent aucune personne, installation ou opération réelle d'OCP.
"""
from datetime import date, timedelta

from flask import current_app

from . import db
from .models import (Demande, Intervention, Message, Piece, Technicien, User,
                     UtilisationPiece, utcnow)


def seed_if_empty():
    if not current_app.config.get('DEMO_MODE'):
        raise RuntimeError("Le seed synthétique nécessite DEMO_MODE=1.")
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
                    statut=statut, date_creation=utcnow() - timedelta(days=cree_il_y_a),
                    date_echeance=(today + timedelta(days=echeance_dans)) if echeance_dans is not None else None,
                    createur_id=admin.id)
        db.session.add(d)
        db.session.flush()
        return d

    def mk_intervention(demande, technicien, planifiee_il_y_a, statut, duree_h=None,
                        observations_txt=None, rapport_txt=None):
        iv = Intervention(demande_id=demande.id, technicien_id=technicien.id,
                          date_planifiee=today - timedelta(days=planifiee_il_y_a),
                          statut=statut)
        if statut in ('En cours', 'Terminée'):
            iv.date_debut = utcnow() - timedelta(days=planifiee_il_y_a, hours=2)
        if statut == 'Terminée':
            iv.date_fin = iv.date_debut + timedelta(hours=duree_h or 3)
            iv.observations = observations_txt or 'Intervention réalisée conformément au planning.'
            iv.rapport = rapport_txt or 'Diagnostic effectué, pièce remplacée, essais concluants.'
        db.session.add(iv)
        db.session.flush()
        return iv

    # Terminées (historique pour les graphiques et le rapport global)
    d1 = mk_demande('Panne convoyeur bande CV-12', 'Arrêt complet du convoyeur, panne moteur détectée.',
                    'Atelier Lavage', 'Zone Nord', 'Mécanique', 5, 'Critique', 'Terminée', 75)
    iv1 = mk_intervention(d1, t1, 74, 'Terminée', 5,
        observations_txt="Moteur du convoyeur CV-12 en surchauffe, odeur de brûlé constatée. "
                         "Roulements côté entraînement fortement usés, jeu axial excessif détecté "
                         "au démontage. Courroie de transmission également fissurée sur toute sa longueur.",
        rapport_txt="Remplacement des deux roulements côté entraînement (SKF 6208) et de la courroie "
                    "de transmission. Alignement du moteur vérifié et corrigé. Essai de rotation à vide "
                    "concluant, aucune vibration résiduelle. Convoyeur remis en service normal.")

    d2 = mk_demande('Remplacement disjoncteur armoire T2', 'Disjoncteur défaillant, coupures répétées.',
                    'Poste Électrique', 'Zone Sud', 'Électrique', 4, 'Haute', 'Terminée', 55)
    iv2 = mk_intervention(d2, t2, 54, 'Terminée', 2,
        observations_txt="Coupures électriques répétées sur l'armoire T2, déclenchement intempestif "
                         "du disjoncteur principal 32A. Trace de noircissement visible sur les bornes "
                         "de raccordement, signe probable d'un échauffement local.",
        rapport_txt="Disjoncteur 32A remplacé après confirmation du défaut (résistance de contact "
                    "anormale mesurée). Bornes de raccordement nettoyées et resserrées au couple. "
                    "Test de déclenchement effectué, calibrage conforme. Aucune coupure depuis.")

    d3 = mk_demande('Fuite circuit hydraulique presse P-07', 'Fuite détectée sur le vérin principal.',
                    'Atelier Presses', 'Zone Sud', 'Hydraulique', 4, 'Haute', 'Terminée', 40)
    iv3 = mk_intervention(d3, t5, 39, 'Terminée', 4,
        observations_txt="Fuite hydraulique visible au niveau du joint du vérin principal de la "
                         "presse P-07. Flaque d'huile constatée au sol, niveau du réservoir en baisse "
                         "progressive depuis plusieurs jours selon l'opérateur.",
        rapport_txt="Joints du vérin principal remplacés (usure normale liée au nombre de cycles). "
                    "Circuit hydraulique purgé et niveau d'huile complété. Test de pression à froid "
                    "et à chaud effectué, aucune fuite résiduelle constatée après 2h de fonctionnement.")

    d4 = mk_demande('Mise à jour poste de supervision', 'Migration du logiciel de supervision salle contrôle.',
                    'Salle de Contrôle', 'Site Khouribga', 'Informatique', 2, 'Basse', 'Terminée', 30)
    iv4 = mk_intervention(d4, t3, 29, 'Terminée', 3,
        observations_txt="Poste de supervision salle contrôle sous ancienne version du logiciel, "
                         "incompatible avec les nouveaux modules de reporting demandés par la direction.",
        rapport_txt="Migration effectuée vers la nouvelle version du logiciel de supervision. "
                    "Sauvegarde complète de la configuration existante réalisée avant intervention. "
                    "Tests de connexion aux automates vérifiés, aucune perte de données.")

    d5 = mk_demande('Vibration anormale broyeur BR-3', 'Vibration excessive sur le palier côté moteur.',
                    'Atelier Broyage', 'Zone Nord', 'Mécanique', 4, 'Haute', 'Terminée', 18)
    iv5 = mk_intervention(d5, t4, 17, 'Terminée', 6,
        observations_txt="Vibration anormale et bruit sourd constatés sur le palier côté moteur du "
                         "broyeur BR-3. Amplitude de vibration mesurée nettement supérieure au seuil "
                         "habituel. Jeu détecté au niveau du roulement principal.",
        rapport_txt="Roulement principal du palier remplacé (SKF 6208). Réajustement du jeu de "
                    "fonctionnement effectué selon spécifications constructeur. Joint d'étanchéité "
                    "également remplacé par précaution. Mesures de vibration post-intervention "
                    "revenues dans la plage normale.")

    d6 = mk_demande('Capteur pression ligne L-9 HS', 'Signal 4-20mA instable, capteur défaillance probable.',
                    'Unité Granulation', 'Zone Sud', 'Instrumentation', 3, 'Moyenne', 'Terminée', 10)
    iv6 = mk_intervention(d6, t2, 9, 'Terminée', 2,
        observations_txt="Signal du capteur de pression 4-20mA instable et incohérent sur la ligne L-9. "
                         "Valeurs erratiques constatées sur l'écran de supervision, capteur suspecté "
                         "en fin de vie.",
        rapport_txt="Capteur de pression remplacé (référence CPT-420). Câblage de raccordement "
                    "vérifié, aucune anomalie détectée. Calibrage effectué selon plage de mesure "
                    "0-10 bar. Signal stable et cohérent depuis la remise en service.")

        # ---------- Familles complémentaires pour le moteur de cas similaires ----------

    # Famille "Panne moteur/roulement" (variante 2 — vocabulaire différent)
    d10 = mk_demande('Échauffement moteur pompe hydraulique P-22',
                     'Moteur chaud au toucher, arrêt automatique par sécurité thermique.',
                     'Station Pompage', 'Zone Nord', 'Mécanique', 4, 'Haute', 'Terminée', 62)
    mk_intervention(d10, t4, 61, 'Terminée', 4,
        observations_txt="Moteur de la pompe P-22 déclenché par la sécurité thermique intégrée. "
                         "Au toucher, carcasse anormalement chaude. Roulement avant présentant un "
                         "jeu radial important, grattement audible à la rotation manuelle.",
        rapport_txt="Roulement avant remplacé (référence SKF 6208). Graissage complet effectué "
                    "selon plan de lubrification. Redémarrage progressif surveillé pendant 30 minutes, "
                    "température stabilisée dans la plage normale.")

    # Famille "Panne moteur/roulement" (variante 3)
    d11 = mk_demande('Bruit anormal ventilateur extraction VE-5',
                     'Bruit métallique intermittent signalé par les opérateurs de nuit.',
                     'Atelier Broyage', 'Zone Nord', 'Mécanique', 3, 'Moyenne', 'Terminée', 22)
    mk_intervention(d11, t1, 21, 'Terminée', 3,
        observations_txt="Bruit métallique intermittent constaté sur le ventilateur d'extraction VE-5, "
                         "plus marqué en début de cycle. Vibration légère ressentie sur le carter. "
                         "Roulement arrière suspecté après inspection visuelle.",
        rapport_txt="Roulement arrière remplacé par précaution malgré usure encore modérée. "
                    "Équilibrage de la turbine vérifié. Essai sur cycle complet effectué, "
                    "aucun bruit résiduel constaté.")

    # Famille "Fuite hydraulique" (variante 2)
    d12 = mk_demande('Suintement huile vérin presse P-03',
                     'Léger suintement constaté sous le vérin, à surveiller.',
                     'Atelier Presses', 'Zone Sud', 'Hydraulique', 2, 'Basse', 'Terminée', 48)
    mk_intervention(d12, t5, 47, 'Terminée', 2,
        observations_txt="Léger suintement d'huile hydraulique constaté sous le vérin de la presse "
                         "P-03, sans flaque importante. Niveau du réservoir stable. Joint torique "
                         "du vérin probablement en début d'usure.",
        rapport_txt="Joint torique du vérin remplacé de manière préventive. Nettoyage de la zone "
                    "affectée effectué. Surveillance recommandée sur les prochains cycles, "
                    "aucune fuite constatée après remise en service.")

    # Famille "Fuite hydraulique" (variante 3)
    d13 = mk_demande('Perte de pression circuit hydraulique broyeur BR-1',
                     'Baisse de pression progressive constatée sur le manomètre.',
                     'Atelier Broyage', 'Zone Nord', 'Hydraulique', 3, 'Moyenne', 'Terminée', 33)
    mk_intervention(d13, t1, 32, 'Terminée', 3,
        observations_txt="Baisse de pression progressive constatée sur le circuit hydraulique du "
                         "broyeur BR-1, manomètre affichant une valeur inférieure à la normale. "
                         "Flexible d'alimentation présentant une fissure superficielle.",
        rapport_txt="Flexible hydraulique remplacé. Circuit purgé et remis en pression. "
                    "Pression stabilisée à la valeur nominale après essai de 1h en charge.")

    # Famille "Défaut électrique/disjoncteur" (variante 2)
    d14 = mk_demande('Déclenchement répété armoire électrique A5',
                     'Coupure du courant plusieurs fois par jour sur armoire A5.',
                     'Atelier Lavage', 'Zone Nord', 'Électrique', 4, 'Haute', 'Terminée', 15)
    mk_intervention(d14, t2, 14, 'Terminée', 2,
        observations_txt="Déclenchement répété du disjoncteur de l'armoire A5, plusieurs fois par "
                         "jour selon les opérateurs. Aucune surcharge apparente identifiée au premier "
                         "abord. Contact électrique légèrement oxydé constaté sur une phase.",
        rapport_txt="Contact oxydé nettoyé et resserré. Test de charge effectué sur les trois phases, "
                    "aucun déséquilibre détecté. Disjoncteur remis en service, surveillance sur "
                    "48h sans nouvelle coupure.")

    # Famille "Défaut électrique/disjoncteur" (variante 3)
    d15 = mk_demande('Court-circuit suspecté armoire T5',
                     'Odeur de brûlé signalée près de l\'armoire électrique T5.',
                     'Poste Électrique', 'Zone Sud', 'Électrique', 5, 'Critique', 'Terminée', 8)
    mk_intervention(d15, t2, 7, 'Terminée', 3,
        observations_txt="Odeur de brûlé signalée par le personnel à proximité de l'armoire T5. "
                         "Trace de fusion visible sur un des câbles de raccordement, court-circuit "
                         "probable ayant déclenché la protection différentielle.",
        rapport_txt="Câble endommagé remplacé intégralement sur le tronçon concerné. Isolation "
                    "vérifiée au mégohmmètre, conforme. Protection différentielle testée, "
                    "déclenchement conforme aux normes.")

    # Famille "Capteur/instrumentation" (variante 2)
    d16 = mk_demande('Dérive mesure capteur température T-14',
                     'Valeurs de température incohérentes avec la réalité terrain.',
                     'Unité Granulation', 'Zone Sud', 'Instrumentation', 3, 'Moyenne', 'Terminée', 25)
    mk_intervention(d16, t5, 24, 'Terminée', 2,
        observations_txt="Capteur de température T-14 affichant des valeurs incohérentes avec les "
                         "mesures manuelles de contrôle. Dérive progressive constatée sur les "
                         "trois dernières semaines selon l'historique de supervision.",
        rapport_txt="Capteur recalibré selon procédure constructeur. Écart résiduel vérifié "
                    "conforme à la tolérance. Historique de supervision purgé des valeurs "
                    "erronées, nouvelle référence enregistrée.")

    # Famille "Capteur/instrumentation" (variante 3)
    d17 = mk_demande('Capteur niveau bac B-15 ne répond plus',
                     'Absence totale de signal du capteur de niveau depuis ce matin.',
                     'Atelier Lavage', 'Zone Nord', 'Instrumentation', 4, 'Haute', 'Terminée', 12)
    mk_intervention(d17, t2, 11, 'Terminée', 2,
        observations_txt="Capteur de niveau du bac B-15 sans signal depuis ce matin, alarme "
                         "d'absence de communication déclenchée sur le poste de supervision. "
                         "Connexion électrique suspectée après inspection préliminaire.",
        rapport_txt="Connecteur défaillant identifié et remplacé au niveau du boîtier de "
                    "raccordement. Communication rétablie et testée. Signal stable observé "
                    "pendant 1h de surveillance.")

    # Famille "Panne informatique/réseau site" (variante 2)
    d18 = mk_demande('Latence réseau bureau planification',
                     'Connexion très lente sur les postes du bureau planification.',
                     'Bureau Planification', 'Site Khouribga', 'Informatique', 2, 'Moyenne', 'Terminée', 20)
    mk_intervention(d18, t3, 19, 'Terminée', 2,
        observations_txt="Latence réseau importante signalée sur l'ensemble des postes du bureau "
                         "planification. Ralentissement plus marqué en fin de matinée. Switch "
                         "réseau du bureau suspecté après vérification des câblages.",
        rapport_txt="Switch réseau redémarré et firmware mis à jour vers la dernière version "
                    "stable. Tests de débit effectués sur chaque poste, latence revenue à la "
                    "normale sur l'ensemble du bureau.")

    # Famille "Panne informatique/réseau site" (variante 3)
    d19 = mk_demande('Perte de connexion poste supervision atelier',
                     'Écran de supervision figé, perte de connexion aux automates.',
                     'Salle de Contrôle', 'Site Khouribga', 'Informatique', 4, 'Haute', 'Terminée', 5)
    mk_intervention(d19, t3, 4, 'Terminée', 1,
        observations_txt="Écran de supervision de l'atelier figé, aucune mise à jour des données "
                         "depuis plusieurs minutes. Perte de connexion constatée entre le poste et "
                         "les automates de la ligne de production.",
        rapport_txt="Redémarrage du service de communication effectué. Câble réseau vérifié, "
                    "connecteur légèrement desserré remis en place. Connexion rétablie et "
                    "stable, données de supervision à jour.")

    # ---------- Cas isolés (démontrent "aucun historique proche") ----------
    d20 = mk_demande('Fissure structurelle passerelle accès zone stockage',
                     'Fissure constatée sur un support métallique de la passerelle.',
                     'Zone Stockage', 'Zone Sud', 'Civil', 5, 'Critique', 'Terminée', 60)
    mk_intervention(d20, t4, 59, 'Terminée', 8,
        observations_txt="Fissure structurelle constatée sur un support métallique de la passerelle "
                         "d'accès à la zone de stockage. Défaut probablement lié à la fatigue du "
                         "matériau après plusieurs années d'exposition aux intempéries.",
        rapport_txt="Support métallique renforcé par soudure et plaque de consolidation, "
                    "conformément aux préconisations du bureau d'études structure. Contrôle "
                    "visuel et test de charge statique réalisés, passerelle validée pour "
                    "remise en service.")

    d21 = mk_demande('Formation utilisateurs nouveau logiciel GMAO',
                     'Séance de formation demandée pour la prise en main du nouvel outil.',
                     'Bureau Accueil', 'Site Khouribga', 'Informatique', 1, 'Basse', 'Terminée', 5)
    mk_intervention(d21, t3, 4, 'Terminée', 3,
        observations_txt="Demande de formation à la prise en main du nouvel outil GMAO pour "
                         "l'équipe administrative, suite à la migration effectuée récemment.",
        rapport_txt="Session de formation de 3h organisée avec démonstration pratique des "
                    "principales fonctionnalités. Support de formation distribué aux participants. "
                    "Retours positifs recueillis en fin de session.")


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
        Message(intervention_id=iv1.id, user_id=planif.id,
                contenu="Merci de vérifier l'alignement avant remise en route.",
                date=utcnow() - timedelta(days=73, hours=5)),
        Message(intervention_id=iv1.id, user_id=tech.id,
                contenu="Alignement contrôlé, essai de rotation OK. Intervention terminée.",
                date=utcnow() - timedelta(days=73, hours=3)),
    ])

    db.session.commit()
