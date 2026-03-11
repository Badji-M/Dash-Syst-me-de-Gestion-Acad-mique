"""
pages/sessions.py — Module 2 : Cahier de Texte & Présences
- Enregistrement de séance (cours, date, durée, thème)
- Appel numérique : checklist dynamique des étudiants
- Historique des séances filtrable par date / cours
- Vue feuilles de présence par séance
"""

from dash import html, dcc, callback, Output, Input, State, no_update, ctx, ALL
from datetime import date, datetime
import plotly.graph_objects as go

from database.db import get_db
from database.models import Course, Session, Student, Attendance
from components.tables import empty_state, progress_bar
from components.modals import confirm_modal
from sqlalchemy import func
from sqlalchemy.orm import joinedload


# ═══════════════════════════════════════════════════════════════════════════════
# LAYOUT PRINCIPAL — Historique des séances
# ═══════════════════════════════════════════════════════════════════════════════
def layout():
    return html.Div(
        className="fade-in",
        children=[
            # ── Page Header ──────────────────────────────────────────────
            html.Div(className="page-header", children=[
                html.Div([
                    html.H1("Cahier de Texte", className="page-title"),
                    html.P("Historique des séances et suivi pédagogique",
                           className="page-subtitle"),
                ], className="page-header-left"),
                html.Div(className="page-header-actions", children=[
                    dcc.Link(
                        [html.I(className="fa-solid fa-clipboard-check"), " Présences"],
                        href="/sessions/attendance",
                        className="btn btn-outline btn-sm",
                    ),
                    html.Button(
                        [html.I(className="fa-solid fa-plus"), " Nouvelle Séance"],
                        id="btn-open-add-session",
                        className="btn btn-primary btn-sm",
                        n_clicks=0,
                    ),
                ]),
            ]),

            # ── Feedback ─────────────────────────────────────────────────
            html.Div(id="session-feedback"),

            # ── Formulaire inline ─────────────────────────────────────────
            html.Div(id="session-form-container", children=_empty_session_form(),
                     style={"marginBottom": "20px"}),

            # ── Filtres + Tableau historique ──────────────────────────────
            html.Div(className="table-container", children=[
                html.Div(className="table-header", children=[
                    html.Div(
                        [html.I(className="fa-solid fa-clock-rotate-left"),
                         " Historique des Séances"],
                        className="table-title",
                    ),
                    html.Div(
                        style={"display": "flex", "gap": "10px", "alignItems": "center",
                               "flexWrap": "wrap"},
                        children=[
                            # Filtre par cours
                            dcc.Dropdown(
                                id="session-filter-course",
                                placeholder="Filtrer par cours",
                                clearable=True,
                                style={"minWidth": "180px", "fontSize": "0.85rem"},
                            ),
                            # Filtre par date début
                            dcc.DatePickerSingle(
                                id="session-filter-date-from",
                                placeholder="Date début",
                                display_format="DD/MM/YYYY",
                                clearable=True,
                                style={"fontSize": "0.85rem"},
                            ),
                            # Filtre par date fin
                            dcc.DatePickerSingle(
                                id="session-filter-date-to",
                                placeholder="Date fin",
                                display_format="DD/MM/YYYY",
                                clearable=True,
                                style={"fontSize": "0.85rem"},
                            ),
                            html.Button(
                                html.I(className="fa-solid fa-rotate"),
                                id="btn-refresh-sessions",
                                className="btn btn-ghost btn-icon btn-sm",
                                **{"data-tooltip": "Actualiser"},
                                n_clicks=0,
                            ),
                        ],
                    ),
                ]),
                html.Div(id="sessions-table-body", style={"padding": "0"}),
            ]),

            # ── Modal suppression ─────────────────────────────────────────
            confirm_modal(
                "delete-session",
                "Supprimer la séance",
                "Cette action supprimera la séance ainsi que toutes les présences enregistrées.",
                confirm_label="Supprimer",
                confirm_icon="fa-trash",
            ),

            # ── Stores ────────────────────────────────────────────────────
            dcc.Store(id="session-edit-id",        data=None),
            dcc.Store(id="session-delete-id",      data=None),
            dcc.Store(id="sessions-refresh-trigger", data=0),
        ],
    )


# ═══════════════════════════════════════════════════════════════════════════════
# LAYOUT AJOUT SÉANCE (réutilise layout avec form ouvert)
# ═══════════════════════════════════════════════════════════════════════════════
def layout_add():
    return layout()


