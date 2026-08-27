<div align="center">

# 🔧 Gestion des Interventions — OCP Khouribga

**Plateforme de planification, suivi et pilotage des interventions de maintenance**

*Service Informatique — Groupe OCP, Site de Khouribga*

![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=flat&logo=python&logoColor=white)
![Flask](https://img.shields.io/badge/Flask-3.0-000000?style=flat&logo=flask&logoColor=white)
![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-ORM-D71F00?style=flat)
![License](https://img.shields.io/badge/Licence-Académique-lightgrey?style=flat)
![Status](https://img.shields.io/badge/Statut-Actif-success?style=flat)

</div>

---

## Sommaire

- [Contexte du projet](#contexte-du-projet)
- [Aperçu](#aperçu)
- [Fonctionnalités](#fonctionnalités)
- [Stack technique](#stack-technique)
- [Acteurs et rôles](#acteurs-et-rôles)
- [Flux applicatif détaillé](#flux-applicatif-détaillé)
- [Modèle de données](#modèle-de-données)
- [Le module d'aide à la décision](#le-module-daide-à-la-décision)
- [Installation](#installation)
- [Configuration](#configuration)
- [Base de données et migrations](#base-de-données-et-migrations)
- [Lancement](#lancement)
- [Comptes de démonstration](#comptes-de-démonstration)
- [Rôles et permissions](#rôles-et-permissions)
- [Structure du projet](#structure-du-projet)
- [Liste des routes principales](#liste-des-routes-principales)
- [Sécurité](#sécurité)
- [Dépannage](#dépannage)
- [Limites connues et pistes d'évolution](#limites-connues-et-pistes-dévolution)
- [Auteur](#auteur)

---

## Contexte du projet

Ce projet a été développé dans le cadre d'un stage au sein du service informatique de **Digiself OCP Khouribga**. Il répond à un besoin identifié sur le terrain : faciliter la gestion des demandes d'intervention, améliorer la planification des activités des techniciens et optimiser le suivi des opérations de maintenance.

L'application couvre l'ensemble du cycle de vie d'une intervention, de la demande initiale jusqu'à la clôture et l'archivage du rapport, en intégrant une couche d'aide à la décision pour assister le planificateur.

---

## Aperçu

L'application est organisée autour de cinq grands blocs fonctionnels :

1. **Gestion des demandes** — création, suivi, priorisation
2. **Planification** — affectation des techniciens, scoring de pertinence
3. **Suivi opérationnel** — statuts, observations, communication terrain/bureau
4. **Gestion des stocks** — pièces détachées consommées pendant les interventions
5. **Pilotage** — tableau de bord, alertes, rapports, prévisions

Le tout est servi par une interface web unique, avec un accès différencié selon le rôle de la personne connectée.

---

## Fonctionnalités

### Demandes d'intervention
- Création avec titre, description, client, localisation, type, impact métier (1 à 5), échéance
- Filtrage par statut (Nouvelle, Planifiée, En cours, Terminée, Annulée) et par priorité
- **Priorisation automatique** : un score sur 100 est calculé à partir de mots-clés d'urgence détectés dans le texte, de l'impact déclaré et de la proximité de l'échéance

### Planification intelligente
Pour chaque demande, le système calcule un score de pertinence pour chaque technicien disponible, basé sur :
- la correspondance de compétences (40 points)
- la disponibilité déclarée (25 points)
- la charge de travail actuelle (25 points)
- la proximité de zone géographique (10 points)

Le planificateur choisit librement, en s'appuyant sur ce classement.

### Suivi en temps réel
- Cycle de statut d'une intervention : Planifiée → En cours → Terminée (ou Annulée à tout moment)
- Réaffectation possible d'un technicien à un autre en cours de route
- Observations terrain et rapport technique rédigés directement par le technicien
- Protection d'accès : un technicien ne peut consulter ou modifier que les interventions qui lui sont assignées

### Communication
- Messagerie intégrée par intervention, entre le technicien sur le terrain et le bureau

### Gestion du stock
- Suivi des pièces détachées : quantité, seuil d'alerte, prix unitaire
- Prélèvement de pièces directement depuis la fiche intervention, uniquement quand l'intervention est En cours, avec possibilité d'annuler un prélèvement erroné
- Validation des champs numériques des formulaires (rejet propre des valeurs non numériques ou négatives)

### Alertes intelligentes
Générées en continu à partir de l'état réel du système :
- Stock sous le seuil d'alerte
- Demande non planifiée dont l'échéance approche (risque SLA)
- Technicien en surcharge (4 interventions actives ou plus)
- Intervention planifiée mais en retard de démarrage

### Rapports
- Rapport global (toutes interventions terminées) et rapport détaillé par intervention
- Consultables en ligne, imprimables via le navigateur, et exportables en PDF (généré côté serveur avec xhtml2pdf)

### Suivi client
- Chaque demande génère un lien de suivi public unique (token UUID), consultable sans authentification, pour permettre au client de suivre l'avancement de sa demande

### Carte des techniciens
- Localisation partagée à la demande par le technicien (géolocalisation navigateur), visualisée sur une carte interactive (Leaflet / OpenStreetMap) par le planificateur

---

## Stack technique

| Couche | Technologies |
|---|---|
| Langage | Python 3.10+ |
| Framework web | Flask 3.0 |
| ORM | Flask-SQLAlchemy |
| Authentification | Flask-Login |
| Sécurité formulaires | Flask-WTF (protection CSRF) |
| Migrations de schéma | Flask-Migrate (Alembic) |
| Base de données | SQLite (développement), compatible PostgreSQL |
| Frontend | Bootstrap 5, Bootstrap Icons |
| Graphiques | Chart.js |
| Cartographie | Leaflet.js + OpenStreetMap |
| Génération PDF | xhtml2pdf |
| Conteneurisation | Docker |

---

## Acteurs et rôles

| Acteur | Description |
|---|---|
| Administrateur | Responsable du service maintenance. Accès complet, y compris les suppressions (techniciens, pièces). |
| Planificateur | Reçoit les demandes, décide de la planification, gère le stock et les fiches techniciens (sans droit de suppression). |
| Technicien | Exécute les interventions sur le terrain. N'a accès qu'à ses propres interventions ; ne gère ni stock ni techniciens. |
| Client (sans compte) | Suit l'avancement de sa demande via un lien de suivi public, sans authentification. |

---

## Flux applicatif détaillé

1. **Création** — une demande est créée (titre, description, impact, échéance)
2. **Analyse Intelligente** — le système calcule une priorité suggérée (score sur 100)
3. **Suggestion** — le système classe les techniciens disponibles pour cette demande
4. **Planification** — le planificateur choisit un technicien et une date ; une intervention est créée
5. **Exécution** — le technicien passe l'intervention "En cours", prélève des pièces, échange des messages, rédige ses observations
6. **Clôture** — statut "Terminée", durée calculée automatiquement, technicien libéré, rapport finalisé
7. **Pilotage** — les KPI, alertes et prévisions sont mis à jour en continu sur le tableau de bord

---

## Modèle de données

L'application repose sur sept entités principales.

| Entité | Rôle |
|---|---|
| User | Compte de connexion (rôle : admin, planificateur ou technicien) |
| Technicien | Fiche technicien (compétences, zone, disponibilité, position GPS) |
| Demande | Demande d'intervention initiale, avec token de suivi public |
| Intervention | Exécution planifiée d'une demande, liée à un technicien |
| Piece | Pièce détachée en stock |
| UtilisationPiece | Table d'association entre Intervention et Piece, avec quantité et date |
| Message | Message échangé sur une intervention |

**Relations clés :**
- User et Technicien : relation un-à-un facultative des deux côtés (un technicien n'a pas forcément de compte, un compte n'est pas forcément lié à une fiche technicien)
- Technicien vers Intervention : un technicien réalise zéro à plusieurs interventions ; chaque intervention a exactement un technicien
- Demande vers Intervention : une demande génère zéro ou une intervention, uniquement une fois planifiée
- Intervention et Piece : relation plusieurs-à-plusieurs matérialisée par UtilisationPiece, qui porte la quantité et la date du prélèvement

---

## Le module d'aide à la décision

Le fichier `app/intelligence.py` centralise toute la logique décisionnelle sous forme de règles pondérées explicites. Il ne s'agit pas de machine learning, mais d'un système de scoring transparent et explicable.

| Fonction | Rôle | Détail |
|---|---|---|
| `analyser_priorite()` | Priorisation automatique | Mots-clés d'urgence, plus impact métier multiplié par 5, plus proximité d'échéance, plafonné à 100 |
| `scorer_techniciens()` | Suggestion d'affectation | Compétence (40), disponibilité (25), charge (25), zone (10), avec détail explicatif |
| `generer_alertes()` | Surveillance continue | Fusionne quatre sources : stock, SLA, surcharge, retards |
| `previsions_stock()` | Anticipation des ruptures | Consommation moyenne sur 30 jours, traduite en nombre d'interventions encore couvertes |
| `recommandations_affectation()` | Vue globale | Meilleur technicien et alternatives pour chaque demande en attente |
| `calculer_kpis()` | Indicateurs de pilotage | Taux de résolution, durée moyenne, taux de retard |

Tous les calculs sont effectués à la volée à chaque requête, sans mise en cache, pour garantir des données toujours à jour.

---

## Installation

### Prérequis
- Python 3.10 ou supérieur
- pip
- git

### Étapes

```bash
git clone <url-du-repo>
cd ocp

python3 -m venv venv
source venv/bin/activate
```

Sous Windows, remplacez la dernière ligne par :
```bash
venv\Scripts\activate
```

Puis installez les dépendances :
```bash
pip install -r requirements.txt
```

---

## Configuration

Copiez le fichier d'exemple et ajustez-le si nécessaire :

```bash
cp .env.example .env
```

| Variable | Description | Valeur par défaut |
|---|---|---|
| `SECRET_KEY` | Clé secrète Flask, utilisée pour signer les sessions et les tokens CSRF | générée aléatoirement à chaque démarrage |
| `DATABASE_URL` | URI de connexion à la base de données | `sqlite:///interventions.db` |
| `FLASK_DEBUG` | Active le débogueur interactif Flask (1 ou 0) | 0 |

> **Important** : en production ou pour toute démonstration partagée, définissez toujours `SECRET_KEY` explicitement. La valeur aléatoire par défaut change à chaque redémarrage du serveur, ce qui invalide toutes les sessions actives. Ne laissez jamais `FLASK_DEBUG=1` activé en dehors d'un débogage local : le débogueur Werkzeug permet l'exécution de code arbitraire si le serveur est joignable depuis l'extérieur.

---

## Base de données et migrations

Le schéma est géré par Flask-Migrate (Alembic), et non par `db.create_all()`, afin de pouvoir faire évoluer le modèle de données sans perdre les données existantes.

### Premier lancement

```bash
export FLASK_APP=run.py
flask db init
flask db migrate -m "schema initial"
flask db upgrade
```

Sous Windows (cmd), remplacez la première ligne par :
```bash
set FLASK_APP=run.py
```

### Après une modification de `app/models.py`

```bash
flask db migrate -m "description du changement"
flask db upgrade
```

> **Note technique** : le seed de données de démonstration (`app/seed.py`) n'est déclenché que par `python run.py`, jamais par les commandes `flask db`. Cette séparation évite un conflit où le seed tenterait d'interroger des tables qui n'existent pas encore au moment des migrations.

---

## Lancement

```bash
python run.py
```

L'application est accessible sur `http://127.0.0.1:5000`.

Au premier lancement, si la base est vide, des données de démonstration sont automatiquement injectées : cinq techniciens, cinq pièces détachées, trois comptes utilisateurs et une quinzaine de demandes et interventions à différents statuts.

### Avec Docker

```bash
docker build -t ocp-interventions .
docker run -p 5000:5000 --env-file .env ocp-interventions
```

---

## Comptes de démonstration

| Rôle | Identifiant | Mot de passe | Droits |
|---|---|---|---|
| Administrateur | admin | admin123 | Accès complet, y compris suppressions |
| Planificateur | planif | planif123 | Gestion des demandes, techniciens, stock |
| Technicien | ahmed | tech123 | Accès à ses propres interventions uniquement |

---

## Rôles et permissions

| Action | Administrateur | Planificateur | Technicien |
|---|:---:|:---:|:---:|
| Créer ou planifier une demande | ✅ | ✅ | ❌ |
| Réaffecter une intervention | ✅ | ✅ | ❌ |
| Gérer les techniciens | ✅ | ✅ | ❌ |
| Gérer le stock | ✅ | ✅ | ❌ |
| Suppression (techniciens, pièces) | ✅ | ❌ | ❌ |
| Voir ou modifier ses propres interventions | ✅ | ✅ | ✅ |
| Voir les interventions d'un autre technicien | ✅ | ✅ | ❌ |
| Prélever une pièce sur une intervention | ✅ | ✅ | ✅ si assigné |
| Consulter les rapports | ✅ | ✅ | ✅ |

---

## Structure du projet

**Racine du projet (`ocp/`)**
- `requirements.txt` — dépendances Python
- `run.py` — point d'entrée de l'application
- `Dockerfile` — image de conteneurisation
- `.env.example` — modèle de configuration
- `README.md` — ce fichier

**Dossier `app/`**
- `__init__.py` — application factory (création et configuration de l'app Flask)
- `models.py` — modèles SQLAlchemy
- `seed.py` — données de démonstration
- `intelligence.py` — module d'aide à la décision

**Dossier `app/routes/`** (blueprints)
- `auth.py` — connexion, déconnexion, contrôle des rôles
- `main.py` — tableau de bord, centre de décision
- `demandes.py` — création et planification des demandes
- `interventions.py` — suivi, statuts, pièces, messages
- `techniciens.py` — gestion des techniciens et position GPS
- `stock.py` — gestion des pièces détachées
- `rapports.py` — rapports web et export PDF
- `suivi.py` — suivi public par lien à token

**Dossier `app/templates/`**
- sous-dossiers `demandes/`, `interventions/`, `techniciens/`, `stock/`, `rapports/`, `suivi/`, `errors/` (pages 403 et 404 personnalisées)

**Dossier `migrations/`**
- historique des migrations Alembic

---

## Liste des routes principales

| Route | Méthode | Description |
|---|---|---|
| `/login` | GET, POST | Connexion |
| `/` | GET | Tableau de bord |
| `/intelligence` | GET | Centre d'aide à la décision |
| `/demandes` | GET | Liste des demandes |
| `/demandes/nouvelle` | GET, POST | Création d'une demande |
| `/demandes/<id>` | GET | Détail et suggestions de techniciens |
| `/demandes/<id>/planifier` | POST | Planification |
| `/interventions/<id>` | GET | Suivi d'une intervention |
| `/interventions/<id>/statut` | POST | Changement de statut |
| `/interventions/<id>/reaffecter` | POST | Réaffectation de technicien |
| `/interventions/<id>/piece` | POST | Prélèvement de pièce |
| `/techniciens` | GET | Liste des techniciens |
| `/techniciens/carte` | GET | Carte de localisation |
| `/stock` | GET | Liste des pièces |
| `/rapports` | GET | Rapport global |
| `/rapports/pdf` | GET | Export PDF du rapport global |
| `/suivi/<token>` | GET | Suivi public d'une demande, sans authentification |

---

## Sécurité

- Mots de passe hachés avec Werkzeug (`generate_password_hash` et `check_password_hash`), jamais stockés en clair
- Protection CSRF sur tous les formulaires via Flask-WTF
- Contrôle d'accès par rôle sur chaque route sensible
- Un technicien ne peut agir que sur ses propres interventions, avec réponse HTTP 403 explicite en cas de tentative d'accès non autorisé
- Pages d'erreur 403 et 404 personnalisées, cohérentes avec le reste de l'interface
- Le lien de suivi client repose sur un token UUID non devinable, sans exposer d'information sur les autres demandes

---

## Dépannage

**Erreur `ModuleNotFoundError: No module named 'app.seed'` lors de `flask db init`**
Le fichier `app/seed.py` doit exister avant toute commande `flask db`, car `create_app()` en dépend indirectement au chargement du module.

**Erreur `sqlite3.OperationalError: no such table: user`**
Le seed s'exécute avant que les migrations n'aient créé les tables. Vérifiez que l'appel à `seed_if_empty()` se trouve bien à l'intérieur du bloc `if __name__ == '__main__':` de `run.py`, jamais au niveau module.

**Erreur `ValueError: Constraint must have a name` lors d'une migration SQLite**
SQLite exige un nom explicite pour toute contrainte unique ajoutée en mode batch Alembic. Nommez-la manuellement dans le fichier de migration généré, par exemple `uq_ma_table_ma_colonne`.

---

## Limites connues et pistes d'évolution

- La position des techniciens est partagée ponctuellement, à la demande, et non en suivi continu type géolocalisation temps réel
- Le suivi client se fait par lien à token, sans compte ni authentification dédiée, ce qui est suffisant pour un usage simple mais ne conserve pas d'historique de connexion côté client
- Le module d'intelligence repose sur des règles pondérées explicites, et non sur un modèle entraîné à partir de données historiques
- Aucun test automatisé n'est encore en place ; une piste d'amélioration prioritaire serait de couvrir `intelligence.py` par des tests unitaires
- Pas de notification push ou email lors des alertes critiques

---

## Auteur

Projet réalisé par El Hynani Manar dans le cadre d'un stage à Digital Corner OCP Khouribga.

École Nationale des Sciences Appliquées de Khouribga (ENSA Khouribga)
Filière Génie Informatique — Université Sultan Moulay Slimane