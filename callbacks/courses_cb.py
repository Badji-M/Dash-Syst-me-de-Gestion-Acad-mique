"""
callbacks/courses_cb.py — Callbacks supplémentaires pour le module Cours
Les callbacks principaux CRUD sont dans pages/courses.py (co-localisés).
Ce fichier contient les callbacks transversaux et les interactions avancées.
"""

from dash import callback, Output, Input, State, no_update, html
from database.db import get_db
from database.models import Course, Session
from sqlalchemy import func


# ── Compteur de séances en temps réel (badge dans le header nav) ──────────────
@callback(
    Output("course-form-container", "style"),
    Input("courses-refresh-trigger", "data"),
    prevent_initial_call=True,
)
def auto_close_form_on_refresh(trigger):
    """Ferme le formulaire automatiquement après une sauvegarde réussie."""
    return {"marginBottom": "20px"}


# ── Validation live du code cours (unicité) ────────────────────────────────────
@callback(
    Output("course-input-code", "className"),
    Input("course-input-code",  "value"),
    State("course-edit-id",     "data"),
    prevent_initial_call=True,
)
def validate_course_code_live(code, edit_id):
    """
    Validation en temps réel du code cours.
    Colore le champ en rouge si le code existe déjà.
    """
    if not code or len(code.strip()) < 2:
        return "form-control"
    try:
        with get_db() as db:
            q = db.query(Course).filter(
                Course.code == code.strip().upper()
            )
            if edit_id:
                q = q.filter(Course.id != edit_id)
            exists = q.first()
        return "form-control form-control-error" if exists else "form-control form-control-success"
    except Exception:
        return "form-control"
