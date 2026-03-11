"""
seed_demo.py — Données de démonstration pour le SGA
======================================================
Simule une promotion réelle :
  - 5 cours avec enseignants
  - 20 étudiants
  - 3 mois de séances (sept → nov 2024) avec présences
  - 3 évaluations par cours avec notes réalistes

Utilisation :
    cd sga/
    python seed_demo.py

Pour remettre à zéro et re-seeder :
    python seed_demo.py --reset
"""

import sys
import os
import random
import hashlib
from datetime import date, timedelta

# ── Résolution des imports depuis la racine du projet ────────────────────────
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database.db import init_db, get_db
from database.models import Student, Course, Session, Attendance, Grade, User


# ════════════════════════════════════════════════════════════════════════════
# DONNÉES FICTIVES RÉALISTES
# ════════════════════════════════════════════════════════════════════════════

ETUDIANTS = [
    ("DIALLO",      "Mamadou",    "mamadou.diallo@etud.sga.sn",    "2001-03-14"),
    ("NDIAYE",      "Fatou",      "fatou.ndiaye@etud.sga.sn",      "2000-07-22"),
    ("SALL",        "Ibrahima",   "ibrahima.sall@etud.sga.sn",     "2001-11-05"),
    ("FALL",        "Aissatou",   "aissatou.fall@etud.sga.sn",     "2000-02-18"),
    ("GUEYE",       "Omar",       "omar.gueye@etud.sga.sn",        "2001-09-30"),
    ("BA",          "Mariama",    "mariama.ba@etud.sga.sn",        "2000-05-12"),
    ("MBAYE",       "Cheikh",     "cheikh.mbaye@etud.sga.sn",      "2001-01-25"),
    ("DIOUF",       "Rokhaya",    "rokhaya.diouf@etud.sga.sn",     "2000-08-09"),
    ("CISSE",       "Abdoulaye",  "abdoulaye.cisse@etud.sga.sn",   "2001-06-17"),
    ("TOURE",       "Khady",      "khady.toure@etud.sga.sn",       "2000-12-03"),
    ("SARR",        "Moussa",     "moussa.sarr@etud.sga.sn",       "2001-04-28"),
    ("FAYE",        "Ndéye",      "ndeye.faye@etud.sga.sn",        "2000-10-15"),
    ("SYLLA",       "Lamine",     "lamine.sylla@etud.sga.sn",      "2001-08-07"),
    ("TRAORE",      "Aminata",    "aminata.traore@etud.sga.sn",    "2000-03-21"),
    ("KOUYATE",     "Serigne",    "serigne.kouyate@etud.sga.sn",   "2001-07-14"),
    ("MBODJ",       "Sokhna",     "sokhna.mbodj@etud.sga.sn",     "2000-01-08"),
    ("DIAGNE",      "Pape",       "pape.diagne@etud.sga.sn",       "2001-05-19"),
    ("LO",          "Binta",      "binta.lo@etud.sga.sn",          "2000-09-27"),
    ("BADJI",       "Elhadji",    "elhadji.badji@etud.sga.sn",     "2001-02-11"),
    ("THIONGANE",   "Coumba",     "coumba.thiongane@etud.sga.sn",  "2000-06-04"),
]

COURS = [
    {
        "code":         "MATH201",
        "label":        "Mathématiques Appliquées",
        "total_hours":  45,
        "teacher":      "Dr. Moussa Diallo",
        "description":  "Algèbre linéaire, analyse numérique et probabilités.",
    },
    {
        "code":         "INFO301",
        "label":        "Algorithmique et Structures de Données",
        "total_hours":  40,
        "teacher":      "Dr. Fatima Ndiaye",
        "description":  "Algorithmes de tri, graphes, arbres binaires et complexité.",
    },
    {
        "code":         "GEST201",
        "label":        "Gestion de Projet",
        "total_hours":  30,
        "teacher":      "M. Ibrahim Sow",
        "description":  "Méthodes agiles, planification et conduite de projet.",
    },
    {
        "code":         "STAT101",
        "label":        "Statistiques Descriptives",
        "total_hours":  35,
        "teacher":      "Dr. Mariama Ba",
        "description":  "Analyse de données, représentations graphiques et inférence.",
    },
    {
        "code":         "COMM101",
        "label":        "Communication Professionnelle",
        "total_hours":  25,
        "teacher":      "Mme Rokhaya Faye",
        "description":  "Rédaction professionnelle, présentations et prise de parole.",
    },
]

