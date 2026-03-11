"""
database/migration.py — Migration Excel → SQLite
Importe les données du fichier source.xlsx vers la base de données SQL.
Conçu pour être idempotent (peut être relancé sans créer de doublons).
"""

import os
import re
import sys
import unicodedata
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime, date
import pandas as pd

from config import EXCEL_SOURCE
from database.db import get_db
from database.models import Student, Course, Grade


# ─── Utilitaires ─────────────────────────────────────────────────────────────
def safe_date(value):
    """Convertit une valeur Excel en objet date Python."""
    if pd.isna(value):
        return None
    if isinstance(value, (datetime, date)):
        return value if isinstance(value, date) else value.date()
    try:
        return pd.to_datetime(value).date()
    except Exception:
        return None


def safe_str(value, default=""):
    """Convertit proprement une cellule en string."""
    if pd.isna(value):
        return default
    return str(value).strip()


def safe_float(value, default=0.0):
    """Convertit une cellule en float."""
    try:
        if pd.isna(value):
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def safe_bool(value, default=True):
    """Convertit une cellule texte en booléen."""
    text = safe_str(value, "")
    if not text:
        return default
    normalized = _normalize_label(text)
    if normalized in {"oui", "true", "1", "actif", "active"}:
        return True
    if normalized in {"non", "false", "0", "inactif", "inactive"}:
        return False
    return default


def _normalize_label(value) -> str:
    """Normalise noms de feuilles et colonnes pour tolérer accents et variantes."""
    if value is None or pd.isna(value):
        return ""
    text = unicodedata.normalize("NFKD", str(value)).encode("ascii", "ignore").decode("ascii")
    text = text.lower().replace("*", " ")
    return re.sub(r"[^a-z0-9]+", "_", text).strip("_")


def _resolve_sheet_name(sheet_names, candidates):
    candidate_names = {_normalize_label(name) for name in candidates}
    for sheet_name in sheet_names:
        if _normalize_label(sheet_name) in candidate_names:
            return sheet_name
    return None


def _load_sheet(xl: pd.ExcelFile, sheet_candidates, column_aliases):
    """Charge une feuille Excel en détectant automatiquement la vraie ligne d'en-tête."""
    sheet_name = _resolve_sheet_name(xl.sheet_names, sheet_candidates)
    if not sheet_name:
        print(f"[MIGRATION] Feuille '{sheet_candidates[0]}' introuvable — skip.")
        return None, None

    raw = xl.parse(sheet_name, header=None)
    alias_pool = {
        _normalize_label(alias)
        for aliases in column_aliases.values()
        for alias in aliases
    }

    best_header_idx = None
    best_score = -1
    for idx in range(min(len(raw), 10)):
        labels = [_normalize_label(value) for value in raw.iloc[idx].tolist()]
        score = sum(1 for label in labels if label in alias_pool)
        if score > best_score:
            best_score = score
            best_header_idx = idx

    if best_header_idx is None or best_score <= 0:
        print(f"[MIGRATION] En-têtes introuvables dans la feuille '{sheet_name}' — skip.")
        return sheet_name, None

    df = raw.iloc[best_header_idx + 1:].copy()
    df.columns = raw.iloc[best_header_idx].tolist()
    df = df.dropna(how="all").reset_index(drop=True)

    rename_map = {}
    normalized_aliases = {
        field: {_normalize_label(alias) for alias in aliases}
        for field, aliases in column_aliases.items()
    }
    for col in df.columns:
        normalized_col = _normalize_label(col)
        for field, aliases in normalized_aliases.items():
            if normalized_col in aliases:
                rename_map[col] = field
                break

    return sheet_name, df.rename(columns=rename_map)


def _has_required_columns(df, required_columns, sheet_name):
    missing = [col for col in required_columns if col not in df.columns]
    if missing:
        print(
            f"[MIGRATION] Colonnes manquantes dans '{sheet_name}' : {', '.join(missing)} — skip."
        )
        return False
    return True


# ─── Migration des Étudiants ──────────────────────────────────────────────────
def migrate_students(xl: pd.ExcelFile, db) -> dict:
    """
    Importe la feuille 'Students' du fichier Excel.
    Retourne un mapping {excel_id: db_id} pour les relations.
    Colonnes attendues : ID, Nom, Prénom, Email, Date_naissance
    """
    id_map = {}

    sheet_name, df = _load_sheet(
        xl,
        ["Students", "Etudiants"],
        {
            "excel_id": ["ID"],
            "last_name": ["Nom", "Nom *"],
            "first_name": ["Prénom", "Prenom", "Prénom *", "Prenom *"],
            "email": ["Email", "Email *"],
            "birth_date": ["Date_naissance", "Date naissance"],
            "is_active": ["Actif", "Actif (Oui/Non)"],
        },
    )
    if df is None:
        return id_map
    if not _has_required_columns(df, ["last_name", "first_name", "email"], sheet_name):
        return id_map

    count_new = 0

    for _, row in df.iterrows():
        email = safe_str(row.get("email", "")).lower()
        if not email:
            continue

        # Vérifier si l'étudiant existe déjà
        existing = db.query(Student).filter(Student.email == email).first()
        if existing:
            excel_id = row.get("excel_id")
            if not pd.isna(excel_id):
                id_map[excel_id] = existing.id
            id_map[email] = existing.id
            continue

        student = Student(
            last_name  = safe_str(row.get("last_name",  "")),
            first_name = safe_str(row.get("first_name", "")),
            email      = email,
            birth_date = safe_date(row.get("birth_date")),
            is_active  = safe_bool(row.get("is_active"), True),
        )
        db.add(student)
        db.flush()
        excel_id = row.get("excel_id")
        if not pd.isna(excel_id):
            id_map[excel_id] = student.id
        id_map[email] = student.id
        count_new += 1

    print(f"[MIGRATION] Students : {count_new} importés.")
    return id_map