# ═══════════════════════════════════════════════════════════════════════════════
# LAYOUT FEUILLES DE PRÉSENCE
# ═══════════════════════════════════════════════════════════════════════════════
def layout_attendance():
    return html.Div(
        className="fade-in",
        children=[
            html.Div(className="page-header", children=[
                html.Div([
                    html.H1("Feuilles de Présence", className="page-title"),
                    html.P("Consultation et export des présences par séance",
                           className="page-subtitle"),
                ], className="page-header-left"),
                html.Div([
                    dcc.Link(
                        [html.I(className="fa-solid fa-arrow-left"), " Retour"],
                        href="/sessions",
                        className="btn btn-outline btn-sm",
                    ),
                ], className="page-header-actions"),
            ]),

            # Sélecteur de séance
            html.Div(className="card mb-24", children=[
                html.Div(className="card-header", children=[
                    html.Div(
                        [html.I(className="fa-solid fa-filter"), " Sélectionner une séance"],
                        className="card-title",
                    ),
                ]),
                html.Div(className="card-body", children=[
                    html.Div(className="grid-2", children=[
                        html.Div([
                            html.Label(
                                [html.I(className="fa-solid fa-book-open",
                                        style={"marginRight": "5px"}), "Cours"],
                                className="form-label",
                            ),
                            dcc.Dropdown(
                                id="attendance-filter-course",
                                placeholder="Sélectionner un cours",
                                clearable=True,
                            ),
                        ], className="form-group"),
                        html.Div([
                            html.Label(
                                [html.I(className="fa-solid fa-calendar",
                                        style={"marginRight": "5px"}), "Séance"],
                                className="form-label",
                            ),
                            dcc.Dropdown(
                                id="attendance-filter-session",
                                placeholder="Sélectionner une séance",
                                clearable=True,
                            ),
                        ], className="form-group"),
                    ]),
                ]),
            ]),

            # Feuille de présence
            html.Div(id="attendance-sheet-container"),

            dcc.Store(id="attendance-refresh", data=0),
        ],
    )


# ═══════════════════════════════════════════════════════════════════════════════
# HELPERS UI
# ═══════════════════════════════════════════════════════════════════════════════
def _get_course_options(db):
    """Retourne les options dropdown des cours actifs."""
    courses = db.query(Course).filter(Course.is_active == True).order_by(Course.code).all()
    return [{"label": f"{c.code} — {c.label}", "value": c.id} for c in courses]


def _get_student_checklist(db, session_obj=None):
    """
    Retourne la checklist des étudiants pour l'appel.
    Si session_obj est fourni, pré-coche les absents déjà enregistrés.
    """
    students = db.query(Student).filter(Student.is_active == True)\
                 .order_by(Student.last_name, Student.first_name).all()

    # Récupérer les absents déjà enregistrés si édition
    pre_absent = set()
    if session_obj:
        absents = db.query(Attendance.student_id).filter(
            Attendance.session_id == session_obj.id,
            Attendance.is_absent == True,
        ).all()
        pre_absent = {a[0] for a in absents}

    items = []
    for s in students:
        is_absent = s.id in pre_absent
        items.append(
            html.Div(
                style={
                    "display": "flex", "alignItems": "center", "gap": "12px",
                    "padding": "8px 14px",
                    "background": "#fff8e1" if is_absent else "transparent",
                    "borderRadius": "8px", "marginBottom": "4px",
                    "border": "1px solid #ffe082" if is_absent else "1px solid transparent",
                    "transition": "all 0.15s",
                },
                children=[
                    dcc.Checklist(
                        id={"type": "student-absent-check", "index": s.id},
                        options=[{"label": "", "value": s.id}],
                        value=[s.id] if is_absent else [],
                        style={"margin": "0"},
                    ),
                    html.Div(
                        style={"width": "34px", "height": "34px",
                               "background": "#e8eaf6", "borderRadius": "50%",
                               "display": "flex", "alignItems": "center",
                               "justifyContent": "center", "fontSize": "0.8rem",
                               "fontWeight": "700", "color": "#1a237e", "flexShrink": "0"},
                        children=f"{s.first_name[0]}{s.last_name[0]}".upper(),
                    ),
                    html.Div([
                        html.Span(s.full_name,
                                  style={"fontWeight": "500", "fontSize": "0.88rem"}),
                        html.Div(s.email,
                                 style={"fontSize": "0.76rem", "color": "#9ca3af"}),
                    ]),
                    html.Div(
                        html.Span("ABSENT", style={
                            "fontSize": "0.7rem", "fontWeight": "700",
                            "color": "#f57f17", "background": "#fff8e1",
                            "padding": "2px 7px", "borderRadius": "10px",
                            "border": "1px solid #ffe082",
                        }) if is_absent else None,
                        style={"marginLeft": "auto"},
                    ),
                ],
            )
        )

    return items if items else html.P(
        "Aucun étudiant enregistré.",
        style={"color": "#9ca3af", "fontSize": "0.87rem", "padding": "12px 0"},
    )


