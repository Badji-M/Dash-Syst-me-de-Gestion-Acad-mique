"""
callbacks/students_cb.py — Callbacks supplémentaires pour le module Étudiants
Les callbacks principaux CRUD sont dans pages/students.py.
Ce fichier contient les validations live et interactions avancées.
"""

from dash import callback, Output, Input, State, no_update, html
from database.db import get_db
from database.models import Student


# ── Validation live de l'email ────────────────────────────────────────────────
@callback(
    Output("student-input-email", "className"),
    Input("student-input-email",  "value"),
    State("student-edit-id",      "data"),
    prevent_initial_call=True,
)
def validate_email_live(email, edit_id):
    """
    Vérifie en temps réel si l'email est valide et unique.
    """
    if not email or "@" not in email or "." not in email:
        return "form-control"
    try:
        with get_db() as db:
            q = db.query(Student).filter(Student.email == email.strip().lower())
            if edit_id:
                q = q.filter(Student.id != edit_id)
            exists = q.first()
        return "form-control form-control-error" if exists else "form-control form-control-success"
    except Exception:
        return "form-control"


# ── Activation du bouton import selon l'état du parsing ─────────────────────
@callback(
    Output("btn-import-grades", "disabled"),
    Input("upload-parsed-data", "data"),
    prevent_initial_call=True,
)
def toggle_import_button(parsed_data):
    """Active le bouton d'import uniquement si le parsing est réussi."""
    return parsed_data is None or len(parsed_data) == 0


# ── Réinitialisation du formulaire étudiant après annulation ─────────────────
@callback(
    Output("student-input-lastname",  "value"),
    Output("student-input-firstname", "value"),
    Output("student-input-email",     "value"),
    Output("student-input-birthdate", "date"),
    Input("btn-cancel-student-form",  "n_clicks"),
    Input("btn-close-student-form",   "n_clicks"),
    prevent_initial_call=True,
)
def reset_student_form(n_cancel, n_close):
    return "", "", "", None
