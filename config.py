"""
config.py — Configuration globale du SGA
Centralise toutes les constantes, chemins et paramètres de l'application.
"""

import os

# ─── Chemins ────────────────────────────────────────────────────────────────
BASE_DIR    = os.path.dirname(os.path.abspath(__file__))
DATA_DIR    = os.path.join(BASE_DIR, "data")
ASSETS_DIR  = os.path.join(BASE_DIR, "assets")

# ─── Base de Données ─────────────────────────────────────────────────────────
DB_PATH     = os.path.join(BASE_DIR, "sga.db")
DB_URL      = f"sqlite:///{DB_PATH}"

# ─── Fichier Excel Source (migration) ───────────────────────────────────────
EXCEL_SOURCE = os.path.join(DATA_DIR, "source.xlsx")

# ─── Application Dash ────────────────────────────────────────────────────────
APP_TITLE   = "Academic Management System"
APP_VERSION = "1.0.0"
DEBUG       = True

# ─── Authentification ────────────────────────────────────────────────────────
SECRET_KEY  = "sga_secret_key_change_in_production"

# Utilisateurs par défaut (sera remplacé par la DB en production)
DEFAULT_USERS = {
    "admin": {
        "password": "admin123",   # sera hashé
        "role":     "admin",
        "name":     "Administrateur"
    },
    "teacher": {
        "password": "teacher123",
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
