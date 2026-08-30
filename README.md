<div align="center">

# 🔧 Gestion des Interventions — OCP Khouribga

**Plateforme de planification, suivi et pilotage des interventions de maintenance**

*Service Informatique — Digital Corner OCP Khouribga*

![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=flat&logo=python&logoColor=white)
![Flask](https://img.shields.io/badge/Flask-3.0-000000?style=flat&logo=flask&logoColor=white)
![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-ORM-D71F00?style=flat)
![scikit-learn](https://img.shields.io/badge/scikit--learn-ML-F7931E?style=flat)
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
- [Le moteur de cas similaires (RAG)](#le-moteur-de-cas-similaires-rag)
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

Ce projet a été développé dans le cadre d'un stage d'observation au sein du Digital Corner OCP Khouribga, service informatique du Groupe OCP. Il répond à un besoin identifié sur le terrain : faciliter la gestion des demandes d'intervention, améliorer la planification des activités des techniciens et optimiser le suivi des opérations de maintenance.

L'application couvre l'ensemble du cycle de vie d'une intervention, de la demande initiale jusqu'à la clôture et l'archivage du rapport, en intégrant une couche d'aide à la décision multicritère et un moteur de recherche de cas similaires basé sur l'historique des interventions.

---

## Aperçu

L'application est organisée autour de six grands blocs fonctionnels :

1. **Gestion des demandes** — création, suivi, priorisation
2. **Planification** — affectation des techniciens, scoring de pertinence
3. **Suivi opérationnel** — statuts, observations, communication terrain/bureau
4. **Gestion des stocks** — pièces détachées consommées pendant les interventions
5. **Pilotage** — tableau de bord, alertes, rapports, prévisions
6. **Aide à la décision augmentée** — recherche de cas similaires et synthèse IA ancrée sur l'historique réel

Le tout est servi par une interface web unique, avec un accès différencié selon le rôle de la personne connectée.

---

## Fonctionnalités

### Demandes d'intervention
- Création avec titre, description, client, localisation, type, impact métier (1 à 5), échéance
- Filtrage par statut (Nouvelle, Planifiée, En cours, Terminée, Annulée) et par priorité
- **Priorisation automatique** : un score sur 100 est calculé à partir de mots-clés d'urgence détectés dans le texte, de l'impact déclaré et de la proximité de l'échéance
- La création d'une demande est ouverte à tout utilisateur connecté ; seule la **planification** (affectation d'un technicien et d'une date) reste réservée à l'administrateur et au planificateur

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
- Validation des champs numériques des formulaires

### Alertes intelligentes
Générées en continu à partir de l'état réel du système :
- Stock sous le seuil d'alerte
- Demande non planifiée dont l'échéance approche (risque SLA)
- Technicien en surcharge (4 interventions actives ou plus)
- Intervention planifiée mais en retard de démarrage

### Rapports
- Rapport global (toutes interventions terminées) et rapport détaillé par intervention
- Consultables en ligne, imprimables via le navigateur, et exportables en PDF (xhtml2pdf)

### Suivi client
- Chaque demande génère un lien de suivi public unique (token UUID), consultable sans authentification

### Carte des techniciens
- Localisation partagée à la demande par le technicien, visualisée sur une carte interactive (Leaflet / OpenStreetMap)

### Moteur de cas similaires (RAG)
- Recherche, parmi les interventions terminées, des cas les plus proches textuellement d'une nouvelle demande (vectorisation TF-IDF + similarité cosinus, 100 % local)
- Synthèse en langage naturel générée par un modèle de langage, **ancrée exclusivement** sur les cas réellement retrouvés (citation explicite des sources, aucune invention d'information)

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
| Recherche de similarité | scikit-learn (TF-IDF, similarité cosinus) |
| Synthèse IA ancrée (RAG) | API GroqCloud (modèle `openai/gpt-oss-120b`) |
| Conteneurisation | Docker |

---

## Acteurs et rôles

| Acteur | Description |
|---|---|
| Administrateur | Responsable du service maintenance. Hérite de toutes les permissions du planificateur, plus le droit de suppression (techniciens, pièces). |
| Planificateur | Reçoit les demandes, décide de la planification, gère le stock et les fiches techniciens (sans droit de suppression). |
| Technicien | Peut créer une demande et exécute les interventions sur le terrain. N'a accès qu'à ses propres interventions ; ne gère ni stock ni techniciens. |
| Client (sans compte) | Suit l'avancement de sa demande via un lien de suivi public, sans authentification. |

---

## Flux applicatif détaillé

1. **Création** — une demande est créée par n'importe quel utilisateur connecté
2. **Analyse IA** — le système calcule une priorité suggérée (score sur 100) et recherche des cas similaires dans l'historique
3. **Suggestion** — le système classe les techniciens disponibles pour cette demande
4. **Planification** — le planificateur choisit un technicien et une date ; une intervention est créée
5. **Exécution** — le technicien passe l'intervention "En cours", prélève des pièces, échange des messages, rédige ses observations
6. **Clôture** — statut "Terminée", durée calculée automatiquement, technicien libéré, rapport finalisé
7. **Pilotage** — les KPI, alertes et prévisions sont mis à jour en continu sur le tableau de bord ; l'intervention enrichit l'historique consultable par le moteur de cas similaires

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
- User et Technicien : relation un-à-un facultative des deux côtés
- Technicien vers Intervention : un technicien réalise zéro à plusieurs interventions ; chaque intervention a exactement un technicien
- Demande vers Intervention : une demande génère zéro ou une intervention, uniquement une fois planifiée
- Intervention et Piece : relation plusieurs-à-plusieurs matérialisée par UtilisationPiece

---

## Le module d'aide à la décision

Le fichier `app/intelligence.py` centralise la logique décisionnelle sous forme de règles pondérées explicites (pas de machine learning au sens de modèle entraîné pour cette partie) :

| Fonction | Rôle |
|---|---|
| `analyser_priorite()` | Score /100 à partir des mots-clés d'urgence, de l'impact métier et de la proximité d'échéance |
| `scorer_techniciens()` | Classe les techniciens pour une demande : compétence (40 pts), disponibilité (25), charge (25), zone (10) |
| `generer_alertes()` | Surveille en continu : stock critique, risque SLA, surcharge, retard de démarrage |
| `previsions_stock()` | Estime le nombre d'interventions futures couvertes par le stock actuel |
| `recommandations_affectation()` | Vue globale : meilleur technicien pour chaque demande en attente |
| `calculer_kpis()` | Taux de résolution, durée moyenne, taux de retard |

---

## Le moteur de cas similaires (RAG)

En complément du scoring par règles, un module de type *Retrieval-Augmented Generation* aide le planificateur à s'appuyer sur l'historique réel des interventions.

| Fonction | Rôle | Dépendance réseau |
|---|---|---|
| `rechercher_cas_similaires()` | Recherche les interventions terminées les plus proches textuellement (TF-IDF + similarité cosinus) | Aucune — calcul 100 % local |
| `synthetiser_recommandation_ia()` | Génère une synthèse en langage naturel, ancrée exclusivement sur les cas retrouvés, avec citation explicite des sources | Oui (API GroqCloud) — avec repli gracieux si indisponible |

**Principe de robustesse :** la synthèse IA n'est jamais générée sans preuves — si aucun cas similaire n'est trouvé localement, aucun appel au modèle de langage n'est effectué. Si le service de synthèse est indisponible, les cas similaires bruts restent affichés au planificateur.

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
| `GROQ_API_KEY` | Clé API GroqCloud, nécessaire pour la synthèse IA du moteur de cas similaires (gratuite sur console.groq.com) | aucune — la fonctionnalité de synthèse se désactive proprement si absente |

> **Important** : en production ou pour toute démonstration partagée, définissez toujours `SECRET_KEY` explicitement. Ne laissez jamais `FLASK_DEBUG=1` activé en dehors d'un débogage local. La clé `GROQ_API_KEY` doit être exportée dans le même terminal que celui utilisé pour lancer `python run.py`.

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

> **Note technique** : le seed de données de démonstration (`app/seed.py`) n'est déclenché que par `python run.py`, jamais par les commandes `flask db`. Le jeu de données inclut 18 interventions terminées réparties en 5 familles de pannes (mécanique, hydraulique, électrique, instrumentation, informatique) avec des observations et rapports textuellement variés, conçues pour démontrer le moteur de cas similaires.

---

## Lancement

```bash
export GROQ_API_KEY=ta-cle-groq   # optionnel, pour activer la synthèse IA
python run.py
```

L'application est accessible sur `http://127.0.0.1:5000`.

Au premier lancement, si la base est vide, des données de démonstration sont automatiquement injectées.

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
| Technicien | ahmed | tech123 | Création de demandes, accès à ses propres interventions uniquement |

---

## Rôles et permissions

| Action | Administrateur | Planificateur | Technicien |
|---|:---:|:---:|:---:|
| Créer une demande | ✅ | ✅ | ✅ |
| Planifier une demande (affecter technicien + date) | ✅ | ✅ | ❌ |
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
- `__init__.py` — application factory
- `models.py` — modèles SQLAlchemy
- `seed.py` — données de démonstration (21 interventions, 5 familles de pannes)
- `intelligence.py` — module d'aide à la décision et moteur de cas similaires (RAG)

**Dossier `app/routes/`** (blueprints)
- `auth.py`, `main.py`, `demandes.py`, `interventions.py`, `techniciens.py`, `stock.py`, `rapports.py`, `suivi.py`

**Dossier `app/templates/`**
- sous-dossiers `demandes/`, `interventions/`, `techniciens/`, `stock/`, `rapports/`, `suivi/`, `errors/`

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
| `/demandes/<id>` | GET | Détail, suggestions de techniciens et cas similaires |
| `/demandes/<id>/planifier` | POST | Planification |
| `/demandes/<id>/synthese-ia` | GET | Génération de la synthèse IA ancrée sur les cas similaires |
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

- Mots de passe hachés avec Werkzeug, jamais stockés en clair
- Protection CSRF sur tous les formulaires via Flask-WTF
- Contrôle d'accès par rôle sur chaque route sensible
- Un technicien ne peut agir que sur ses propres interventions, avec réponse HTTP 403 explicite
- Pages d'erreur 403 et 404 personnalisées
- Le lien de suivi client repose sur un token UUID non devinable
- La synthèse IA est strictement ancrée sur des données réelles de la base, limitant le risque de génération d'informations inventées (hallucination)

---

## Dépannage

**Erreur `ModuleNotFoundError: No module named 'app.seed'` lors de `flask db init`**
Le fichier `app/seed.py` doit exister avant toute commande `flask db`.

**Erreur `sqlite3.OperationalError: no such table: user`**
Le seed s'exécute avant que les migrations n'aient créé les tables. Vérifiez que `seed_if_empty()` se trouve bien à l'intérieur du bloc `if __name__ == '__main__':` de `run.py`.

**La synthèse IA affiche « n'est pas disponible pour le moment »**
Vérifiez dans l'ordre : que `GROQ_API_KEY` est bien exportée dans le terminal où `python run.py` a été lancé, que le crédit/quota de votre compte n'est pas épuisé, et que le nom du modèle utilisé (`openai/gpt-oss-120b`) n'a pas été déprécié entre-temps par le fournisseur.

**Les scores de similarité du moteur de cas similaires semblent tous nuls ou absents**
Vérifiez le seuil minimal et le paramètre `ngram_range` dans `rechercher_cas_similaires()` — sur un petit corpus, des bigrammes combinés à un seuil trop élevé peuvent filtrer tous les résultats malgré un classement relatif correct.

---

## Limites connues et pistes d'évolution

- La position des techniciens est partagée ponctuellement, à la demande, et non en suivi continu
- Le suivi client se fait par lien à token, sans compte ni authentification dédiée
- Le module d'aide à la décision principal repose sur des règles pondérées explicites, et non sur un modèle entraîné
- Le moteur de cas similaires utilise TF-IDF plutôt que des embeddings sémantiques, pour des raisons de robustesse et d'explicabilité sur un petit corpus ; une évolution vers des embeddings deviendrait pertinente avec un historique plus volumineux
- Aucun test automatisé n'est encore en place
- Pas de notification push ou email lors des alertes critiques

---

## Auteur

Projet réalisé par El hynani Manar dans le cadre d'un stage à Digital Corner OCP Khouribga.

École Nationale des Sciences Appliquées de Khouribga (ENSA Khouribga)
Filière Génie Informatique — Université Sultan Moulay Slimane