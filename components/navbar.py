"""
components/navbar.py — Logique de navigation et breadcrumb
Séparé de header.py pour la clarté architecturale.
Fournit : get_breadcrumb(), get_nav_structure(), is_active_route()
"""

from dash import html, dcc

# ─── Structure de navigation (source unique de vérité) ────────────────────────
NAV_STRUCTURE = {
    "/": {
        "label": "Tableau de Bord",
        "icon":  "fa-gauge-high",
        "parent": None,
    },
    "/courses": {
        "label": "Cours",
        "icon":  "fa-book-open",
        "parent": None,
        "children": ["/courses", "/courses/add", "/courses/progress"],
    },
    "/courses/add": {
        "label": "Ajouter un Cours",
        "icon":  "fa-plus",
        "parent": "/courses",
    },
    "/courses/progress": {
        "label": "Progression",
        "icon":  "fa-chart-line",
        "parent": "/courses",
    },
    "/sessions": {
        "label": "Séances",
        "icon":  "fa-chalkboard-user",
        "parent": None,
        "children": ["/sessions", "/sessions/add", "/sessions/attendance"],
    },
    "/sessions/add": {
        "label": "Nouvelle Séance",
        "icon":  "fa-pen-to-square",
        "parent": "/sessions",
    },
    "/sessions/attendance": {
        "label": "Feuilles de Présence",
        "icon":  "fa-clipboard-check",
        "parent": "/sessions",
    },
    "/students": {
        "label": "Étudiants",
        "icon":  "fa-user-graduate",
        "parent": None,
        "children": ["/students", "/students/profile",
                     "/students/grades", "/students/excel"],
    },
    "/students/profile": {
        "label": "Fiche Étudiant",
        "icon":  "fa-id-card",
        "parent": "/students",
    },
    "/students/grades": {
        "label": "Gestion des Notes",
        "icon":  "fa-star-half-stroke",
        "parent": "/students",
    },
    "/students/excel": {
        "label": "Import / Export Excel",
        "icon":  "fa-file-excel",
        "parent": "/students",
    },
    "/analytics/grades": {
        "label": "Distribution des Notes",
        "icon":  "fa-chart-bar",
        "parent": "/analytics",
    },
    "/analytics/trends": {
        "label": "Évolution des Moyennes",
        "icon":  "fa-chart-line",
        "parent": "/analytics",
    },
    "/analytics/attendance": {
        "label": "Rapport de Présence",
        "icon":  "fa-clipboard-list",
        "parent": "/analytics",
    },
}


def get_breadcrumb(pathname):
    """
    Retourne un composant breadcrumb pour le pathname donné.
    Ex: /courses/progress → Accueil > Cours > Progression
    """
    if not pathname or pathname == "/":
        return None

    info = NAV_STRUCTURE.get(pathname)
    if not info:
        return None

    crumbs = []

    # Accueil
    crumbs.append(
        dcc.Link(
            [html.I(className="fa-solid fa-house",
                    style={"fontSize": "0.75rem"})],
            href="/",
            className="breadcrumb-link",
        )
    )

    # Parent éventuel
    parent = info.get("parent")
    if parent and parent in NAV_STRUCTURE:
        parent_info = NAV_STRUCTURE[parent]
        crumbs.append(html.Span(
            html.I(className="fa-solid fa-chevron-right"),
            style={"fontSize": "0.65rem", "color": "#9ca3af", "margin": "0 6px"},
        ))
        crumbs.append(
            dcc.Link(parent_info["label"], href=parent, className="breadcrumb-link")
        )

    # Page courante
    crumbs.append(html.Span(
        html.I(className="fa-solid fa-chevron-right"),
        style={"fontSize": "0.65rem", "color": "#9ca3af", "margin": "0 6px"},
    ))
    crumbs.append(
        html.Span(info["label"],
                  style={"color": "#1c1c2e", "fontWeight": "500", "fontSize": "0.83rem"})
    )

    return html.Nav(
        crumbs,
        style={"display": "flex", "alignItems": "center",
               "padding": "6px 0", "marginBottom": "12px"},
        className="breadcrumb",
    )


def is_active_route(pathname, route):
    """Retourne True si pathname correspond à route ou à l'un de ses enfants."""
    if not pathname:
        return False
    route_info = NAV_STRUCTURE.get(route, {})
    children   = route_info.get("children", [route])
    return pathname in children or pathname == route


def get_page_title(pathname):
    """Retourne le titre et l'icône de la page courante."""
    info = NAV_STRUCTURE.get(pathname or "/")
    if info:
        return info.get("label", ""), info.get("icon", "fa-circle")
    return "Page introuvable", "fa-question"


def sidebar_link(label, icon, href, active=False):
    """
    Lien de sidebar (utilisable dans un futur layout sidebar).
    """
    return dcc.Link(
        [
            html.I(className=f"fa-solid {icon}",
                   style={"width": "18px", "textAlign": "center",
                          "marginRight": "10px"}),
            html.Span(label),
        ],
        href=href,
        className=f"sidebar-link {'active' if active else ''}",
        style={
            "display": "flex", "alignItems": "center",
            "padding": "9px 14px", "borderRadius": "8px",
            "color": "#1a237e" if active else "#6b7280",
            "background": "#e8eaf6" if active else "transparent",
            "fontWeight": "600" if active else "400",
            "fontSize": "0.87rem", "textDecoration": "none",
            "transition": "all 0.15s",
        },
    )
