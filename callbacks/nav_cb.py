"""
callbacks/nav_cb.py — Callbacks de navigation globale
- Mise en évidence du lien actif dans le header
- Gestion de la recherche globale
- Breadcrumb dynamique
NOTE : Ces callbacks sont enregistrés automatiquement au démarrage car
       nav_cb est importé dans callbacks/__init__.py
"""

from dash import callback, Output, Input, State, no_update, html, dcc, ctx


# ── Recherche globale ─────────────────────────────────────────────────────────
@callback(
    Output("url", "pathname"),
    Input("global-search-input", "n_submit"),
    State("global-search-input", "value"),
    prevent_initial_call=True,
)
def global_search_redirect(n_submit, query):
    """
    La recherche globale redirige vers la liste étudiants
    avec le terme pré-rempli (implémentation extensible).
    Pour l'instant : redirect vers /students si recherche non vide.
    """
    if query and query.strip():
        return "/students"
    return no_update
