# models.py
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class Produit(db.Model):
    id = db.Column(db.String(20), primary_key=True)
    nom = db.Column(db.String(100), nullable=False)
    prix_achat = db.Column(db.Float, nullable=False)
    prix_vente = db.Column(db.Float, nullable=False)
    quantite = db.Column(db.Integer, default=0)
    id_fournisseur = db.Column(db.String(20), db.ForeignKey('fournisseur.id'))
    categorie = db.Column(db.String(50))
    promotion = db.Column(db.Float, default=0.0)

    # Relation
    fournisseur = db.relationship('Fournisseur', back_populates='produits')
    transactions = db.relationship('Transaction', back_populates='produit', cascade="all, delete-orphan")

    def benefice_unitaire(self):
        return self.prix_vente - self.prix_achat

class Fournisseur(db.Model):
    id = db.Column(db.String(20), primary_key=True)
    nom = db.Column(db.String(100), nullable=False)
    contact = db.Column(db.String(100))

    produits = db.relationship('Produit', back_populates='fournisseur')

class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    produit_id = db.Column(db.String(20), db.ForeignKey('produit.id'), nullable=False)
    type = db.Column(db.String(10), nullable=False)  # 'achat' ou 'vente'
    quantite = db.Column(db.Integer, nullable=False)
    prix_achat = db.Column(db.Float, nullable=False)
    prix_vente = db.Column(db.Float, nullable=False)
    date = db.Column(db.DateTime, default=datetime.utcnow)

    produit = db.relationship('Produit', back_populates='transactions')

class Credit(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nom_client = db.Column(db.String(100), nullable=False)
    contact = db.Column(db.String(100))
    date = db.Column(db.DateTime, default=datetime.utcnow)
    total = db.Column(db.Float, nullable=False)
    regle = db.Column(db.Boolean, default=False)

    paiements = db.relationship('Paiement', back_populates='credit', cascade="all, delete-orphan")
    details = db.relationship('CreditDetail', back_populates='credit', cascade="all, delete-orphan")

class CreditDetail(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    credit_id = db.Column(db.Integer, db.ForeignKey('credit.id'))
    produit_id = db.Column(db.String(20), db.ForeignKey('produit.id'))
    quantite = db.Column(db.Integer)
    prix_vente = db.Column(db.Float)

    credit = db.relationship('Credit', back_populates='details')
    produit = db.relationship('Produit')

class Paiement(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    credit_id = db.Column(db.Integer, db.ForeignKey('credit.id'))
    montant = db.Column(db.Float, nullable=False)
    date = db.Column(db.DateTime, default=datetime.utcnow)

    credit = db.relationship('Credit', back_populates='paiements')