import os
from datetime import timedelta

BASE_DIR = os.path.abspath(os.path.dirname(__file__))


def _normalize_database_url(database_url):
    if database_url.startswith("postgres://"):
        return database_url.replace("postgres://", "postgresql://", 1)
    return database_url


def _default_sqlite_path():
    sqlite_db_path = os.environ.get("SQLITE_DB_PATH")
    if sqlite_db_path:
        return sqlite_db_path

    if os.environ.get("VERCEL"):
        return "/tmp/library.db"

    return os.path.join(BASE_DIR, "library.db")


def _database_uri():
    database_url = os.environ.get("DATABASE_URL")
    if database_url:
        return _normalize_database_url(database_url)

    return f"sqlite:///{_default_sqlite_path()}"


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "secret-key")
    SQLALCHEMY_DATABASE_URI = _database_uri()
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    PERMANENT_SESSION_LIFETIME = timedelta(hours=2)
    WTF_CSRF_ENABLED = True


class DevelopmentConfig(Config):
    DEBUG = True


class ProductionConfig(Config):
    DEBUG = False


config = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "default": DevelopmentConfig,
}