# Thèmes de séances par cours
THEMES = {
    "MATH201": [
        "Introduction à l'algèbre linéaire",
        "Matrices et déterminants",
        "Systèmes d'équations linéaires",
        "Vecteurs propres et valeurs propres",
        "Suites et séries numériques",
        "Dérivées et intégrales",
        "Probabilités — événements et variables",
        "Distributions de probabilité",
        "Loi normale et théorème central limite",
        "Révisions et exercices d'application",
    ],
    "INFO301": [
        "Complexité algorithmique — notations O",
        "Tri par insertion et tri fusion",
        "Tri rapide (quicksort)",
        "Listes chaînées et piles",
        "Files et arbres binaires",
        "Arbres binaires de recherche",
        "Parcours de graphes — DFS / BFS",
        "Algorithmes de plus court chemin",
        "Programmation dynamique",
        "Révisions et TD",
    ],
    "GEST201": [
        "Introduction à la gestion de projet",
        "Méthodes agiles — Scrum",
        "Planification et WBS",
        "Gestion des risques",
        "Diagramme de Gantt",
        "Suivi d'avancement et indicateurs",
        "Gestion des parties prenantes",
        "Clôture de projet et retour d'expérience",
    ],
    "STAT101": [
        "Introduction aux statistiques",
        "Variables statistiques et tableaux de données",
        "Mesures de tendance centrale",
        "Mesures de dispersion",
        "Représentations graphiques",
        "Corrélation et régression linéaire",
        "Introduction à l'inférence statistique",
        "Tests d'hypothèses",
        "Applications sur données réelles",
    ],
    "COMM101": [
        "Techniques de communication",
        "Rédaction d'un rapport professionnel",
        "Prise de parole en public",
        "Communication non-verbale",
        "Gestion des conflits",
        "Présentation PowerPoint efficace",
        "Rédaction d'emails professionnels",
    ],
}

EVALUATIONS = [
    ("Contrôle 1",      1.0),
    ("Contrôle 2",      1.0),
    ("Examen Final",    2.0),
]


# ════════════════════════════════════════════════════════════════════════════
# GÉNÉRATEURS DE NOTES RÉALISTES
# ════════════════════════════════════════════════════════════════════════════

def generate_realistic_grade(student_idx, course_idx, eval_idx):
    """
    Génère une note réaliste en tenant compte du profil de l'étudiant.
    Les 5 premiers étudiants sont forts, les 5 derniers plus faibles.
    """
    random.seed(student_idx * 100 + course_idx * 10 + eval_idx)

    # Profil de base
    if student_idx < 4:          # Très bons
        base = random.gauss(16, 1.5)
    elif student_idx < 8:        # Bons
        base = random.gauss(14, 2.0)
    elif student_idx < 14:       # Moyens
        base = random.gauss(11, 2.5)
    else:                        # En difficulté
        base = random.gauss(8, 3.0)

    # Légère progression dans le temps
    progression = eval_idx * 0.5
    note = base + progression + random.uniform(-0.5, 0.5)

    return round(max(0, min(20, note)), 1)


def generate_absence_pattern(student_idx, session_total):
    """
    Génère un pattern d'absences réaliste.
    Quelques étudiants ont des problèmes d'assiduité.
    """
    random.seed(student_idx * 999)

    # Taux d'absence par profil
    if student_idx in [6, 13, 17]:   # Absentéistes notoires
        rate = random.uniform(0.25, 0.40)
    elif student_idx in [9, 15]:      # Quelques absences
        rate = random.uniform(0.10, 0.20)
    else:                             # Assidus
        rate = random.uniform(0.0, 0.08)

    absents = set()
    for i in range(session_total):
        if random.random() < rate:
            absents.add(i)
    return absents


