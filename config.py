# config.py
import os

class Config:
    # 🔐 Clé secrète : obligatoire en production
    SECRET_KEY = os.environ.get("SECRET_KEY")
    if not SECRET_KEY:
        raise RuntimeError("SECRET_KEY is not set. Define it in environment variables.")

    # 🛢️ URL de la base de données
    DATABASE_URL = (
        os.environ.get("DATABASE_URL") or
        os.environ.get("POSTGRES_URL") or
        os.environ.get("POSTGRESQL_URL")
    )

    # 🛠️ Fallback en local uniquement (SQLite)
    if not DATABASE_URL:
        DATABASE_URL = "sqlite:///local.db"
        print("⚠️ Using SQLite for local development. Set DATABASE_URL in production.")

    # 🔗 Remplacer postgres:// ou postgresql:// par postgresql+pg8000://
    if DATABASE_URL.startswith("postgres://"):
        DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql+pg8000://", 1)
    elif DATABASE_URL.startswith("postgresql://"):
        DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+pg8000://", 1)

    # 📦 Configuration Flask-SQLAlchemy
    SQLALCHEMY_DATABASE_URI = DATABASE_URL
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # ⚙️ Options pour la stabilité (pooling + SSL pour Supabase)
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,           # Vérifie la connexion avant chaque requête
        'pool_recycle': 300,             # Recrée les connexions toutes les 5 min
        'connect_args': {
            'ssl_context': True          # 🔐 Obligatoire pour Supabase
        } if 'supabase.co' in DATABASE_URL else {}
    }