def _empty_session_form():
    return html.Div(
        style={"display": "none"},
        children=[
            html.Button(id="btn-close-session-form", n_clicks=0),
            html.Button(id="btn-cancel-session-form", n_clicks=0),
            html.Button(id="btn-save-session", n_clicks=0),
            dcc.Dropdown(id="session-input-course", options=[], value=None),
            dcc.DatePickerSingle(id="session-input-date", date=None),
            dcc.Input(id="session-input-duration", type="number", value=None),
            dcc.Input(id="session-input-topic", value=""),
            dcc.Textarea(id="session-input-notes", value=""),
        ],
    )


def _session_form(session=None):
    """Formulaire inline de création / modification de séance."""
    is_edit = session is not None
    title   = "Modifier la séance" if is_edit else "Enregistrer une séance"
    icon    = "fa-pen-to-square" if is_edit else "fa-plus"

    try:
        with get_db() as db:
            course_opts = _get_course_options(db)
            student_checklist = _get_student_checklist(db, session)
    except Exception:
        course_opts = []
        student_checklist = []

    return html.Div(
        className="card",
        style={"borderLeft": "3px solid #1a237e"},
        children=[
            html.Div(className="card-header", children=[
                html.Div(
                    [html.I(className=f"fa-solid {icon}"), f" {title}"],
                    className="card-title",
                ),
                html.Button(
                    html.I(className="fa-solid fa-xmark"),
                    id="btn-close-session-form",
                    className="btn btn-ghost btn-icon btn-sm",
                    **{"data-tooltip": "Fermer"},
                    n_clicks=0,
                ),
            ]),
            html.Div(className="card-body", children=[

                # ── Informations de la séance ─────────────────────────
                html.Div(
                    style={"borderBottom": "1px solid #f1f5f9",
                           "paddingBottom": "20px", "marginBottom": "20px"},
                    children=[
                        html.Div(
                            [html.I(className="fa-solid fa-circle-info",
                                    style={"marginRight": "6px", "color": "#1a237e"}),
                             html.Strong("Informations de la séance")],
                            style={"fontSize": "0.88rem", "marginBottom": "16px"},
                        ),
                        html.Div(className="grid-2", children=[
                            html.Div([
                                html.Label(
                                    [html.I(className="fa-solid fa-book-open",
                                            style={"marginRight": "5px"}), "Cours"],
                                    className="form-label required",
                                ),
                                dcc.Dropdown(
                                    id="session-input-course",
                                    options=course_opts,
                                    value=session.course_id if is_edit else None,
                                    placeholder="Sélectionner un cours",
                                ),
                            ], className="form-group"),

                            html.Div([
                                html.Label(
                                    [html.I(className="fa-solid fa-calendar",
                                            style={"marginRight": "5px"}), "Date de la séance"],
                                    className="form-label required",
                                ),
                                dcc.DatePickerSingle(
                                    id="session-input-date",
                                    date=str(session.date) if is_edit else str(date.today()),
                                    display_format="DD/MM/YYYY",
                                    style={"width": "100%"},
                                ),
                            ], className="form-group"),

                            html.Div([
                                html.Label(
                                    [html.I(className="fa-solid fa-hourglass-half",
                                            style={"marginRight": "5px"}),
                                     "Durée (heures)"],
                                    className="form-label required",
                                ),
                                dcc.Input(
                                    id="session-input-duration",
                                    type="number",
                                    placeholder="ex: 2",
                                    value=session.duration if is_edit else 1.5,
                                    min=0.5, max=12, step=0.5,
                                    className="form-control",
                                ),
                            ], className="form-group"),

                            html.Div([
                                html.Label(
                                    [html.I(className="fa-solid fa-tag",
                                            style={"marginRight": "5px"}),
                                     "Thème abordé"],
                                    className="form-label",
                                ),
                                dcc.Input(
                                    id="session-input-topic",
                                    type="text",
                                    placeholder="ex: Introduction aux dérivées",
                                    value=session.topic if (is_edit and session.topic) else "",
                                    className="form-control",
                                ),
                            ], className="form-group"),
                        ]),

                        html.Div([
                            html.Label(
                                [html.I(className="fa-solid fa-align-left",
                                        style={"marginRight": "5px"}),
                                 "Notes pédagogiques (optionnel)"],
                                className="form-label",
                            ),
                            dcc.Textarea(
                                id="session-input-notes",
                                placeholder="Contenu du cours, exercices, devoirs...",
                                value=session.notes if (is_edit and session.notes) else "",
                                className="form-control",
                                style={"height": "80px", "resize": "vertical"},
                            ),
                        ], className="form-group"),
                    ],
                ),

                # ── Appel numérique ───────────────────────────────────
                html.Div([
                    html.Div(
                        style={"display": "flex", "alignItems": "center",
                               "justifyContent": "space-between", "marginBottom": "14px"},
                        children=[
                            html.Div(
                                [html.I(className="fa-solid fa-clipboard-check",
                                        style={"marginRight": "6px", "color": "#1a237e"}),
                                 html.Strong("Appel numérique")],
                                style={"fontSize": "0.88rem"},
                            ),
                            html.Div(
                                [html.I(className="fa-solid fa-circle-info",
                                        style={"marginRight": "5px", "color": "#9ca3af",
                                               "fontSize": "0.78rem"}),
                                 "Cocher les étudiants ABSENTS"],
                                style={"fontSize": "0.78rem", "color": "#9ca3af"},
                            ),
                        ],
                    ),
                    html.Div(
                        id="student-checklist-container",
                        children=student_checklist,
                        style={
                            "maxHeight": "320px",
                            "overflowY": "auto",
                            "border": "1px solid #e2e8f0",
                            "borderRadius": "10px",
                            "padding": "8px",
                        },
                    ),
                ]),

                # ── Boutons ───────────────────────────────────────────
                html.Div(
                    style={"display": "flex", "gap": "10px",
                           "justifyContent": "flex-end", "marginTop": "20px"},
                    children=[
                        html.Button(
                            [html.I(className="fa-solid fa-xmark"), " Annuler"],
                            id="btn-cancel-session-form",
                            className="btn btn-ghost",
                            n_clicks=0,
                        ),
                        html.Button(
                            [html.I(className="fa-solid fa-floppy-disk"),
                             " Enregistrer la séance"],
                            id="btn-save-session",
                            className="btn btn-primary",
                            n_clicks=0,
                        ),
                    ],
                ),
            ]),
        ],
    )