# ════════════════════════════════════════════════════════════════════════════
# GÉNÉRATION DES DATES DE SÉANCES
# ════════════════════════════════════════════════════════════════════════════

def generate_session_dates(nb_sessions, start=date(2024, 9, 9)):
    """
    Génère des dates de séances réparties sur la semaine (lundi à vendredi).
    Exclut les weekends.
    """
    dates = []
    current = start
    while len(dates) < nb_sessions:
        if current.weekday() < 5:  # Lundi à vendredi
            dates.append(current)
        current += timedelta(days=random.randint(2, 5))
    return dates


# ════════════════════════════════════════════════════════════════════════════
# SCRIPT PRINCIPAL
# ════════════════════════════════════════════════════════════════════════════

def reset_db():
    """Supprime toutes les données sauf les users."""
    print("  [RESET] Suppression des données existantes...")
    with get_db() as db:
        db.query(Attendance).delete()
        db.query(Grade).delete()
        db.query(Session).delete()
        db.query(Course).delete()
        db.query(Student).delete()
    print("  [RESET] Base nettoyée (users conservés).")


def seed_students(db):
    """Insère les 20 étudiants."""
    students = []
    for last, first, email, bdate in ETUDIANTS:
        # Vérifier si déjà existant
        existing = db.query(Student).filter(Student.email == email).first()
        if existing:
            students.append(existing)
            continue
        s = Student(
            last_name  = last,
            first_name = first,
            email      = email,
            birth_date = date.fromisoformat(bdate),
            is_active  = True,
        )
        db.add(s)
        students.append(s)

    db.flush()
    print(f"  [OK] {len(students)} étudiants insérés.")
    return students


def seed_courses(db):
    """Insère les 5 cours."""
    courses = []
    for c in COURS:
        existing = db.query(Course).filter(Course.code == c["code"]).first()
        if existing:
            courses.append(existing)
            continue
        course = Course(
            code        = c["code"],
            label       = c["label"],
            total_hours = c["total_hours"],
            teacher     = c["teacher"],
            description = c["description"],
            is_active   = True,
        )
        db.add(course)
        courses.append(course)

    db.flush()
    print(f"  [OK] {len(courses)} cours insérés.")
    return courses


def seed_sessions_and_attendance(db, courses, students):
    """
    Génère les séances et les présences pour chaque cours.
    Environ 8 à 10 séances par cours, 3 mois de cours.
    """
    total_sessions = 0
    total_att      = 0

    for c_idx, course in enumerate(courses):
        themes   = THEMES.get(course.code, ["Séance de cours"] * 10)
        nb_sessions = len(themes)
        dates    = generate_session_dates(nb_sessions,
                                          start=date(2024, 9, 9) + timedelta(days=c_idx))

        for s_idx, (session_date, theme) in enumerate(zip(dates, themes)):
            # Créer la séance
            session = Session(
                course_id = course.id,
                date      = session_date,
                duration  = 1.5 if s_idx % 3 == 0 else 2.0,
                topic     = theme,
                notes     = f"Cours dispensé normalement. {nb_sessions - s_idx - 1} séance(s) restante(s).",
            )
            db.add(session)
            db.flush()
            total_sessions += 1

            # Générer les présences pour chaque étudiant
            for st_idx, student in enumerate(students):
                absent_sessions = generate_absence_pattern(st_idx, nb_sessions)
                att = Attendance(
                    session_id = session.id,
                    student_id = student.id,
                    is_absent  = s_idx in absent_sessions,
                    is_excused = False,
                )
                db.add(att)
                total_att += 1

        db.flush()

    print(f"  [OK] {total_sessions} séances insérées.")
    print(f"  [OK] {total_att} enregistrements de présence insérés.")


