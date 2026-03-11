"""
components/header.py — Header global du SGA
FIX : btn-logout ajouté dans le user dropdown (requis par handle_logout dans app.py)
"""

from dash import html, dcc


def build_nav_item(label, icon, href=None, children=None):
    chevron = html.I(className="fa-solid fa-chevron-down nav-chevron") if children else None
    link_content = [html.I(className=f"fa-solid {icon}"), html.Span(label), chevron]
    link_content = [el for el in link_content if el is not None]

    if children:
        trigger  = html.Div(link_content, className="nav-link",
                            id={"type": "nav-trigger", "index": label})
        dropdown = html.Div([build_dropdown_item(*item) for item in children],
                            className="nav-dropdown")
        return html.Div([trigger, dropdown], className="nav-item")
    else:
        return html.Div(
            dcc.Link(link_content, href=href or "/", className="nav-link"),
            className="nav-item",
        )


def build_dropdown_item(label, icon, href):
    return dcc.Link(
        [html.I(className=f"fa-solid {icon}"), html.Span(label)],
        href=href, className="nav-dropdown-item",
    )


def get_header(username="Admin", role="admin"):
    initials = "".join([w[0].upper() for w in username.split()[:2]]) if username else "U"

    nav_items = [
        build_nav_item("Tableau de Bord", "fa-gauge-high", href="/"),
        build_nav_item("Cours", "fa-book-open", children=[
            ("Liste des Cours",     "fa-list",          "/courses"),
            ("Ajouter un Cours",    "fa-plus",          "/courses/add"),
            ("Progression",         "fa-chart-line",    "/courses/progress"),
        ]),
        build_nav_item("Séances", "fa-chalkboard-user", children=[
            ("Enregistrer une Séance",  "fa-pen-to-square",      "/sessions/add"),
            ("Historique",              "fa-clock-rotate-left",  "/sessions"),
            ("Feuilles de Présence",    "fa-clipboard-check",    "/sessions/attendance"),
        ]),
        build_nav_item("Étudiants", "fa-user-graduate", children=[
            ("Liste des Étudiants",   "fa-users",            "/students"),
            ("Fiche Étudiant",        "fa-id-card",          "/students/profile"),
            ("Gestion des Notes",     "fa-star-half-stroke", "/students/grades"),
            ("Import / Export Excel", "fa-file-excel",       "/students/excel"),
        ]),
        build_nav_item("Analyses", "fa-chart-pie", children=[
            ("Distribution des Notes", "fa-chart-bar",      "/analytics/grades"),
            ("Évolution des Moyennes", "fa-chart-line",     "/analytics/trends"),
            ("Rapport de Présence",    "fa-clipboard-list", "/analytics/attendance"),
        ]),
    ]

    # ── User dropdown avec logout ─────────────────────────────────────────────
    user_dropdown = html.Div(
        className="nav-item",
        children=[
            # Trigger avatar
            html.Div(
                className="header-user nav-link",
                id="header-user-menu",
                **{"data-tooltip": f"Connecté : {username}"},
                children=[
                    html.Div(initials, className="user-avatar"),
                    html.Span(username, style={"fontSize": "0.83rem"}),
                    html.I(className="fa-solid fa-chevron-down nav-chevron",
                           style={"fontSize": "0.7rem", "opacity": "0.7"}),
                ],
            ),
            # Dropdown user
            html.Div(
                className="nav-dropdown",
                style={"right": "0", "left": "auto", "minWidth": "180px"},
                children=[
                    html.Div(
                        [html.I(className="fa-solid fa-user",
                                style={"color": "#1a237e", "marginRight": "8px",
                                       "width": "16px", "textAlign": "center"}),
                         html.Span(username, style={"fontWeight": "500"})],
                        style={"padding": "10px 13px", "fontSize": "0.85rem",
                               "borderBottom": "1px solid #f1f5f9", "color": "#1c1c2e"},
                    ),
                    html.Div(
                        [html.I(className="fa-solid fa-shield-halved",
                                style={"marginRight": "8px", "width": "16px",
                                       "textAlign": "center", "color": "#1a237e"}),
                         html.Span("Rôle : " + role.capitalize())],
                        style={"padding": "8px 13px", "fontSize": "0.8rem",
                               "color": "#9ca3af", "borderBottom": "1px solid #f1f5f9"},
                    ),
                    # Bouton logout — ID requis par handle_logout dans app.py
                    html.Button(
                        [html.I(className="fa-solid fa-right-from-bracket",
                                style={"marginRight": "8px", "width": "16px",
                                       "textAlign": "center", "color": "#e53935"}),
                         html.Span("Se déconnecter",
                                   style={"color": "#e53935"})],
                        id="btn-logout",
                        n_clicks=0,
                        style={"width": "100%", "padding": "10px 13px",
                               "background": "transparent", "border": "none",
                               "cursor": "pointer", "textAlign": "left",
                               "fontSize": "0.85rem", "display": "flex",
                               "alignItems": "center", "borderRadius": "0 0 8px 8px"},
                        className="nav-dropdown-item",
                    ),
                ],
            ),
        ],
    )

    return html.Header(
        id="sga-header",
        children=[
            # Gauche : Brand
            dcc.Link(
                href="/",
                className="header-brand",
                children=[
                    html.Div(html.I(className="fa-solid fa-graduation-cap"),
                             className="header-brand-icon"),
                    html.Div([
                        html.Span("Academic Management System",
                                  className="header-brand-title"),
                        html.Span("Système de Gestion Académique",
                                  className="header-brand-sub"),
                    ], className="header-brand-text"),
                ],
            ),
            # Centre : Navigation
            html.Nav(nav_items, className="header-nav"),
            # Droite : Search + User
            html.Div(
                className="header-search",
                children=[
                    html.Div(
                        className="search-box",
                        children=[
                            html.I(className="fa-solid fa-magnifying-glass"),
                            dcc.Input(
                                id="global-search-input",
                                type="text",
                                placeholder="Rechercher... (Ctrl+K)",
                                className="search-input",
                                debounce=True,
                            ),
                        ],
                    ),
                    html.Div(style={"width": "1px", "height": "24px",
                                    "background": "rgba(255,255,255,0.2)",
                                    "margin": "0 6px"}),
                    user_dropdown,
                ],
            ),
        ],
    )
