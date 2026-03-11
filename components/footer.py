"""
components/footer.py — Footer global du SGA
Footer fixe en bas de chaque page.
"""

from dash import html
from config import APP_VERSION, SCHOOL_NAME
from datetime import datetime


def get_footer():
    """Retourne le composant footer de l'application."""
    year = datetime.now().year

    return html.Footer(
        id="sga-footer",
        children=[
            # ── Gauche ─────────────────────────────────────────────────────
            html.Div(
                className="footer-left",
                children=[
                    html.I(className="fa-solid fa-graduation-cap"),
                    html.Span(f"{SCHOOL_NAME} — Academic Management System v{APP_VERSION}"),
                ],
            ),

            # ── Droite ─────────────────────────────────────────────────────
            html.Div(
                className="footer-right",
                children=[
                    html.Span(
                        [
                            html.I(className="fa-regular fa-copyright",
                                   style={"marginRight": "4px"}),
                            f"{year} SGA. Tous droits réservés.",
                        ],
                    ),
                    html.Span("|", style={"opacity": "0.4"}),
                    html.A(
                        [html.I(className="fa-solid fa-shield-halved",
                                style={"marginRight": "4px"}),
                         "Confidentialité"],
                        href="#",
                        style={"textDecoration": "none", "color": "inherit"},
                    ),
                    html.A(
                        [html.I(className="fa-solid fa-circle-question",
                                style={"marginRight": "4px"}),
                         "Aide"],
                        href="#",
                        style={"textDecoration": "none", "color": "inherit"},
                    ),
                ],
            ),
        ],
    )
