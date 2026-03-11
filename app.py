"""
app.py — Point d'entrée principal du SGA
FIX CRITIQUE : Import de toutes les pages AU DÉMARRAGE pour enregistrer
               leurs callbacks avant que Dash ne démarre.
"""

import dash
from dash import html, dcc, callback, Output, Input, State, no_update

from config import (
    APP_TITLE,
    FA_CDN,
    DEBUG,
    HOST,
    PORT,
    SECRET_KEY,
    AUTO_INIT_DB,
    RUN_STARTUP_MIGRATION,
)
from database.db import init_db
from database.migration import run_migration
from components.header import get_header
from components.footer import get_footer

# ═══════════════════════════════════════════════════════════════════════════
# IMPORT OBLIGATOIRE DE TOUTES LES PAGES ICI
# Dash enregistre les callbacks au moment de l'import du module.
# Si la page n'est pas importée au démarrage, ses callbacks n'existent pas.
# ═══════════════════════════════════════════════════════════════════════════
from pages import login
from pages import home
try:
    from pages import courses
except Exception as e:
    print(f"[WARN] courses: {e}")
try:
    from pages import sessions
except Exception as e:
    print(f"[WARN] sessions: {e}")
try:
    from pages import students
except Exception as e:
    print(f"[WARN] students: {e}")
try:
    from pages import analytics
except Exception as e:
    print(f"[WARN] analytics: {e}")


# ─── Initialisation Dash ──────────────────────────────────────────────────────
app = dash.Dash(
    __name__,
    suppress_callback_exceptions=True,
    title=APP_TITLE,
    meta_tags=[
        {"name": "viewport",    "content": "width=device-width, initial-scale=1"},
        {"name": "description", "content": "Système de Gestion Académique"},
        {"charset": "UTF-8"},
    ],
    external_stylesheets=[FA_CDN],
)
server = app.server
server.config["SECRET_KEY"] = SECRET_KEY


_BOOTSTRAPPED = False


def bootstrap_app():
    global _BOOTSTRAPPED
    if _BOOTSTRAPPED:
        return

    if AUTO_INIT_DB or RUN_STARTUP_MIGRATION:
        init_db()
    if RUN_STARTUP_MIGRATION:
        run_migration()

    _BOOTSTRAPPED = True


bootstrap_app()


# ─── Layout Global ────────────────────────────────────────────────────────────
app.layout = html.Div(
    id="app-wrapper",
    children=[
        dcc.Location(id="url", refresh=False),
        dcc.Store(id="session-store", storage_type="session"),
        html.Div(id="app-shell"),
    ],
)


# ─── Routing ─────────────────────────────────────────────────────────────────
@callback(
    Output("app-shell", "children"),
    Input("url",           "pathname"),
    Input("session-store", "data"),
)
def render_page(pathname, session):
    if not session or "user_id" not in session:
        return login.layout()

    username = session.get("name", session.get("username", "Utilisateur"))
    role     = session.get("role", "viewer")
    content  = _route(pathname or "/")
    return html.Div([
        get_header(username=username, role=role),
        html.Main(content, id="page-content", className="fade-in"),
        get_footer(),
    ])


def _route(pathname):
    routes = {
        "/":                        home.layout,
        "/dashboard":               home.layout,
        "/courses":                 courses.layout,
        "/courses/add":             courses.layout_add,
        "/courses/progress":        courses.layout_progress,
        "/sessions":                sessions.layout,
        "/sessions/add":            sessions.layout_add,
        "/sessions/attendance":     sessions.layout_attendance,
        "/students":                students.layout,
        "/students/profile":        students.layout_profile,
        "/students/grades":         students.layout_grades,
        "/students/excel":          students.layout_excel,
        "/analytics/grades":        analytics.layout_grades,
        "/analytics/trends":        analytics.layout_trends,
        "/analytics/attendance":    analytics.layout_attendance,
    }
    fn = routes.get(pathname)
    if fn:
        try:
            return fn()
        except Exception as e:
            return _error_page(str(e))
    return _not_found_page(pathname)


# ─── LOGIN ────────────────────────────────────────────────────────────────────
@callback(
    Output("login-error",   "children"),
    Output("session-store", "data"),
    Input("login-btn",      "n_clicks"),
    Input("login-password", "n_submit"),
    Input("login-username", "n_submit"),
    State("login-username", "value"),
    State("login-password", "value"),
    prevent_initial_call=True,
)
def handle_login(n_clicks, pw_submit, un_submit, username, password):
    import hashlib
    from datetime import datetime
    from database.db import get_db
    from database.models import User

    if not username or not password:
        return (html.Div([html.I(className="fa-solid fa-circle-exclamation"),
                          " Veuillez remplir tous les champs."],
                         className="alert alert-warning"), no_update)

    pwd_hash = hashlib.sha256(password.strip().encode()).hexdigest()
    try:
        with get_db() as db:
            user = db.query(User).filter(
                User.username      == username.strip(),
                User.password_hash == pwd_hash,
                User.is_active     == True,
            ).first()
            if user:
                user.last_login = datetime.now()
                return None, {
                    "user_id":  user.id,
                    "username": user.username,
                    "role":     user.role,
                    "name":     user.full_name or user.username,
                }
            return (html.Div([html.I(className="fa-solid fa-circle-xmark"),
                              " Identifiant ou mot de passe incorrect."],
                             className="alert alert-danger"), no_update)
    except Exception as e:
        return (html.Div([html.I(className="fa-solid fa-triangle-exclamation"),
                          f" Erreur : {str(e)}"], className="alert alert-danger"), no_update)


# ─── LOGOUT ───────────────────────────────────────────────────────────────────
@callback(
    Output("session-store", "data", allow_duplicate=True),
    Input("btn-logout",     "n_clicks"),
    prevent_initial_call=True,
)
def handle_logout(n_clicks):
    if n_clicks:
        return None
    return no_update


# ─── Pages utilitaires ────────────────────────────────────────────────────────
def _not_found_page(pathname):
    return html.Div(className="fade-in",
        style={"textAlign": "center", "padding": "80px 20px"},
        children=[
            html.I(className="fa-solid fa-map-location-dot",
                   style={"fontSize": "3.5rem", "color": "#e2e8f0",
                          "display": "block", "marginBottom": "20px"}),
            html.H2("Page introuvable",
                    style={"fontSize": "1.5rem", "marginBottom": "8px"}),
            html.P(f"Route « {pathname} » introuvable.",
                   style={"color": "#9ca3af", "marginBottom": "28px"}),
            dcc.Link([html.I(className="fa-solid fa-house",
                             style={"marginRight": "6px"}), "Retour"],
                     href="/", className="btn btn-primary"),
        ])


def _error_page(msg):
    return html.Div(className="alert alert-danger fade-in",
        style={"margin": "40px auto", "maxWidth": "600px"},
        children=[
            html.I(className="fa-solid fa-circle-xmark"),
            html.Div([html.Strong("Erreur chargement : "), msg],
                     style={"marginLeft": "8px"}),
        ])


# ─── Démarrage ────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("=" * 55)
    print(f"  {APP_TITLE}")
    print("=" * 55)
    bootstrap_app()
    print(f"[BOOT] http://127.0.0.1:{PORT}")
    print("=" * 55)
    app.run(debug=DEBUG, host=HOST, port=PORT)