# ─── Migration des Cours ──────────────────────────────────────────────────────
def migrate_courses(xl: pd.ExcelFile, db) -> dict:
    """
    Importe la feuille 'Courses' du fichier Excel.
    Retourne un mapping {excel_code: db_id}.
    Colonnes attendues : Code, Libellé, Volume_horaire, Enseignant
    """
    id_map = {}

    sheet_name, df = _load_sheet(
        xl,
        ["Courses", "Cours"],
        {
            "code": ["Code", "Code *"],
            "label": ["Libellé", "Libelle", "Intitulé", "Intitule", "Intitulé *", "Intitule *"],
            "total_hours": ["Volume_horaire", "Volume horaire", "Volume horaire *"],
            "teacher": ["Enseignant"],
            "description": ["Description"],
            "is_active": ["Actif", "Actif (Oui/Non)"],
        },
    )
    if df is None:
        return id_map
    if not _has_required_columns(df, ["code", "label"], sheet_name):
        return id_map

    count_new = 0

    for _, row in df.iterrows():
        code = safe_str(row.get("code", "")).upper()
        if not code:
            continue

        existing = db.query(Course).filter(Course.code == code).first()
        if existing:
            id_map[code] = existing.id
            continue

        course = Course(
            code        = code,
            label       = safe_str(row.get("label", "")),
            total_hours = safe_float(row.get("total_hours", 0)),
            teacher     = safe_str(row.get("teacher", "")),
            description = safe_str(row.get("description", "")),
            is_active   = safe_bool(row.get("is_active"), True),
        )
        db.add(course)
        db.flush()
        id_map[code] = course.id
        count_new += 1

    print(f"[MIGRATION] Courses : {count_new} importés.")
    return id_map


# ─── Migration des Notes ──────────────────────────────────────────────────────
def migrate_grades(xl: pd.ExcelFile, db, student_map: dict, course_map: dict):
    """
    Importe la feuille 'Grades' du fichier Excel.
    Colonnes attendues : ID_Student, Code_Course, Note, Coefficient, Libellé, Date
    """
    sheet_name, df = _load_sheet(
        xl,
        ["Grades", "Notes"],
        {
            "student_id": ["ID_Student", "ID Student"],
            "student_email": ["Email étudiant", "Email etudiant", "Email étudiant *", "Email etudiant *"],
            "course_code": ["Code_Course", "Code cours", "Code cours *"],
            "grade": ["Note", "Note /20", "Note /20 *"],
            "coefficient": ["Coefficient"],
            "label": ["Libellé", "Libelle", "Libellé éval", "Libelle eval", "Libellé éval *", "Libelle eval *"],
            "date": ["Date"],
        },
    )
    if df is None:
        return
    if not _has_required_columns(df, ["course_code", "grade"], sheet_name):
        return
    if "student_id" not in df.columns and "student_email" not in df.columns:
        print(f"[MIGRATION] Aucune clé étudiant reconnue dans '{sheet_name}' — skip.")
        return

    count_new = 0

    for _, row in df.iterrows():
        excel_student_id = row.get("student_id")
        student_email    = safe_str(row.get("student_email", "")).lower()
        course_code      = safe_str(row.get("course_code", "")).upper()
        grade_val        = safe_float(row.get("grade"))
        label            = safe_str(row.get("label", "Évaluation"))

        student_id = student_map.get(student_email) if student_email else student_map.get(excel_student_id)
        course_id  = course_map.get(course_code)

        if not student_id or not course_id:
            continue

        # Vérifier doublon
        from sqlalchemy import and_
        existing = db.query(Grade).filter(
            and_(
                Grade.student_id == student_id,
                Grade.course_id  == course_id,
                Grade.label      == label,
            )
        ).first()

        if existing:
            continue

        grade = Grade(
            student_id  = student_id,
            course_id   = course_id,
            grade       = grade_val,
            coefficient = safe_float(row.get("coefficient", 1.0), 1.0),
            label       = label,
            date        = safe_date(row.get("date")),
        )
        db.add(grade)
        count_new += 1

    db.flush()
    print(f"[MIGRATION] Grades : {count_new} importés.")


# ─── Point d'Entrée Principal ─────────────────────────────────────────────────
def run_migration(excel_path: str = None):
    """
    Lance la migration complète Excel → SQLite.
    Peut être appelé depuis app.py ou en ligne de commande.
    """
    path = excel_path or EXCEL_SOURCE

    if not os.path.exists(path):
        print(f"[MIGRATION] Fichier Excel introuvable : {path}")
        print("[MIGRATION] Migration ignorée — démarrage avec base vide.")
        return False

    print(f"[MIGRATION] Démarrage depuis : {path}")

    try:
        xl = pd.ExcelFile(path)
    except Exception as e:
        print(f"[MIGRATION] Impossible de lire le fichier Excel : {e}")
        return False

    try:
        with get_db() as db:
            student_map = migrate_students(xl, db)
            course_map  = migrate_courses(xl, db)
            migrate_grades(xl, db, student_map, course_map)

        print("[MIGRATION] Terminée avec succès.")
        return True

    except Exception as e:
        print(f"[MIGRATION] Erreur : {e}")
        return False


# ─── Exécution directe ────────────────────────────────────────────────────────
if __name__ == "__main__":
    from database.db import init_db
    init_db()
    run_migration()
