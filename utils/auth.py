"""
utils/auth.py — Gestion de l'authentification et des rôles
Hash SHA-256, vérification credentials, contrôle des permissions.
"""

import hashlib
from database.db import get_db
from database.models import User
from config import ROLES


def hash_password(password: str) -> str:
    """Retourne le hash SHA-256 du mot de passe."""
    return hashlib.sha256(password.strip().encode()).hexdigest()


def verify_user(username: str, password: str):
    """
    Vérifie les credentials et retourne l'utilisateur si valide.
    Retourne (User, None) ou (None, error_message).
    """
    if not username or not password:
        return None, "Identifiant et mot de passe requis."

    pwd_hash = hash_password(password)

    try:
        with get_db() as db:
            user = db.query(User).filter(
                User.username      == username.strip(),
                User.password_hash == pwd_hash,
                User.is_active     == True,
            ).first()

            if not user:
                return None, "Identifiant ou mot de passe incorrect."

            # Mettre à jour last_login
            from datetime import datetime
            user.last_login = datetime.utcnow()

            session_data = {
                "user_id":  user.id,
                "username": user.username,
                "role":     user.role,
                "name":     user.full_name or user.username,
            }
            return session_data, None

    except Exception as e:
        return None, f"Erreur serveur : {str(e)}"


def has_permission(session: dict, permission: str) -> bool:
    """
    Vérifie si un utilisateur a une permission donnée.
    session : dict de session (user_id, role, ...)
    permission : 'read' | 'write' | 'delete' | 'export' | 'manage_users'
    """
    if not session or "role" not in session:
        return False
    role = session.get("role", "viewer")
    return permission in ROLES.get(role, [])


def require_role(session: dict, min_role: str) -> bool:
    """
    Vérifie si l'utilisateur a au moins le rôle spécifié.
    Hiérarchie : admin > teacher > viewer
    """
    hierarchy = {"admin": 3, "teacher": 2, "viewer": 1}
    if not session:
        return False
    user_level = hierarchy.get(session.get("role", "viewer"), 0)
    required   = hierarchy.get(min_role, 99)
    return user_level >= required


def change_password(user_id: int, old_password: str, new_password: str):
    """
    Change le mot de passe d'un utilisateur.
    Retourne (True, None) ou (False, error_message).
    """
    if len(new_password) < 6:
        return False, "Le nouveau mot de passe doit contenir au moins 6 caractères."

    try:
        with get_db() as db:
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                return False, "Utilisateur introuvable."
            if user.password_hash != hash_password(old_password):
                return False, "Ancien mot de passe incorrect."
            user.password_hash = hash_password(new_password)
        return True, None
    except Exception as e:
        return False, str(e)