"""
components/tables.py — Composants tables réutilisables
Tous les composants de tableau, filtres et pagination du SGA.
"""

from dash import html, dash_table


def action_buttons(row_id, prefix, show_view=True, show_edit=True, show_delete=True):
    """
    Génère les boutons d'action pour une ligne de tableau.
    Utilise Font Awesome exclusivement.
    """
    btns = []
    if show_view:
        btns.append(html.Button(
            html.I(className="fa-solid fa-eye"),
            id={"type": f"{prefix}-btn-view", "index": row_id},
            className="btn btn-icon btn-sm btn-view",
            **{"data-tooltip": "Voir le détail"},
            n_clicks=0,
        ))
    if show_edit:
        btns.append(html.Button(
            html.I(className="fa-solid fa-pen-to-square"),
            id={"type": f"{prefix}-btn-edit", "index": row_id},
            className="btn btn-icon btn-sm btn-edit",
            **{"data-tooltip": "Modifier"},
            n_clicks=0,
        ))
    if show_delete:
        btns.append(html.Button(
            html.I(className="fa-solid fa-trash"),
            id={"type": f"{prefix}-btn-delete", "index": row_id},
            className="btn btn-icon btn-sm btn-delete",
            **{"data-tooltip": "Supprimer"},
            n_clicks=0,
        ))
    return html.Div(btns, className="action-btns")


def progress_bar(value, label="", show_label=True, size="md"):
    """
    Barre de progression stylée.
    value : 0-100
    """
    if value >= 80:
        cls = "success"
    elif value >= 40:
        cls = ""
    elif value >= 20:
        cls = "warning"
    else:
        cls = "danger"

    height = "10px" if size == "lg" else "7px"

    return html.Div(
        className="progress-bar-wrapper",
        children=[
            html.Div(
                className="progress-bar-label",
                children=[
                    html.Span(label),
                    html.Span(f"{value}%", style={"fontWeight": "600"}),
                ],
            ) if show_label else None,
            html.Div(
                className="progress-bar-track",
                style={"height": height},
                children=[
                    html.Div(
                        className=f"progress-bar-fill {cls}",
                        style={"width": f"{value}%"},
                    )
                ],
            ),
        ],
    )


def empty_state(icon, title, subtitle=None, action=None):
    """Affichage 'état vide' pour les listes sans données."""
    return html.Div(
        style={"textAlign": "center", "padding": "48px 20px"},
        children=[
            html.Div(
                html.I(className=f"fa-solid {icon}",
                       style={"fontSize": "2.8rem", "color": "#e2e8f0"}),
                style={"marginBottom": "16px"},
            ),
            html.Div(title, style={"fontSize": "1rem", "fontWeight": "600",
                                    "color": "#6b7280", "marginBottom": "6px"}),
            html.Div(subtitle, style={"fontSize": "0.84rem", "color": "#9ca3af",
                                       "marginBottom": "20px"}) if subtitle else None,
            action,
        ],
    )


def table_filter_bar(filters, prefix):
    """
    Barre de filtres réutilisable au-dessus d'un tableau.
    filters : liste de dicts {id, placeholder, type}
    """
    from dash import dcc
    items = []
    for f in filters:
        if f.get("type") == "dropdown":
            items.append(
                dcc.Dropdown(
                    id=f["id"],
                    options=f.get("options", []),
                    placeholder=f["placeholder"],
                    clearable=True,
                    style={"minWidth": "160px", "fontSize": "0.85rem"},
                )
            )
        else:
            items.append(
                html.Div(
                    [
                        html.I(className="fa-solid fa-magnifying-glass",
                               style={"position": "absolute", "left": "10px",
                                      "top": "50%", "transform": "translateY(-50%)",
                                      "color": "#9ca3af", "fontSize": "0.8rem",
                                      "pointerEvents": "none"}),
                        dcc.Input(
                            id=f["id"],
                            type="text",
                            placeholder=f["placeholder"],
                            debounce=True,
                            style={"paddingLeft": "32px", "width": "220px",
                                   "fontSize": "0.85rem"},
                            className="form-control",
                        ),
                    ],
                    style={"position": "relative"},
                )
            )
    return html.Div(
        items,
        style={"display": "flex", "gap": "10px", "alignItems": "center",
               "flexWrap": "wrap"},
    )
