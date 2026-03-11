"""
callbacks/sessions_cb.py — Callbacks supplémentaires pour le module Séances
Les callbacks principaux CRUD sont dans pages/sessions.py.
Ce fichier contient les interactions avancées et validations transversales.
"""

from dash import callback, Output, Input, State, no_update, html, ALL
from database.db import get_db
from database.models import Course, Session, Student
from sqlalchemy import func


# ── Compteur d'étudiants absents en temps réel ────────────────────────────────
@callback(
    Output("student-checklist-container", "style"),
    Input({"type": "student-absent-check", "index": ALL}, "value"),
    prevent_initial_call=True,
)
def highlight_checklist_on_absence(absent_values):
    """
    Met en évidence le conteneur de la checklist quand des absences sont cochées.
    """
    nb_absents = sum(1 for vals in absent_values if vals)
    if nb_absents > 0:
        return {
            "maxHeight": "320px", "overflowY": "auto",
            "border": f"1.5px solid #f57f17",
            "borderRadius": "10px", "padding": "8px",
        }
    return {
        "maxHeight": "320px", "overflowY": "auto",
        "border": "1px solid #e2e8f0",
        "borderRadius": "10px", "padding": "8px",
    }


# ── Mise à jour dynamique des options de séances selon le cours sélectionné ───
@callback(
    Output("attendance-filter-session", "placeholder"),
    Input("attendance-filter-course",   "value"),
    prevent_initial_call=True,
)
def update_session_placeholder(course_id):
    if not course_id:
        return "Sélectionner une séance"
    try:
        with get_db() as db:
            nb = db.query(func.count(Session.id)).filter(
                Session.course_id == course_id
            ).scalar() or 0
        return f"{nb} séance(s) disponible(s)"
    except Exception:
        return "Sélectionner une séance"
