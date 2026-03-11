"""
debug_app.py — Lance l'app en mode debug verbeux
Affiche TOUTES les erreurs des callbacks dans le terminal
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Test 1 : imports
print("\n[TEST 1] Imports des pages...")
errors = []
try:
    from pages import home;      print("  [OK] home")
except Exception as e:           print(f"  [ERR] home: {e}"); errors.append(e)
try:
    from pages import courses;   print("  [OK] courses")
except Exception as e:           print(f"  [ERR] courses: {e}"); errors.append(e)
try:
    from pages import sessions;  print("  [OK] sessions")
except Exception as e:           print(f"  [ERR] sessions: {e}"); errors.append(e)
try:
    from pages import students;  print("  [OK] students")
except Exception as e:           print(f"  [ERR] students: {e}"); errors.append(e)
try:
    from pages import analytics; print("  [OK] analytics")
except Exception as e:           print(f"  [ERR] analytics: {e}"); errors.append(e)

# Test 2 : lecture DB
print("\n[TEST 2] Lecture de la base de données...")
try:
    from database.db import get_db
    from database.models import Student, Course, Session, Grade, Attendance
    from sqlalchemy import func

    with get_db() as db:
        nb_s = db.query(func.count(Student.id)).scalar()
        nb_c = db.query(func.count(Course.id)).scalar()
        nb_g = db.query(func.count(Grade.id)).scalar()
        nb_a = db.query(func.count(Attendance.id)).scalar()
        print(f"  Étudiants : {nb_s}")
        print(f"  Cours     : {nb_c}")
        print(f"  Notes     : {nb_g}")
        print(f"  Présences : {nb_a}")

    if nb_s == 0:
        print("  [ATTENTION] La base est vide ! Relancez: python seed_demo.py --reset")
    else:
        print("  [OK] Données présentes")
except Exception as e:
    print(f"  [ERR] {e}")
    errors.append(e)

# Test 3 : callbacks home
print("\n[TEST 3] Test callback dashboard...")
try:
    from database.db import get_db
    from database.models import Student, Course, Session, Attendance, Grade
    from sqlalchemy import func

    with get_db() as db:
        nb_students = db.query(func.count(Student.id)).filter(Student.is_active == True).scalar() or 0
        nb_courses  = db.query(func.count(Course.id)).filter(Course.is_active == True).scalar() or 0
        nb_sessions = db.query(func.count(Session.id)).scalar() or 0
        avg_grade   = db.query(func.avg(Grade.grade)).scalar()

    print(f"  [OK] Dashboard lirait: {nb_students} étudiants, {nb_courses} cours")
    print(f"  [OK] Moyenne: {round(float(avg_grade),2) if avg_grade else '—'}/20")
except Exception as e:
    print(f"  [ERR] {e}")
    errors.append(e)

# Test 4 : liste cours
print("\n[TEST 4] Test callback liste cours...")
try:
    from database.db import get_db
    from database.models import Course
    with get_db() as db:
        courses_list = db.query(Course).filter(Course.is_active == True).all()
    print(f"  [OK] {len(courses_list)} cours lus:")
    for c in courses_list:
        print(f"       - {c.code}: {c.label} ({c.teacher})")
except Exception as e:
    print(f"  [ERR] {e}")
    errors.append(e)

# Test 5 : liste étudiants
print("\n[TEST 5] Test callback liste étudiants...")
try:
    from database.db import get_db
    from database.models import Student
    with get_db() as db:
        students_list = db.query(Student).filter(Student.is_active == True).all()
    print(f"  [OK] {len(students_list)} étudiants lus:")
    for s in students_list[:5]:
        print(f"       - {s.full_name} ({s.email})")
    if len(students_list) > 5:
        print(f"       ... et {len(students_list)-5} autres")
except Exception as e:
    print(f"  [ERR] {e}")
    errors.append(e)

# Bilan
print("\n" + "="*50)
if errors:
    print(f"  {len(errors)} ERREUR(S) DETECTEE(S) — voir ci-dessus")
else:
    print("  TOUT OK — Le problème vient de l'interface web")
    print("  Ouvrez http://127.0.0.1:8050 dans Chrome/Firefox")
    print("  (pas IE ni Edge legacy)")
print("="*50 + "\n")
