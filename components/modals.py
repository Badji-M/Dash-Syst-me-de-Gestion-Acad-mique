"""
components/modals.py — Modals réutilisables
Modals de confirmation, d'information et de formulaire.
"""

from dash import html


def confirm_modal(modal_id, title, message, confirm_label="Confirmer",
                  confirm_class="btn-danger", confirm_icon="fa-trash"):
    """
    Modal de confirmation générique.
    Rendu visible via display block/none depuis un callback.
    """
    return html.Div(
        id=f"{modal_id}-overlay",
        className="modal-overlay",
        style={"display": "none"},
        children=[
            html.Div(
                className="modal-box",
                children=[
                    html.Div(
                        className="modal-header",
                        children=[
                            html.Span(
                                [html.I(className="fa-solid fa-triangle-exclamation",
                                        style={"color": "#f57f17", "marginRight": "8px"}),
                                 title],
                                className="modal-title",
                            ),
                            html.Button(
                                html.I(className="fa-solid fa-xmark"),
                                id=f"{modal_id}-close",
                                className="modal-close",
                                n_clicks=0,
                            ),
                        ],
                    ),
                    html.P(message, style={"fontSize": "0.9rem", "color": "#555",
                                           "lineHeight": "1.6"}),
                    html.Div(
                        className="modal-footer",
                        children=[
                            html.Button(
                                [html.I(className="fa-solid fa-xmark"), " Annuler"],
                                id=f"{modal_id}-cancel",
                                className="btn btn-ghost",
                                n_clicks=0,
                            ),
                            html.Button(
                                [html.I(className=f"fa-solid {confirm_icon}"),
                                 f" {confirm_label}"],
                                id=f"{modal_id}-confirm",
                                className=f"btn {confirm_class}",
                                n_clicks=0,
                            ),
                        ],
                    ),
                ],
            ),
        ],
    )


def form_modal(modal_id, title, body, footer_extra=None):
    """
    Modal contenant un formulaire.
    body : composants Dash à afficher dans le corps.
    """
    return html.Div(
        id=f"{modal_id}-overlay",
        className="modal-overlay",
        style={"display": "none"},
        children=[
            html.Div(
                className="modal-box",
                style={"maxWidth": "560px"},
                children=[
                    html.Div(
                        className="modal-header",
                        children=[
                            html.Span(title, className="modal-title"),
                            html.Button(
                                html.I(className="fa-solid fa-xmark"),
                                id=f"{modal_id}-close",
                                className="modal-close",
                                n_clicks=0,
                            ),
                        ],
                    ),
                    html.Div(body, style={"marginTop": "4px"}),
                    html.Div(
                        className="modal-footer",
                        children=footer_extra or [],
                    ),
                ],
            ),
        ],
    )
