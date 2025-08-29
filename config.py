# config.py
import os

class Config:
    # Clé secrète
    SECRET_KEY = os.environ.get("SECRET_KEY") or "super-secret-key"

    # Base de données
    DATABASE_URL = os.environ.get("DATABASE_URL")

    if not DATABASE_URL:
        raise ValueError("La variable d'environnement DATABASE_URL est manquante !")

    # Remplacer postgres:// par postgresql:// (obligatoire pour SQLAlchemy >= 1.4)
    if DATABASE_URL.startswith("postgres://"):
        DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

    SQLALCHEMY_DATABASE_URI = DATABASE_URL
    SQLALCHEMY_TRACK_MODIFICATIONS = False