def seed_grades(db, courses, students):
    """Génère 3 évaluations par cours pour chaque étudiant."""
    total_grades = 0

    eval_dates = [
        date(2024, 10, 5),
        date(2024, 11, 9),
        date(2024, 12, 14),
    ]

    for c_idx, course in enumerate(courses):
        for ev_idx, (eval_label, coeff) in enumerate(EVALUATIONS):
            for st_idx, student in enumerate(students):
                note = generate_realistic_grade(st_idx, c_idx, ev_idx)

                # Vérifier si déjà existant
                from sqlalchemy import and_
                existing = db.query(Grade).filter(
                    and_(Grade.student_id == student.id,
                         Grade.course_id  == course.id,
                         Grade.label      == eval_label)
                ).first()
                if existing:
                    continue

                grade = Grade(
                    student_id  = student.id,
                    course_id   = course.id,
                    grade       = note,
                    coefficient = coeff,
                    label       = eval_label,
                    date        = eval_dates[ev_idx],
                )
                db.add(grade)
                total_grades += 1

    db.flush()
    print(f"  [OK] {total_grades} notes insérées ({len(EVALUATIONS)} évaluations × {len(courses)} cours × {len(students)} étudiants).")


def print_summary(db):
    """Affiche un résumé des données insérées."""
    from sqlalchemy import func

    nb_students = db.query(func.count(Student.id)).filter(Student.is_active == True).scalar()
    nb_courses  = db.query(func.count(Course.id)).filter(Course.is_active == True).scalar()
    nb_sessions = db.query(func.count(Session.id)).scalar()
    nb_grades   = db.query(func.count(Grade.id)).scalar()
    nb_att      = db.query(func.count(Attendance.id)).scalar()
    nb_abs      = db.query(func.count(Attendance.id)).filter(Attendance.is_absent == True).scalar()
    avg_grade   = db.query(func.avg(Grade.grade)).scalar()

    pres_rate = round((nb_att - nb_abs) / nb_att * 100, 1) if nb_att > 0 else 0

    print()
    print("╔══════════════════════════════════════════════════════╗")
    print("║           RÉSUMÉ DES DONNÉES DE DÉMO                ║")
    print("╠══════════════════════════════════════════════════════╣")
    print(f"║  Étudiants       : {nb_students:<4}                               ║")
    print(f"║  Cours           : {nb_courses:<4}                               ║")
    print(f"║  Séances         : {nb_sessions:<4}                               ║")
    print(f"║  Notes           : {nb_grades:<4}                               ║")
    print(f"║  Présences       : {nb_att:<4}  ({pres_rate}% de présence)         ║")
    print(f"║  Absences        : {nb_abs:<4}                               ║")
    print(f"║  Moyenne globale : {round(float(avg_grade), 2) if avg_grade else '—':<5}/ 20                        ║")
    print("╠══════════════════════════════════════════════════════╣")
    print("║  Comptes :                                          ║")
    print("║    admin   / admin123    (Administrateur)           ║")
    print("║    teacher / teacher123  (Enseignant)               ║")
    print("╚══════════════════════════════════════════════════════╝")
    print()
    print("  Lancez l'application : python app.py")
    print("  Accès               : http://127.0.0.1:8050")
    print()


def main():
    reset_flag = "--reset" in sys.argv

    print()
    print("══════════════════════════════════════════════════════")
    print("  SGA — Script de données de démonstration")
    print("══════════════════════════════════════════════════════")
    print()

    # Initialiser la DB
    print("[1/5] Initialisation de la base de données...")
    init_db()
    print("  [OK] Tables créées.")

    # Reset si demandé
    if reset_flag:
        print("[RESET] Remise à zéro...")
        reset_db()

    print("[2/5] Insertion des étudiants...")
    print("[3/5] Insertion des cours...")
    print("[4/5] Génération des séances et présences...")
    print("[5/5] Génération des notes...")
    print()

    with get_db() as db:
        students = seed_students(db)
        courses  = seed_courses(db)
        seed_sessions_and_attendance(db, courses, students)
        seed_grades(db, courses, students)

    print()
    print("  Génération terminée avec succès !")

    with get_db() as db:
        print_summary(db)


if __name__ == "__main__":
    main()
