# config.py
import os

class Config:
    # Clé secrète
    SECRET_KEY = os.environ.get("SECRET_KEY") or "change-this-in-production-render-2025"

    # Base de données - gestion pour pg8000
    DATABASE_URL = (
        os.environ.get("DATABASE_URL") or 
        os.environ.get("POSTGRES_URL") or
        os.environ.get("POSTGRESQL_URL")
    )

    # Si aucune URL de base de données n'est trouvée, utiliser SQLite en local
    if not DATABASE_URL:
        DATABASE_URL = "sqlite:///local.db"
        print("WARNING: Using SQLite for local development. Set DATABASE_URL for production.")

    # Adapter l'URL pour pg8000
    if DATABASE_URL.startswith("postgres://"):
        DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql+pg8000://", 1)
    elif DATABASE_URL.startswith("postgresql://"):
        DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+pg8000://", 1)

    SQLALCHEMY_DATABASE_URI = DATABASE_URL
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Options optimisées pour pg8000
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,
        'pool_recycle': 300,
        'pool_timeout': 20,
        'max_overflow': 0,
    }