def _build_sessions_table(sessions):
    """Construit le tableau HTML des séances."""
    if not sessions:
        return empty_state(
            "fa-chalkboard-user",
            "Aucune séance enregistrée",
            "Cliquez sur « Nouvelle Séance » pour commencer.",
        )

    header = html.Div(
        style={
            "display": "grid",
            "gridTemplateColumns": "100px 1fr 160px 80px 100px 80px 80px",
            "gap": "12px", "padding": "10px 20px",
            "background": "#f8fafc",
            "borderBottom": "1px solid #e2e8f0",
        },
        children=[
            _th("Date"), _th("Cours / Thème"), _th("Enseignant"),
            _th("Durée", center=True), _th("Présents", center=True),
            _th("Absents", center=True), _th("Actions", right=True),
        ],
    )

    rows = []
    for s in sessions:
        course_code  = s.course.code    if s.course  else "—"
        course_label = s.course.label   if s.course  else "—"
        teacher      = s.course.teacher if s.course  else "—"

        total_att = len(s.attendances)
        absents   = sum(1 for a in s.attendances if a.is_absent)
        presents  = total_att - absents

        rows.append(html.Div(
            className="table-row-hover",
            style={
                "display": "grid",
                "gridTemplateColumns": "100px 1fr 160px 80px 100px 80px 80px",
                "gap": "12px", "padding": "14px 20px",
                "borderBottom": "1px solid #f1f5f9",
                "alignItems": "center",
            },
            children=[
                # Date
                html.Div([
                    html.Div(str(s.date).split("-")[2],
                             style={"fontSize": "1.2rem", "fontWeight": "700",
                                    "color": "#1a237e", "lineHeight": "1"}),
                    html.Div(
                        _month_short(str(s.date)),
                        style={"fontSize": "0.72rem", "color": "#9ca3af",
                               "textTransform": "uppercase"},
                    ),
                ], style={"textAlign": "center"}),

                # Cours + thème
                html.Div([
                    html.Div(
                        [html.Span(course_code,
                                   style={"fontFamily": "monospace", "fontWeight": "700",
                                          "fontSize": "0.8rem", "color": "#1a237e",
                                          "background": "#e8eaf6", "padding": "2px 7px",
                                          "borderRadius": "5px", "marginRight": "8px"}),
                         html.Span(course_label,
                                   style={"fontSize": "0.87rem", "fontWeight": "500"})],
                        style={"marginBottom": "3px"},
                    ),
                    html.Div(
                        [html.I(className="fa-solid fa-tag",
                                style={"marginRight": "4px", "fontSize": "0.7rem",
                                       "color": "#9ca3af"}),
                         s.topic or "—"],
                        style={"fontSize": "0.77rem", "color": "#9ca3af"},
                    ),
                ]),

                # Enseignant
                html.Div(
                    [html.I(className="fa-solid fa-chalkboard-user",
                            style={"marginRight": "5px", "color": "#9ca3af",
                                   "fontSize": "0.78rem"}),
                     teacher or "—"],
                    style={"fontSize": "0.83rem"},
                ),

                # Durée
                html.Div(
                    [html.Span(f"{s.duration}h",
                               style={"fontWeight": "600", "fontSize": "0.9rem"})],
                    style={"textAlign": "center"},
                ),

                # Présents
                html.Div(
                    [html.I(className="fa-solid fa-user-check",
                            style={"color": "#2e7d32", "marginRight": "5px",
                                   "fontSize": "0.8rem"}),
                     str(presents)],
                    style={"textAlign": "center", "fontSize": "0.87rem",
                           "color": "#2e7d32", "fontWeight": "500"},
                ),

                # Absents
                html.Div(
                    [html.I(className="fa-solid fa-user-xmark",
                            style={"color": "#e53935" if absents > 0 else "#9ca3af",
                                   "marginRight": "5px", "fontSize": "0.8rem"}),
                     str(absents)],
                    style={"textAlign": "center", "fontSize": "0.87rem",
                           "color": "#e53935" if absents > 0 else "#9ca3af",
                           "fontWeight": "500"},
                ),

                # Actions
                html.Div(
                    style={"display": "flex", "gap": "5px", "justifyContent": "flex-end"},
                    children=[
                        html.Button(
                            html.I(className="fa-solid fa-pen-to-square"),
                            id={"type": "session-btn-edit", "index": s.id},
                            className="btn btn-icon btn-sm btn-edit",
                            **{"data-tooltip": "Modifier"},
                            n_clicks=0,
                        ),
                        html.Button(
                            html.I(className="fa-solid fa-trash"),
                            id={"type": "session-btn-delete", "index": s.id},
                            className="btn btn-icon btn-sm btn-delete",
                            **{"data-tooltip": "Supprimer"},
                            n_clicks=0,
                        ),
                    ],
                ),
            ],
        ))

    return html.Div([header] + rows)


