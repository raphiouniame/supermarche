# app.py
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from models import db, Produit, Fournisseur, Transaction, Credit, CreditDetail, Paiement
from config import Config
import re
from difflib import SequenceMatcher
from datetime import datetime, timedelta

app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)

# Créer les tables si elles n'existent pas
@app.before_first_request
def create_tables():
    db.create_all()

# === FONCTIONS UTILITAIRES ===
def similar(a, b):
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()

def trouver_produit_par_nom(nom):
    if not nom:
        raise ValueError("Nom vide")
    produits = Produit.query.all()
    exact = [p for p in produits if p.nom.lower() == nom.lower()]
    if exact:
        return exact[0]
    partial = [p for p in produits if nom.lower() in p.nom.lower()]
    if len(partial) == 1:
        return partial[0]
    ranked = sorted(produits, key=lambda p: similar(p.nom, nom), reverse=True)
    if ranked and similar(ranked[0].nom, nom) > 0.6:
        return ranked[0]
    raise ValueError("Produit non trouvé")

# === ROUTES ===
@app.route("/")
def index():
    total_ventes = db.session.query(db.func.sum(Transaction.prix_vente * Transaction.quantite)) \
                             .filter(Transaction.type == 'vente').scalar() or 0
    total_achats = db.session.query(db.func.sum(Transaction.prix_achat * Transaction.quantite)) \
                             .filter(Transaction.type == 'achat').scalar() or 0
    benefice_estime = total_ventes - total_achats
    stock_faible = Produit.query.filter(Produit.quantite <= 5).count()
    credits_en_cours = Credit.query.filter_by(regle=False).count()

    return render_template("index.html",
        total_ventes=total_ventes,
        benefice_estime=benefice_estime,
        stock_faible=stock_faible,
        credits_en_cours=credits_en_cours
    )

# --- VENTES ---
@app.route("/ventes", methods=["GET", "POST"])
def ventes():
    if request.method == "POST":
        data = request.form.get("produits", "")
        items = [item.strip() for item in data.split(",") if item.strip()]
        details = []
        total_global = 0.0

        for item in items:
            if 'x' not in item:
                flash(f"Format invalide : {item}", "error")
                continue
            nom, qte = item.rsplit('x', 1)
            nom = nom.strip()
            try:
                qte = int(qte.strip())
                produit = trouver_produit_par_nom(nom)
                if qte > produit.quantite:
                    flash(f"Stock insuffisant pour {produit.nom}", "error")
                    continue
                total = produit.prix_vente * qte
                if produit.promotion > 0:
                    total *= (1 - produit.promotion / 100)
                details.append({
                    'produit': produit,
                    'quantite': qte,
                    'total': total,
                    'prix_vente': produit.prix_vente
                })
                total_global += total
            except Exception as e:
                flash(f"Erreur avec {nom}: {str(e)}", "error")

        if not details:
            return redirect(url_for("ventes"))

        montant_paye = float(request.form.get("montant", 0))
        monnaie = montant_paye - total_global

        if monnaie < 0:
            flash(f"Montant insuffisant. Il manque {-monnaie:.2f}F", "error")
            return redirect(url_for("ventes"))

        if not request.form.get("confirm"):
            return render_template("confirm_sale.html", details=details, total_global=total_global, montant_paye=montant_paye, monnaie=monnaie)

        # Confirmer la vente
        for d in details:
            produit = d['produit']
            produit.quantite -= d['quantite']
            transaction = Transaction(
                produit_id=produit.id,
                type='vente',
                quantite=d['quantite'],
                prix_achat=produit.prix_achat,
                prix_vente=d['prix_vente']
            )
            db.session.add(transaction)
        db.session.commit()
        flash(f"Vente de {total_global:.2f}F enregistrée !", "success")
        return redirect(url_for("ventes"))

    produits = Produit.query.all()
    return render_template("ventes.html", produits=produits)

# --- AUTOCOMPLETE PRODUITS (AJAX) ---
@app.route("/recherche_produit")
def recherche_produit():
    q = request.args.get("q", "")
    if len(q) < 2:
        return jsonify([])
    produits = Produit.query.filter(Produit.nom.ilike(f"%{q}%")).limit(10).all()
    return jsonify([{"id": p.id, "nom": p.nom} for p in produits])

