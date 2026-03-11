"""
pages/login.py — Page d'authentification du SGA
IMPORTANT : Le callback handle_login est dans app.py (session-store y est déclaré).
            Ce fichier contient UNIQUEMENT le layout.
"""

from dash import html, dcc


def layout():
    """
    Layout login — PAS de dcc.Store, PAS de dcc.Location, PAS de callback.
    Tout cela est dans app.py pour éviter les conflits d'Output.
    """
    return html.Div(
        className="login-page",
        children=[
            html.Div(
                className="login-card",
                children=[

                    # Logo
                    html.Div(className="login-logo", children=[
                        html.Div(
                            html.I(className="fa-solid fa-graduation-cap"),
                            className="login-logo-icon",
                        ),
                        html.Div("Academic Management", className="login-logo-title"),
                        html.Div("Système de Gestion Académique",
                                 className="login-logo-sub"),
                    ]),

                    # Zone feedback
                    html.Div(id="login-error", style={"marginBottom": "12px"}),

                    # Username
                    html.Div(className="form-group", children=[
                        html.Label(
                            [html.I(className="fa-solid fa-user",
                                    style={"marginRight": "6px"}),
                             "Nom d'utilisateur"],
                            className="form-label required",
                        ),
                        dcc.Input(
                            id="login-username",
                            type="text",
                            placeholder="Entrez votre identifiant",
                            className="form-control",
                            style={"width": "100%"},
                            n_submit=0,
                            autoFocus=True,
                        ),
                    ]),

                    # Password
                    html.Div(className="form-group", children=[
                        html.Label(
                            [html.I(className="fa-solid fa-lock",
                                    style={"marginRight": "6px"}),
                             "Mot de passe"],
                            className="form-label required",
                        ),
                        dcc.Input(
                            id="login-password",
                            type="password",
                            placeholder="Entrez votre mot de passe",
                            className="form-control",
                            style={"width": "100%"},
                            n_submit=0,
                        ),
                    ]),

                    # Bouton
                    html.Button(
                        [html.I(className="fa-solid fa-right-to-bracket"),
                         " Se connecter"],
                        id="login-btn",
                        className="btn btn-primary",
                        style={"width": "100%", "justifyContent": "center",
                               "padding": "11px", "fontSize": "0.95rem",
                               "marginTop": "8px"},
                        n_clicks=0,
                    ),

                    # Aide
                    html.Div(
                        style={"textAlign": "center", "margin": "20px 0 16px",
                               "fontSize": "0.78rem", "color": "#9ca3af"},
                        children=[
                            html.Span("Compte démo : "),
                            html.Code("admin / admin123",
                                      style={"background": "#f1f5f9",
                                             "padding": "2px 6px",
                                             "borderRadius": "4px"}),
                        ],
                    ),

                    html.Div(
                        style={"textAlign": "center"},
                        children=[
                            html.I(className="fa-solid fa-shield-halved",
                                   style={"color": "#9ca3af", "marginRight": "5px",
                                          "fontSize": "0.78rem"}),
                            html.Span("Accès sécurisé — Données confidentielles",
                                      style={"fontSize": "0.76rem",
                                             "color": "#9ca3af"}),
                        ],
                    ),
                ],
            ),
        ],
    )