def _th(label, center=False, right=False):
    align = "center" if center else ("right" if right else "left")
    return html.Span(
        label,
        style={"fontSize": "0.75rem", "fontWeight": "700",
               "textTransform": "uppercase", "color": "#6b7280",
               "letterSpacing": "0.05em", "textAlign": align},
    )


def _month_short(date_str):
    months = ["Jan","Fév","Mar","Avr","Mai","Jun",
              "Jul","Aoû","Sep","Oct","Nov","Déc"]
    try:
        m = int(date_str.split("-")[1])
        return months[m - 1]
    except Exception:
        return ""


# ═══════════════════════════════════════════════════════════════════════════════
# CALLBACKS — Historique séances
# ═══════════════════════════════════════════════════════════════════════════════

@callback(
    Output("sessions-table-body",     "children"),
    Output("session-filter-course",   "options"),
    Input("sessions-refresh-trigger", "data"),
    Input("session-filter-course",    "value"),
    Input("session-filter-date-from", "date"),
    Input("session-filter-date-to",   "date"),
    Input("btn-refresh-sessions",     "n_clicks"),
)
def load_sessions_table(trigger, course_filter, date_from, date_to, n_refresh):
    try:
        with get_db() as db:
            q = db.query(Session).order_by(Session.date.desc())

            if course_filter:
                q = q.filter(Session.course_id == course_filter)
            if date_from:
                q = q.filter(Session.date >= date_from)
            if date_to:
                q = q.filter(Session.date <= date_to)

            sessions = q.all()
            course_opts = _get_course_options(db)
            # FIX : construire le HTML DANS la session
            table_html = _build_sessions_table(sessions)

        return table_html, course_opts

    except Exception as e:
        return html.Div(f"Erreur : {e}", className="alert alert-danger"), []


# ── Ouvrir / fermer formulaire ────────────────────────────────────────────────
@callback(
    Output("session-form-container", "children"),
    Output("session-edit-id",        "data"),
    Input("btn-open-add-session",    "n_clicks"),
    Input("btn-close-session-form",  "n_clicks"),
    Input("btn-cancel-session-form", "n_clicks"),
    Input({"type": "session-btn-edit", "index": ALL}, "n_clicks"),
    State({"type": "session-btn-edit", "index": ALL}, "id"),
    State("session-edit-id",         "data"),
    prevent_initial_call=True,
)
def toggle_session_form(n_add, n_close, n_cancel, n_edits, edit_ids, edit_id):
    triggered = ctx.triggered_id

    if triggered in ("btn-close-session-form", "btn-cancel-session-form"):
        return _empty_session_form(), None

    if triggered == "btn-open-add-session":
        return _session_form(None), None

    if isinstance(triggered, dict) and triggered.get("type") == "session-btn-edit":
        clicked = False
        for clicks, button_id in zip(n_edits or [], edit_ids or []):
            if button_id == triggered:
                clicked = bool(clicks and clicks > 0)
                break

        if not clicked:
            return no_update, no_update

        sid = triggered["index"]
        try:
            with get_db() as db:
                session = db.query(Session).filter(Session.id == sid).first()
            if session:
                return _session_form(session), sid
        except Exception:
            pass

    return no_update, no_update


