# -*- coding: utf-8 -*-
"""Modèles de données – Gestion des Interventions."""
import uuid

from datetime import date, datetime

from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash

from . import db, login_manager

PRIORITES = ['Basse', 'Moyenne', 'Haute', 'Critique']
STATUTS_DEMANDE = ['Nouvelle', 'Planifiée', 'En cours', 'Terminée', 'Annulée']
STATUTS_INTERVENTION = ['Planifiée', 'En cours', 'Terminée', 'Annulée']
TYPES_INTERVENTION = ['Mécanique', 'Électrique', 'Informatique', 'Hydraulique', 'Instrumentation', 'Civil']


class User(UserMixin, db.Model):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    nom = db.Column(db.String(120), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='technicien')  # admin | planificateur | technicien
    technicien_id = db.Column(db.Integer, db.ForeignKey('technicien.id'), nullable=True)

    technicien = db.relationship('Technicien', backref='compte', uselist=False)
    messages = db.relationship('Message', backref='auteur', lazy=True)

    def set_password(self, pwd):
        self.password_hash = generate_password_hash(pwd)

    def check_password(self, pwd):
        return check_password_hash(self.password_hash, pwd)

    @property
    def is_admin(self):
        return self.role == 'admin'

    @property
    def is_planificateur(self):
        return self.role in ('admin', 'planificateur')


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


class Technicien(db.Model):
    __tablename__ = 'technicien'
    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(120), nullable=False)
    specialite = db.Column(db.String(200), nullable=False, default='')  # ex. "Mécanique, Hydraulique"
    zone = db.Column(db.String(120), nullable=False, default='Site Khouribga')
    telephone = db.Column(db.String(30), nullable=False, default='')
    statut = db.Column(db.String(20), nullable=False, default='disponible')  # disponible | occupe | absent

    latitude = db.Column(db.Float, nullable=True)
    longitude = db.Column(db.Float, nullable=True)
    derniere_position = db.Column(db.DateTime, nullable=True)

    interventions = db.relationship('Intervention', backref='technicien', lazy=True)

    def charge_active(self):
        """Nombre d'interventions planifiées ou en cours."""
        return Intervention.query.filter(
            Intervention.technicien_id == self.id,
            Intervention.statut.in_(['Planifiée', 'En cours'])).count()

    def competences(self):
        return [s.strip() for s in (self.specialite or '').split(',') if s.strip()]


class Demande(db.Model):
    __tablename__ = 'demande'
    id = db.Column(db.Integer, primary_key=True)
    titre = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True, default='')
    client = db.Column(db.String(120), nullable=False, default='')
    localisation = db.Column(db.String(120), nullable=False, default='')
    type_intervention = db.Column(db.String(60), nullable=False, default='Mécanique')
    impact = db.Column(db.Integer, nullable=False, default=3)  # 1 (faible) à 5 (bloquant)
    priorite = db.Column(db.String(20), nullable=False, default='Moyenne')
    statut = db.Column(db.String(20), nullable=False, default='Nouvelle')
    date_creation = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    date_echeance = db.Column(db.Date, nullable=True)
    token_suivi = db.Column(db.String(36), unique=True, nullable=False,
                        default=lambda: str(uuid.uuid4()))

    intervention = db.relationship('Intervention', backref='demande', uselist=False)

    @property
    def en_retard(self):
        return (self.date_echeance is not None
                and self.date_echeance < date.today()
                and self.statut not in ('Terminée', 'Annulée'))

    @property
    def jours_restants(self):
        if self.date_echeance is None:
            return None
        return (self.date_echeance - date.today()).days


class Intervention(db.Model):
    __tablename__ = 'intervention'
    id = db.Column(db.Integer, primary_key=True)
    demande_id = db.Column(db.Integer, db.ForeignKey('demande.id'), nullable=False)
    technicien_id = db.Column(db.Integer, db.ForeignKey('technicien.id'), nullable=False)
    date_planifiee = db.Column(db.Date, nullable=False)
    date_debut = db.Column(db.DateTime, nullable=True)
    date_fin = db.Column(db.DateTime, nullable=True)
    statut = db.Column(db.String(20), nullable=False, default='Planifiée')
    observations = db.Column(db.Text, nullable=True, default='')
    rapport = db.Column(db.Text, nullable=True, default='')

    pieces_utilisees = db.relationship('UtilisationPiece', backref='intervention',
                                       lazy=True, cascade='all, delete-orphan')
    messages = db.relationship('Message', backref='intervention',
                               lazy=True, cascade='all, delete-orphan')

    def cout_pieces(self):
        return sum(u.quantite * (u.piece.prix_unitaire or 0) for u in self.pieces_utilisees)

    def duree_heures(self):
        if self.date_debut and self.date_fin:
            return round((self.date_fin - self.date_debut).total_seconds() / 3600, 1)
        return None


class Piece(db.Model):
    __tablename__ = 'piece'
    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(150), nullable=False)
    reference = db.Column(db.String(60), unique=True, nullable=False)
    quantite = db.Column(db.Integer, nullable=False, default=0)
    seuil_alerte = db.Column(db.Integer, nullable=False, default=5)
    prix_unitaire = db.Column(db.Float, nullable=False, default=0.0)

    utilisations = db.relationship('UtilisationPiece', backref='piece', lazy=True)

    @property
    def en_alerte(self):
        return self.quantite <= self.seuil_alerte


class UtilisationPiece(db.Model):
    __tablename__ = 'utilisation_piece'
    id = db.Column(db.Integer, primary_key=True)
    intervention_id = db.Column(db.Integer, db.ForeignKey('intervention.id'), nullable=False)
    piece_id = db.Column(db.Integer, db.ForeignKey('piece.id'), nullable=False)
    quantite = db.Column(db.Integer, nullable=False, default=1)
    date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)


class Message(db.Model):
    __tablename__ = 'message'
    id = db.Column(db.Integer, primary_key=True)
    intervention_id = db.Column(db.Integer, db.ForeignKey('intervention.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    contenu = db.Column(db.Text, nullable=False)
    date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)