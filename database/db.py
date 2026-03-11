"""
database/db.py — Gestion de la connexion SQLAlchemy
FIX : expire_on_commit=False pour éviter le détachement des objets
      après fermeture de la session (erreur "not bound to a Session")
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, scoped_session
from contextlib import contextmanager

from config import DB_URL, DEFAULT_USERS
from database.models import Base, User


IS_SQLITE = DB_URL.startswith("sqlite")


# ─── Engine SQLAlchemy ────────────────────────────────────────────────────────
engine_kwargs = {"echo": False}
if IS_SQLITE:
    engine_kwargs["connect_args"] = {"check_same_thread": False}

engine = create_engine(DB_URL, **engine_kwargs)

if IS_SQLITE:
    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()


# ─── Session Factory ──────────────────────────────────────────────────────────
# FIX CRITIQUE : expire_on_commit=False
# Sans ça, SQLAlchemy marque tous les objets comme "expirés" après le commit,
# et toute tentative d'accéder à leurs attributs hors session lève :
# "Instance is not bound to a Session"
SessionFactory = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=True,
    expire_on_commit=False,   # ← FIX
)
ScopedSession = scoped_session(SessionFactory)


# ─── Context Manager ──────────────────────────────────────────────────────────
@contextmanager
def get_db():
    """
    Session DB avec commit/rollback automatique.
    expire_on_commit=False garantit que les objets restent
    accessibles après la fermeture du context manager.
    """
    session = ScopedSession()
    try:
        yield session
        session.commit()
    except Exception as e:
        session.rollback()
        raise e
    finally:
        ScopedSession.remove()   # FIX : remove() au lieu de close()
                                  # libère proprement la session scopée


# ─── Initialisation ───────────────────────────────────────────────────────────
def init_db():
    import hashlib
    Base.metadata.create_all(bind=engine)
    print("[DB] Tables vérifiées / créées avec succès.")

    session = SessionFactory()
    try:
        if session.query(User).count() == 0:
            for username, info in DEFAULT_USERS.items():
                pwd_hash = hashlib.sha256(info["password"].encode()).hexdigest()
                user = User(
                    username      = username,
                    password_hash = pwd_hash,
                    role          = info["role"],
                    full_name     = info["name"],
                )
                session.add(user)
            session.commit()
            print("[DB] Utilisateurs par défaut insérés.")
        else:
            print("[DB] Utilisateurs déjà présents, skip.")
    except Exception as e:
        session.rollback()
        print(f"[DB] Erreur init utilisateurs : {e}")
    finally:
        session.close()


# ─── Helpers ──────────────────────────────────────────────────────────────────
def get_all(model):
    with get_db() as db:
        return db.query(model).all()

def get_by_id(model, record_id):
    with get_db() as db:
        return db.query(model).filter(model.id == record_id).first()

def safe_add(record):
    with get_db() as db:
        try:
            db.add(record)
            db.flush()
            db.refresh(record)
            return True, record
        except Exception as e:
            return False, str(e)

def safe_delete(model, record_id):
    with get_db() as db:
        try:
            record = db.query(model).filter(model.id == record_id).first()
            if record:
                db.delete(record)
                return True, None
            return False, "Enregistrement introuvable."
        except Exception as e:
            return False, str(e)