# ── Sauvegarder la séance + présences ────────────────────────────────────────
@callback(
    Output("session-feedback",           "children"),
    Output("sessions-refresh-trigger",   "data"),
    Output("session-form-container",     "children", allow_duplicate=True),
    Input("btn-save-session",            "n_clicks"),
    State("session-input-course",        "value"),
    State("session-input-date",          "date"),
    State("session-input-duration",      "value"),
    State("session-input-topic",         "value"),
    State("session-input-notes",         "value"),
    State({"type": "student-absent-check", "index": ALL}, "value"),
    State({"type": "student-absent-check", "index": ALL}, "id"),
    State("session-edit-id",             "data"),
    State("sessions-refresh-trigger",    "data"),
    prevent_initial_call=True,
)
def save_session(n_clicks, course_id, session_date, duration,
                 topic, notes, absent_values, absent_ids,
                 edit_id, trigger):
    if not n_clicks:
        return no_update, no_update, no_update

    # ── Validation ────────────────────────────────────────────────────
    errors = []
    if not course_id:
        errors.append("Le cours est requis.")
    if not session_date:
        errors.append("La date de la séance est requise.")
    if not duration or float(duration) <= 0:
        errors.append("La durée doit être supérieure à 0.")

    if errors:
        return (
            html.Div(
                [html.I(className="fa-solid fa-circle-exclamation"),
                 html.Ul([html.Li(e) for e in errors],
                         style={"margin": "6px 0 0 16px"})],
                className="alert alert-warning",
            ),
            no_update, no_update,
        )

    # ── Convertir la date (Dash envoie chaîne, SQLAlchemy attend date Python)
    try:
        if isinstance(session_date, str):
            session_date = datetime.strptime(session_date, "%Y-%m-%d").date()
        elif isinstance(session_date, dict):
            # Cas rare où Dash envoie un dictionnaire
            session_date = datetime.strptime(session_date.get('date', str(date.today())), "%Y-%m-%d").date()
    except Exception as e:
        return (
            html.Div([html.I(className="fa-solid fa-circle-xmark"),
                     f" Erreur conversion date : {e}"],
                    className="alert alert-danger"),
            no_update, no_update,
        )

    # ── Calcul des absents ────────────────────────────────────────────
    absent_student_ids = set()
    for vals, id_obj in zip(absent_values, absent_ids):
        if vals:  # checklist cochée
            absent_student_ids.add(id_obj["index"])

    try:
        with get_db() as db:
            if edit_id:
                # Modification
                session_obj = db.query(Session).filter(Session.id == edit_id).first()
                if not session_obj:
                    raise ValueError("Séance introuvable.")
                session_obj.course_id = course_id
                session_obj.date      = session_date
                session_obj.duration  = float(duration)
                session_obj.topic     = topic.strip() if topic else None
                session_obj.notes     = notes.strip() if notes else None

                # Mettre à jour les présences
                db.query(Attendance).filter(
                    Attendance.session_id == edit_id
                ).delete()
                db.flush()

                msg = f"Séance du {session_date} mise à jour."
                session_id_final = edit_id

            else:
                # Création
                session_obj = Session(
                    course_id = course_id,
                    date      = session_date,
                    duration  = float(duration),
                    topic     = topic.strip() if topic else None,
                    notes     = notes.strip() if notes else None,
                )
                db.add(session_obj)
                db.flush()
                session_id_final = session_obj.id
                msg = f"Séance du {session_date} enregistrée."

            # Enregistrer les présences pour TOUS les étudiants actifs
            students = db.query(Student).filter(Student.is_active == True).all()
            for student in students:
                att = Attendance(
                    session_id = session_id_final,
                    student_id = student.id,
                    is_absent  = student.id in absent_student_ids,
                    is_excused = False,
                )
                db.add(att)

        nb_absents = len(absent_student_ids)
        feedback = html.Div(
            [html.I(className="fa-solid fa-circle-check"),
             f" {msg} ({nb_absents} absent(s) enregistré(s))"],
            className="alert alert-success",
        )
        return feedback, (trigger or 0) + 1, _empty_session_form()

    except Exception as e:
        return (
            html.Div(
                [html.I(className="fa-solid fa-circle-xmark"), f" Erreur : {str(e)}"],
                className="alert alert-danger",
            ),
            no_update, no_update,
        )


