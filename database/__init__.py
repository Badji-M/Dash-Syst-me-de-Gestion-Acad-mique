"""
callbacks/__init__.py — Enregistrement automatique de tous les callbacks
Importé dans app.py au démarrage pour activer tous les callbacks transversaux.

ARCHITECTURE :
  - pages/*.py       → callbacks CRUD co-localisés (pattern Dash recommandé)
  - callbacks/*.py   → callbacks transversaux, validations live, interactions avancées

Les callbacks des pages sont enregistrés automatiquement lors de l'import des pages
via le routing dans app.py (_route). Les callbacks transversaux sont enregistrés ici.
"""

from callbacks import nav_cb        # Navigation globale + recherche
from callbacks import courses_cb    # Validation live code cours
from callbacks import sessions_cb   # Highlight checklist absences
from callbacks import students_cb   # Validation live email + reset form
from callbacks import analytics_cb  # Cache analytics + filtre summary