# --- CREDITS ---
@app.route("/credits", methods=["GET", "POST"])
def credits():
    if request.method == "POST":
        nom = request.form.get("nom_client")
        contact = request.form.get("contact")
        produits_data = request.form.get("produits")
        items = [item.strip() for item in produits_data.split(",") if item.strip()]
        total = 0.0
        details = []

        for item in items:
            if 'x' not in item:
                flash(f"Format invalide : {item}", "error")
                continue
            nom_prod, qte = item.rsplit('x', 1)
            qte = int(qte.strip())
            produit = trouver_produit_par_nom(nom_prod.strip())
            total += produit.prix_vente * qte
            details.append({'produit_id': produit.id, 'quantite': qte, 'prix_vente': produit.prix_vente})

        if total == 0:
            flash("Aucun produit valide", "error")
            return redirect(url_for("credits"))

        credit = Credit(nom_client=nom, contact=contact, total=total, regle=False)
        db.session.add(credit)
        db.session.flush()
        for d in details:
            detail = CreditDetail(
                credit_id=credit.id,
                produit_id=d['produit_id'],
                quantite=d['quantite'],
                prix_vente=d['prix_vente']
            )
            db.session.add(detail)
        db.session.commit()
        flash("Crédit enregistré !", "success")
        return redirect(url_for("credits"))

    credits = Credit.query.order_by(Credit.date.desc()).all()
    return render_template("credits.html", credits=credits)

# --- PAIEMENT CREDIT ---
@app.route("/credit/<int:id>/paiement", methods=["POST"])
def paiement_credit(id):
    credit = Credit.query.get_or_404(id)
    montant = float(request.form.get("montant"))
    solde = credit.total - sum(p.montant for p in credit.paiements)
    if montant > solde:
        flash("Montant trop élevé", "error")
    else:
        paiement = Paiement(credit_id=id, montant=montant)
        db.session.add(paiement)
        db.session.commit()
        if solde - montant <= 0:
            credit.regle = True
            db.session.commit()
            flash("Crédit entièrement remboursé !", "success")
        else:
            flash(f"Paiement enregistré. Solde restant : {solde - montant:.2f}F", "success")
    return redirect(url_for("credits"))

# --- STOCKS ---
@app.route("/stocks")
def stocks():
    seuil = 5
    produits_faibles = Produit.query.filter(Produit.quantite <= seuil).all()
    tous_produits = Produit.query.all()
    return render_template("stocks.html", produits_faibles=produits_faibles, tous_produits=tous_produits)

# --- APPROVISIONNEMENTS ---
@app.route("/approvisionnements", methods=["GET", "POST"])
def approvisionnements():
    if request.method == "POST":
        nom = request.form.get("nom")
        quantite = int(request.form.get("quantite"))
        prix_achat = float(request.form.get("prix_achat"))
        prix_vente = float(request.form.get("prix_vente"))
        id_fournisseur = request.form.get("id_fournisseur")
        categorie = request.form.get("categorie", "")

        produit = Produit.query.filter_by(nom=nom).first()
        if produit:
            produit.quantite += quantite
            produit.prix_achat = prix_achat
            produit.prix_vente = prix_vente
        else:
            id = f"P{Produit.query.count() + 1:03d}"
            produit = Produit(
                id=id, nom=nom, quantite=quantite,
                prix_achat=prix_achat, prix_vente=prix_vente,
                id_fournisseur=id_fournisseur, categorie=categorie
            )
            db.session.add(produit)

        transaction = Transaction(
            produit_id=produit.id,
            type='achat',
            quantite=quantite,
            prix_achat=prix_achat,
            prix_vente=prix_vente
        )
        db.session.add(transaction)
        db.session.commit()
        flash("Approvisionnement enregistré", "success")
        return redirect(url_for("approvisionnements"))

    fournisseurs = Fournisseur.query.all()
    return render_template("approvisionnements.html", fournisseurs=fournisseurs)

# --- FOURNISSEURS ---
@app.route("/fournisseurs", methods=["GET", "POST"])
def fournisseurs():
    if request.method == "POST":
        id = request.form.get("id")
        nom = request.form.get("nom")
        contact = request.form.get("contact")
        fournisseur = Fournisseur(id=id, nom=nom, contact=contact)
        db.session.add(fournisseur)
        db.session.commit()
        flash("Fournisseur ajouté", "success")
        return redirect(url_for("fournisseurs"))

    fournisseurs = Fournisseur.query.all()
    return render_template("fournisseurs.html", fournisseurs=fournisseurs)

if __name__ == "__main__":
    app.run(debug=True)