# ── Modal suppression ─────────────────────────────────────────────────────────
@callback(
    Output("delete-session-overlay", "style"),
    Output("session-delete-id",      "data"),
    Input({"type": "session-btn-delete", "index": ALL}, "n_clicks"),
    Input("delete-session-cancel",   "n_clicks"),
    Input("delete-session-close",    "n_clicks"),
    State({"type": "session-btn-delete", "index": ALL}, "id"),
    prevent_initial_call=True,
)
def toggle_session_delete_modal(n_deletes, n_cancel, n_close, delete_ids):
    triggered = ctx.triggered_id
    if triggered in ("delete-session-cancel", "delete-session-close"):
        return {"display": "none"}, None
    if isinstance(triggered, dict) and triggered.get("type") == "session-btn-delete":
        for clicks, button_id in zip(n_deletes or [], delete_ids or []):
            if button_id == triggered:
                if clicks and clicks > 0:
                    return {"display": "flex"}, triggered["index"]
                break
        return {"display": "none"}, None
    return {"display": "none"}, None


@callback(
    Output("session-feedback",           "children", allow_duplicate=True),
    Output("sessions-refresh-trigger",   "data",     allow_duplicate=True),
    Output("delete-session-overlay",     "style",    allow_duplicate=True),
    Input("delete-session-confirm",      "n_clicks"),
    State("session-delete-id",           "data"),
    State("sessions-refresh-trigger",    "data"),
    prevent_initial_call=True,
)
def confirm_delete_session(n_clicks, session_id, trigger):
    if not session_id:
        return no_update, no_update, {"display": "none"}
    try:
        with get_db() as db:
            session_obj = db.query(Session).filter(Session.id == session_id).first()
            if session_obj:
                db.query(Attendance).filter(
                    Attendance.session_id == session_id
                ).delete()
                db.delete(session_obj)
        return (
            html.Div([html.I(className="fa-solid fa-circle-check"),
                      " Séance supprimée."],
                     className="alert alert-success"),
            (trigger or 0) + 1,
            {"display": "none"},
        )
    except Exception as e:
        return (
            html.Div([html.I(className="fa-solid fa-circle-xmark"), f" Erreur : {str(e)}"],
                     className="alert alert-danger"),
            no_update, {"display": "none"},
        )


# ═══════════════════════════════════════════════════════════════════════════════
# CALLBACKS — Feuilles de présence
# ═══════════════════════════════════════════════════════════════════════════════

@callback(
    Output("attendance-filter-course",  "options"),
    Output("attendance-filter-session", "options"),
    Input("attendance-filter-course",   "value"),
    Input("attendance-refresh",         "data"),
)
def update_attendance_dropdowns(course_id, refresh):
    try:
        with get_db() as db:
            course_opts = _get_course_options(db)
            session_opts = []
            if course_id:
                sessions = db.query(Session).filter(
                    Session.course_id == course_id
                ).order_by(Session.date.desc()).all()
                session_opts = [
                    {"label": f"{s.date} — {s.topic or 'Séance'} ({s.duration}h)",
                     "value": s.id}
                    for s in sessions
                ]
        return course_opts, session_opts
    except Exception:
        return [], []


