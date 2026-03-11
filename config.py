"""
config.py — Configuration globale du SGA
Centralise toutes les constantes, chemins et paramètres de l'application.
"""

import os


def _env_bool(name, default=False):
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _env_int(name, default):
    value = os.getenv(name)
    if value is None:
        return default
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _normalize_db_url(url):
    if url and url.startswith("postgres://"):
        return "postgresql://" + url[len("postgres://"):]
    return url

# ─── Chemins ────────────────────────────────────────────────────────────────
BASE_DIR    = os.path.dirname(os.path.abspath(__file__))
DATA_DIR    = os.path.join(BASE_DIR, "data")
ASSETS_DIR  = os.path.join(BASE_DIR, "assets")

# ─── Base de Données ─────────────────────────────────────────────────────────
DB_PATH     = os.path.join(BASE_DIR, "sga.db")
DB_URL      = _normalize_db_url(
    os.getenv("DATABASE_URL") or os.getenv("DB_URL") or f"sqlite:///{DB_PATH}"
)

# ─── Fichier Excel Source (migration) ───────────────────────────────────────
EXCEL_SOURCE = os.getenv("EXCEL_SOURCE", os.path.join(DATA_DIR, "source.xlsx"))

# ─── Application Dash ────────────────────────────────────────────────────────
APP_TITLE   = "Academic Management System"
APP_VERSION = "1.0.0"
DEBUG       = _env_bool("DEBUG", True)
HOST        = os.getenv("HOST", "0.0.0.0")
PORT        = _env_int("PORT", 8050)
AUTO_INIT_DB = _env_bool("AUTO_INIT_DB", True)
RUN_STARTUP_MIGRATION = _env_bool(
    "RUN_STARTUP_MIGRATION",
    os.path.exists(EXCEL_SOURCE),
)

# ─── Authentification ────────────────────────────────────────────────────────
SECRET_KEY  = os.getenv("SECRET_KEY", "sga_secret_key_change_in_production")

DEFAULT_ADMIN_PASSWORD = os.getenv("DEFAULT_ADMIN_PASSWORD", "admin123")
DEFAULT_TEACHER_PASSWORD = os.getenv("DEFAULT_TEACHER_PASSWORD", "teacher123")

# Utilisateurs par défaut (sera remplacé par la DB en production)
DEFAULT_USERS = {
    "admin": {
        "password": DEFAULT_ADMIN_PASSWORD,   # sera hashé
        "role":     "admin",
        "name":     "Administrateur"
    },
    "teacher": {
        "password": DEFAULT_TEACHER_PASSWORD,
        "role":     "teacher",
        "name":     "Enseignant"
    }
}

# ─── Rôles et Permissions ────────────────────────────────────────────────────
ROLES = {
    "admin":   ["read", "write", "delete", "export", "manage_users"],
    "teacher": ["read", "write", "export"],
    "viewer":  ["read"],
}

# ─── Design / UI ─────────────────────────────────────────────────────────────
# Palette de couleurs (synchronisée avec style.css)
COLORS = {
    "primary":    "#1a237e",   # Bleu institutionnel foncé
    "secondary":  "#283593",
    "accent":     "#e53935",   # Rouge accent
    "success":    "#2e7d32",
    "warning":    "#f57f17",
    "danger":     "#c62828",
    "light":      "#f5f6fa",
    "dark":       "#1c1c2e",
    "text":       "#212121",
    "muted":      "#757575",
    "border":     "#e0e0e0",
    "white":      "#ffffff",
}

# ─── Font Awesome CDN ─────────────────────────────────────────────────────────
FA_CDN = "https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.0/css/all.min.css"

# ─── Pagination ───────────────────────────────────────────────────────────────
DEFAULT_PAGE_SIZE = 10

# ─── Export PDF ───────────────────────────────────────────────────────────────
SCHOOL_NAME     = "Établissement Académique"
SCHOOL_ADDRESS  = "123 Rue de l'École, 75000 Paris"
PDF_OUTPUT_DIR  = os.path.join(BASE_DIR, "exports")
