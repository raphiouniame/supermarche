# config.py
import os

class Config:
    # Clé secrète
    SECRET_KEY = os.environ.get("SECRET_KEY") or "change-this-in-production-render-2025"

    # Base de données
    DATABASE_URL = (
        os.environ.get("DATABASE_URL") or 
        os.environ.get("POSTGRES_URL") or
        os.environ.get("POSTGRESQL_URL")
    )

    # Fallback pour le développement local
    if not DATABASE_URL:
        DATABASE_URL = "sqlite:///local.db"
        print("WARNING: Using SQLite for local development. Set DATABASE_URL for production.")

    # Remplacer postgres:// par postgresql:// (obligatoire pour SQLAlchemy >= 1.4)
    if DATABASE_URL.startswith("postgres://"):
        DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

    SQLALCHEMY_DATABASE_URI = DATABASE_URL
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Options pour la stabilité avec PostgreSQL
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,
        'pool_recycle': 300,
    }