@callback(
    Output("attendance-sheet-container", "children"),
    Input("attendance-filter-session",   "value"),
)
def display_attendance_sheet(session_id):
    if not session_id:
        return html.Div(
            style={"textAlign": "center", "padding": "40px", "color": "#9ca3af"},
            children=[
                html.I(className="fa-solid fa-clipboard-list",
                       style={"fontSize": "2.5rem", "color": "#e2e8f0",
                              "marginBottom": "12px", "display": "block"}),
                "Sélectionnez un cours et une séance pour afficher la feuille de présence.",
            ],
        )

    try:
        with get_db() as db:
            session_obj = db.query(Session).options(
                joinedload(Session.course)
            ).filter(Session.id == session_id).first()
            if not session_obj:
                return html.Div("Séance introuvable.", className="alert alert-danger")

            attendances = db.query(Attendance).options(
                joinedload(Attendance.student)
            ).filter(
                Attendance.session_id == session_id
            ).order_by(Attendance.student_id).all()

            total    = len(attendances)
            absents  = sum(1 for a in attendances if a.is_absent)
            presents = total - absents
            rate     = round((presents / total * 100), 1) if total > 0 else 0

            # Matérialiser tout dans la session
            course_code  = session_obj.course.code if session_obj.course else "—"
            session_date = str(session_obj.date)
            duration     = session_obj.duration
            topic        = session_obj.topic or "—"

            att_data = []
            for att in attendances:
                s = att.student
                att_data.append({
                    "is_absent":   att.is_absent,
                    "is_excused":  att.is_excused,
                    "initials":    f"{s.first_name[0]}{s.last_name[0]}".upper() if s else "?",
                    "last_name":   s.last_name.upper() if s else "—",
                    "first_name":  s.first_name if s else "—",
                })

        # ── En-tête feuille ───────────────────────────────────────────
        header_info = html.Div(className="card mb-24", children=[
            html.Div(className="card-header", children=[
                html.Div(
                    [html.I(className="fa-solid fa-clipboard-check"),
                     " Feuille de Présence"],
                    className="card-title",
                ),
                html.Div(
                    [html.Span(f"{rate}% de présence",
                               className="badge badge-success" if rate >= 75
                               else "badge badge-warning" if rate >= 50
                               else "badge badge-danger")],
                ),
            ]),
            html.Div(className="card-body", children=[
                html.Div(className="grid-4", children=[
                    _info_block("fa-book-open",        "Cours",    course_code),
                    _info_block("fa-calendar",         "Date",     session_date),
                    _info_block("fa-hourglass-half",   "Durée",    f"{duration}h"),
                    _info_block("fa-tag",              "Thème",    topic),
                ]),
                html.Div(style={"marginTop": "16px"},
                         children=progress_bar(rate, label=f"{presents} présents / {total} étudiants")),
            ]),
        ])

        # ── Liste présences ───────────────────────────────────────────
        if not att_data:
            rows = [empty_state("fa-users", "Aucune donnée de présence")]
        else:
            rows = []
            for i, att in enumerate(att_data, 1):
                status_icon  = "fa-circle-check" if not att["is_absent"] else "fa-circle-xmark"
                status_color = "#2e7d32" if not att["is_absent"] else "#e53935"
                status_text  = "Présent" if not att["is_absent"] else \
                               ("Absent justifié" if att["is_excused"] else "Absent")

                rows.append(html.Div(
                    style={
                        "display": "grid",
                        "gridTemplateColumns": "40px 40px 1fr 1fr 120px",
                        "gap": "12px", "padding": "11px 20px",
                        "borderBottom": "1px solid #f1f5f9",
                        "alignItems": "center",
                        "background": "#fff8f8" if att["is_absent"] else "transparent",
                    },
                    children=[
                        html.Span(str(i),
                                  style={"fontSize": "0.78rem", "color": "#9ca3af",
                                         "textAlign": "center"}),
                        html.Div(att["initials"],
                            style={"width": "32px", "height": "32px",
                                   "background": "#e8eaf6", "borderRadius": "50%",
                                   "display": "flex", "alignItems": "center",
                                   "justifyContent": "center", "fontSize": "0.78rem",
                                   "fontWeight": "700", "color": "#1a237e"},
                        ),
                        html.Div(att["last_name"],
                                 style={"fontWeight": "600", "fontSize": "0.87rem"}),
                        html.Div(att["first_name"],
                                 style={"fontSize": "0.87rem"}),
                        html.Div(
                            [html.I(className=f"fa-solid {status_icon}",
                                    style={"marginRight": "5px", "color": status_color}),
                             status_text],
                            style={"fontSize": "0.82rem", "color": status_color,
                                   "fontWeight": "500"},
                        ),
                    ],
                ))

        att_header = html.Div(
            style={
                "display": "grid",
                "gridTemplateColumns": "40px 40px 1fr 1fr 120px",
                "gap": "12px", "padding": "10px 20px",
                "background": "#f8fafc", "borderBottom": "1px solid #e2e8f0",
                "borderRadius": "10px 10px 0 0",
            },
            children=[
                _th("#"), _th(""), _th("Nom"), _th("Prénom"), _th("Statut"),
            ],
        )

        att_table = html.Div(
            className="table-container",
            children=[html.Div(att_header), html.Div(rows)],
        )

        return html.Div([header_info, att_table])

    except Exception as e:
        return html.Div(f"Erreur : {e}", className="alert alert-danger")


def _info_block(icon, label, value):
    return html.Div([
        html.Div(
            [html.I(className=f"fa-solid {icon}",
                    style={"marginRight": "5px", "color": "#9ca3af",
                           "fontSize": "0.78rem"}),
             label],
            style={"fontSize": "0.75rem", "textTransform": "uppercase",
                   "color": "#9ca3af", "letterSpacing": "0.05em",
                   "marginBottom": "4px"},
        ),
        html.Div(value, style={"fontWeight": "600", "fontSize": "0.9rem"}),
    ])
