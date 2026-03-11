"""
pages/courses.py — Module 1 : Gestion des Cours
- Liste des cours avec filtres et actions CRUD
- Formulaire d'ajout / modification inline
- Barres de progression horaire en temps réel
- Vue dédiée progression
"""

from dash import html, dcc, callback, Output, Input, State, no_update, ctx, ALL
import plotly.graph_objects as go

from database.db import get_db
from database.models import Course, Session
from components.tables import progress_bar, empty_state, table_filter_bar
from components.modals import confirm_modal
from sqlalchemy import func


# ═══════════════════════════════════════════════════════════════════════════════
# LAYOUT PRINCIPAL — Liste des cours
# ═══════════════════════════════════════════════════════════════════════════════
def layout():
    return html.Div(
        className="fade-in",
        children=[

            # ── Page Header ──────────────────────────────────────────────
            html.Div(
                className="page-header",
                children=[
                    html.Div([
                        html.H1("Gestion des Cours", className="page-title"),
                        html.P("Curriculum, volumes horaires et suivi de progression",
                               className="page-subtitle"),
                    ], className="page-header-left"),
                    html.Div(
                        className="page-header-actions",
                        children=[
                            dcc.Link(
                                [html.I(className="fa-solid fa-chart-line"), " Progression"],
                                href="/courses/progress",
                                className="btn btn-outline btn-sm",
                            ),
                            html.Button(
                                [html.I(className="fa-solid fa-plus"), " Nouveau Cours"],
                                id="btn-open-add-course",
                                className="btn btn-primary btn-sm",
                                n_clicks=0,
                            ),
                        ],
                    ),
                ],
            ),

            # ── Feedback ─────────────────────────────────────────────────
            html.Div(id="course-feedback"),

            # ── Formulaire ajout / édition (inline collapsible) ──────────
            html.Div(id="course-form-container", children=_empty_course_form(),
                     style={"marginBottom": "20px"}),

            # ── Barre de filtres + tableau ────────────────────────────────
            html.Div(
                className="table-container",
                children=[
                    html.Div(
                        className="table-header",
                        children=[
                            html.Div(
                                [html.I(className="fa-solid fa-book-open"), " Liste des Cours"],
                                className="table-title",
                            ),
                            html.Div(
                                style={"display": "flex", "gap": "10px", "alignItems": "center"},
                                children=[
                                    html.Div(
                                        [
                                            html.I(className="fa-solid fa-magnifying-glass",
                                                   style={"position": "absolute", "left": "10px",
                                                          "top": "50%", "transform": "translateY(-50%)",
                                                          "color": "#9ca3af", "fontSize": "0.8rem",
                                                          "pointerEvents": "none"}),
                                            dcc.Input(
                                                id="course-search",
                                                type="text",
                                                placeholder="Rechercher un cours...",
                                                debounce=True,
                                                className="form-control",
                                                style={"paddingLeft": "32px", "width": "220px",
                                                       "fontSize": "0.85rem"},
                                            ),
                                        ],
                                        style={"position": "relative"},
                                    ),
                                    dcc.Dropdown(
                                        id="course-filter-teacher",
                                        placeholder="Filtrer par enseignant",
                                        clearable=True,
                                        style={"minWidth": "180px", "fontSize": "0.85rem"},
                                    ),
                                    html.Button(
                                        html.I(className="fa-solid fa-rotate"),
                                        id="btn-refresh-courses",
                                        className="btn btn-ghost btn-icon btn-sm",
                                        **{"data-tooltip": "Actualiser"},
                                        n_clicks=0,
                                    ),
                                ],
                            ),
                        ],
                    ),
                    # Corps du tableau
                    html.Div(id="courses-table-body", className="card-body",
                             style={"padding": "0"}),
                ],
            ),

            # ── Modal de confirmation suppression ──────────────────────
            confirm_modal(
                "delete-course",
                "Supprimer le cours",
                "Cette action est irréversible. Toutes les séances et notes associées seront supprimées.",
                confirm_label="Supprimer",
                confirm_icon="fa-trash",
            ),

            # ── Stores ────────────────────────────────────────────────
            dcc.Store(id="course-edit-id", data=None),
            dcc.Store(id="course-delete-id", data=None),
            dcc.Store(id="courses-refresh-trigger", data=0),
        ],
    )


# ═══════════════════════════════════════════════════════════════════════════════
# LAYOUT AJOUT DIRECT
# ═══════════════════════════════════════════════════════════════════════════════
def layout_add():
    return layout()


# ═══════════════════════════════════════════════════════════════════════════════
# LAYOUT PROGRESSION
# ═══════════════════════════════════════════════════════════════════════════════
def layout_progress():
    return html.Div(
        className="fade-in",
        children=[
            html.Div(
                className="page-header",
                children=[
                    html.Div([
                        html.H1("Progression des Cours", className="page-title"),
                        html.P("Suivi du volume horaire réalisé vs prévu", className="page-subtitle"),
                    ], className="page-header-left"),
                    html.Div([
                        dcc.Link(
                            [html.I(className="fa-solid fa-arrow-left"), " Retour"],
                            href="/courses", className="btn btn-outline btn-sm",
                        ),
                    ], className="page-header-actions"),
                ],
            ),

            # KPIs progression
            html.Div(id="progress-kpis", className="grid-4 mb-24"),

            # Graphique progression globale
            html.Div(
                className="chart-container mb-24",
                children=[
                    html.Div(
                        [html.I(className="fa-solid fa-chart-bar"), " Heures Réalisées vs Prévues"],
                        className="chart-title",
                    ),
                    dcc.Graph(id="chart-progress-bars",
                              config={"displayModeBar": False},
                              style={"height": "340px"}),
                ],
            ),

            # Cartes de progression par cours
            html.Div(id="progress-cards-grid", className="grid-3"),

            dcc.Interval(id="progress-interval", interval=60_000, n_intervals=0),
        ],
    )


# ═══════════════════════════════════════════════════════════════════════════════
# HELPERS UI
# ═══════════════════════════════════════════════════════════════════════════════
def _empty_course_form():
    return html.Div(
        style={"display": "none"},
        children=[
            html.Button(id="btn-close-course-form", n_clicks=0),
            html.Button(id="btn-cancel-course-form", n_clicks=0),
            html.Button(id="btn-save-course", n_clicks=0),
            dcc.Input(id="course-input-code", value=""),
            dcc.Input(id="course-input-label", value=""),
            dcc.Input(id="course-input-hours", type="number", value=None),
            dcc.Input(id="course-input-teacher", value=""),
            dcc.Textarea(id="course-input-description", value=""),
        ],
    )


def _course_form(course=None):
    """
    Formulaire inline d'ajout ou de modification d'un cours.
    course : objet Course existant (mode édition) ou None (mode création).
    """
    is_edit = course is not None
    title = "Modifier le cours" if is_edit else "Nouveau cours"
    icon  = "fa-pen-to-square" if is_edit else "fa-plus"

    return html.Div(
        className="card",
        style={"borderLeft": "3px solid #1a237e"},
        children=[
            html.Div(
                className="card-header",
                children=[
                    html.Div(
                        [html.I(className=f"fa-solid {icon}"), f" {title}"],
                        className="card-title",
                    ),
                    html.Button(
                        html.I(className="fa-solid fa-xmark"),
                        id="btn-close-course-form",
                        className="btn btn-ghost btn-icon btn-sm",
                        **{"data-tooltip": "Fermer"},
                        n_clicks=0,
                    ),
                ],
            ),
            html.Div(
                className="card-body",
                children=[
                    html.Div(
                        className="grid-2",
                        children=[
                            html.Div([
                                html.Label(
                                    [html.I(className="fa-solid fa-hashtag",
                                            style={"marginRight": "5px"}), "Code du cours"],
                                    className="form-label required",
                                ),
                                dcc.Input(
                                    id="course-input-code",
                                    type="text",
                                    placeholder="ex: MATH101",
                                    value=course.code if is_edit else "",
                                    className="form-control",
                                    maxLength=20,
                                ),
                                html.Div("Format : lettres + chiffres, sans espaces",
                                         className="form-hint"),
                            ], className="form-group"),

                            html.Div([
                                html.Label(
                                    [html.I(className="fa-solid fa-tag",
                                            style={"marginRight": "5px"}), "Intitulé du cours"],
                                    className="form-label required",
                                ),
                                dcc.Input(
                                    id="course-input-label",
                                    type="text",
                                    placeholder="ex: Mathématiques Avancées",
                                    value=course.label if is_edit else "",
                                    className="form-control",
                                ),
                            ], className="form-group"),

                            html.Div([
                                html.Label(
                                    [html.I(className="fa-solid fa-clock",
                                            style={"marginRight": "5px"}), "Volume horaire total (h)"],
                                    className="form-label required",
                                ),
                                dcc.Input(
                                    id="course-input-hours",
                                    type="number",
                                    placeholder="ex: 30",
                                    value=course.total_hours if is_edit else "",
                                    min=1, max=999,
                                    className="form-control",
                                ),
                            ], className="form-group"),

                            html.Div([
                                html.Label(
                                    [html.I(className="fa-solid fa-chalkboard-user",
                                            style={"marginRight": "5px"}), "Enseignant responsable"],
                                    className="form-label",
                                ),
                                dcc.Input(
                                    id="course-input-teacher",
                                    type="text",
                                    placeholder="ex: Dr. Dupont",
                                    value=course.teacher if (is_edit and course.teacher) else "",
                                    className="form-control",
                                ),
                            ], className="form-group"),
                        ],
                    ),

                    html.Div([
                        html.Label(
                            [html.I(className="fa-solid fa-align-left",
                                    style={"marginRight": "5px"}), "Description (optionnel)"],
                            className="form-label",
                        ),
                        dcc.Textarea(
                            id="course-input-description",
                            placeholder="Objectifs pédagogiques, contenu du cours...",
                            value=course.description if (is_edit and course.description) else "",
                            className="form-control",
                            style={"height": "80px", "resize": "vertical"},
                        ),
                    ], className="form-group"),

                    # Boutons
                    html.Div(
                        style={"display": "flex", "gap": "10px", "justifyContent": "flex-end",
                               "marginTop": "8px"},
                        children=[
                            html.Button(
                                [html.I(className="fa-solid fa-xmark"), " Annuler"],
                                id="btn-cancel-course-form",
                                className="btn btn-ghost",
                                n_clicks=0,
                            ),
                            html.Button(
                                [html.I(className="fa-solid fa-floppy-disk"),
                                 " Enregistrer le cours"],
                                id="btn-save-course",
                                className="btn btn-primary",
                                n_clicks=0,
                            ),
                        ],
                    ),
                ],
            ),
        ],
    )


def _build_courses_table(courses):
    """Construit le tableau HTML des cours."""
    if not courses:
        return empty_state(
            "fa-book-open",
            "Aucun cours enregistré",
            "Cliquez sur « Nouveau Cours » pour commencer.",
        )

    rows = []
    for course in courses:
        pct = course.progress_percent
        done = course.completed_hours

        rows.append(
            html.Div(
                style={
                    "display": "grid",
                    "gridTemplateColumns": "80px 1fr 120px 140px 160px 100px",
                    "alignItems": "center",
                    "gap": "12px",
                    "padding": "14px 20px",
                    "borderBottom": "1px solid #f1f5f9",
                    "transition": "background 0.15s",
                },
                className="table-row-hover",
                children=[
                    # Code
                    html.Div(
                        course.code,
                        style={"fontWeight": "700", "fontSize": "0.82rem",
                               "color": "#1a237e", "fontFamily": "monospace",
                               "background": "#e8eaf6", "padding": "3px 8px",
                               "borderRadius": "6px", "textAlign": "center"},
                    ),
                    # Libellé + enseignant
                    html.Div([
                        html.Div(course.label,
                                 style={"fontWeight": "500", "fontSize": "0.9rem"}),
                        html.Div(
                            [html.I(className="fa-solid fa-chalkboard-user",
                                    style={"marginRight": "4px", "fontSize": "0.7rem"}),
                             course.teacher or "—"],
                            style={"fontSize": "0.77rem", "color": "#9ca3af", "marginTop": "2px"},
                        ),
                    ]),
                    # Volume horaire
                    html.Div(
                        [
                            html.Span(f"{done}h", style={"fontWeight": "600"}),
                            html.Span(f" / {course.total_hours}h",
                                      style={"color": "#9ca3af", "fontSize": "0.82rem"}),
                        ],
                        style={"fontSize": "0.87rem", "textAlign": "center"},
                    ),
                    # Nb séances
                    html.Div(
                        [
                            html.I(className="fa-solid fa-calendar-check",
                                   style={"marginRight": "5px", "color": "#1a237e",
                                          "fontSize": "0.8rem"}),
                            f"{len(course.sessions)} séance{'s' if len(course.sessions) != 1 else ''}",
                        ],
                        style={"fontSize": "0.85rem", "textAlign": "center"},
                    ),
                    # Barre de progression
                    progress_bar(pct, show_label=False, size="md"),
                    # Actions
                    html.Div(
                        style={"display": "flex", "gap": "5px", "justifyContent": "flex-end"},
                        children=[
                            html.Button(
                                html.I(className="fa-solid fa-pen-to-square"),
                                id={"type": "course-btn-edit", "index": course.id},
                                className="btn btn-icon btn-sm btn-edit",
                                **{"data-tooltip": "Modifier"},
                                n_clicks=0,
                            ),
                            html.Button(
                                html.I(className="fa-solid fa-trash"),
                                id={"type": "course-btn-delete", "index": course.id},
                                className="btn btn-icon btn-sm btn-delete",
                                **{"data-tooltip": "Supprimer"},
                                n_clicks=0,
                            ),
                        ],
                    ),
                ],
            )
        )

    # En-tête du tableau
    header = html.Div(
        style={
            "display": "grid",
            "gridTemplateColumns": "80px 1fr 120px 140px 160px 100px",
            "gap": "12px",
            "padding": "10px 20px",
            "background": "#f8fafc",
            "borderBottom": "1px solid #e2e8f0",
        },
        children=[
            html.Span("Code",       style={"fontSize": "0.75rem", "fontWeight": "700",
                                           "textTransform": "uppercase", "color": "#6b7280",
                                           "letterSpacing": "0.05em"}),
            html.Span("Cours",      style={"fontSize": "0.75rem", "fontWeight": "700",
                                           "textTransform": "uppercase", "color": "#6b7280",
                                           "letterSpacing": "0.05em"}),
            html.Span("Heures",     style={"fontSize": "0.75rem", "fontWeight": "700",
                                           "textTransform": "uppercase", "color": "#6b7280",
                                           "letterSpacing": "0.05em", "textAlign": "center"}),
            html.Span("Séances",    style={"fontSize": "0.75rem", "fontWeight": "700",
                                           "textTransform": "uppercase", "color": "#6b7280",
                                           "letterSpacing": "0.05em", "textAlign": "center"}),
            html.Span("Progression",style={"fontSize": "0.75rem", "fontWeight": "700",
                                           "textTransform": "uppercase", "color": "#6b7280",
                                           "letterSpacing": "0.05em"}),
            html.Span("Actions",    style={"fontSize": "0.75rem", "fontWeight": "700",
                                           "textTransform": "uppercase", "color": "#6b7280",
                                           "letterSpacing": "0.05em", "textAlign": "right"}),
        ],
    )

    return html.Div([header] + rows)


# ═══════════════════════════════════════════════════════════════════════════════
# CALLBACKS — Module Cours
# ═══════════════════════════════════════════════════════════════════════════════

# ── Afficher le tableau des cours ─────────────────────────────────────────────
@callback(
    Output("courses-table-body",      "children"),
    Output("course-filter-teacher",   "options"),
    Input("courses-refresh-trigger",  "data"),
    Input("course-search",            "value"),
    Input("course-filter-teacher",    "value"),
    Input("btn-refresh-courses",      "n_clicks"),
)
def load_courses_table(trigger, search, teacher_filter, n_refresh):
    try:
        with get_db() as db:
            q = db.query(Course).filter(Course.is_active == True)

            if search:
                q = q.filter(
                    (Course.code.ilike(f"%{search}%")) |
                    (Course.label.ilike(f"%{search}%")) |
                    (Course.teacher.ilike(f"%{search}%"))
                )
            if teacher_filter:
                q = q.filter(Course.teacher == teacher_filter)

            courses = q.order_by(Course.code).all()

            # Options filtre enseignants
            teachers = db.query(Course.teacher).filter(
                Course.teacher != None, Course.is_active == True
            ).distinct().all()
            teacher_opts = [{"label": t[0], "value": t[0]} for t in teachers if t[0]]

            # FIX : construire le HTML DANS la session (accès aux relations lazy)
            table_html = _build_courses_table(courses)

        return table_html, teacher_opts

    except Exception as e:
        return html.Div(f"Erreur : {e}", className="alert alert-danger"), []


# ── Ouvrir / fermer le formulaire ─────────────────────────────────────────────
@callback(
    Output("course-form-container", "children"),
    Output("course-edit-id",        "data"),
    Input("btn-open-add-course",    "n_clicks"),
    Input("btn-close-course-form",  "n_clicks"),
    Input("btn-cancel-course-form", "n_clicks"),
    Input({"type": "course-btn-edit", "index": ALL}, "n_clicks"),
    State({"type": "course-btn-edit", "index": ALL}, "id"),
    State("course-edit-id",         "data"),
    prevent_initial_call=True,
)
def toggle_course_form(n_add, n_close, n_cancel, n_edits, edit_ids, edit_id):
    triggered = ctx.triggered_id

    # Fermer le formulaire
    if triggered in ("btn-close-course-form", "btn-cancel-course-form"):
        return _empty_course_form(), None

    # Ouvrir en mode ajout
    if triggered == "btn-open-add-course":
        return _course_form(None), None

    # Ouvrir en mode édition
    if isinstance(triggered, dict) and triggered.get("type") == "course-btn-edit":
        clicked = False
        for clicks, button_id in zip(n_edits or [], edit_ids or []):
            if button_id == triggered:
                clicked = bool(clicks and clicks > 0)
                break

        if not clicked:
            return no_update, no_update

        cid = triggered["index"]
        try:
            with get_db() as db:
                course = db.query(Course).filter(Course.id == cid).first()
            if course:
                return _course_form(course), cid
        except Exception:
            pass

    return no_update, no_update


# ── Sauvegarder un cours (ajout ou modification) ──────────────────────────────
@callback(
    Output("course-feedback",           "children"),
    Output("courses-refresh-trigger",   "data"),
    Output("course-form-container",     "children", allow_duplicate=True),
    Input("btn-save-course",            "n_clicks"),
    State("course-input-code",          "value"),
    State("course-input-label",         "value"),
    State("course-input-hours",         "value"),
    State("course-input-teacher",       "value"),
    State("course-input-description",   "value"),
    State("course-edit-id",             "data"),
    State("courses-refresh-trigger",    "data"),
    prevent_initial_call=True,
)
def save_course(n_clicks, code, label, hours, teacher, description, edit_id, trigger):
    if not n_clicks:
        return no_update, no_update, no_update

    # Validation
    errors = []
    if not code or not code.strip():
        errors.append("Le code du cours est requis.")
    if not label or not label.strip():
        errors.append("L'intitulé du cours est requis.")
    if not hours or float(hours) <= 0:
        errors.append("Le volume horaire doit être supérieur à 0.")

    if errors:
        return (
            html.Div(
                [html.I(className="fa-solid fa-circle-exclamation"),
                 html.Ul([html.Li(e) for e in errors], style={"margin": "6px 0 0 16px"})],
                className="alert alert-warning",
            ),
            no_update, no_update,
        )

    try:
        with get_db() as db:
            if edit_id:
                # Modification
                course = db.query(Course).filter(Course.id == edit_id).first()
                if not course:
                    raise ValueError("Cours introuvable.")
                # Vérifier doublon code (hors lui-même)
                existing = db.query(Course).filter(
                    Course.code == code.strip().upper(),
                    Course.id != edit_id
                ).first()
                if existing:
                    raise ValueError(f"Le code « {code} » est déjà utilisé.")

                course.code        = code.strip().upper()
                course.label       = label.strip()
                course.total_hours = float(hours)
                course.teacher     = teacher.strip() if teacher else None
                course.description = description.strip() if description else None
                msg = f"Cours « {course.code} » mis à jour avec succès."
            else:
                # Ajout
                existing = db.query(Course).filter(
                    Course.code == code.strip().upper()
                ).first()
                if existing:
                    raise ValueError(f"Le code « {code} » est déjà utilisé.")

                course = Course(
                    code        = code.strip().upper(),
                    label       = label.strip(),
                    total_hours = float(hours),
                    teacher     = teacher.strip() if teacher else None,
                    description = description.strip() if description else None,
                )
                db.add(course)
                msg = f"Cours « {course.code} » créé avec succès."

        feedback = html.Div(
            [html.I(className="fa-solid fa-circle-check"), f" {msg}"],
            className="alert alert-success",
        )
        return feedback, (trigger or 0) + 1, _empty_course_form()

    except ValueError as ve:
        return (
            html.Div([html.I(className="fa-solid fa-circle-xmark"), f" {str(ve)}"],
                     className="alert alert-danger"),
            no_update, no_update,
        )
    except Exception as e:
        return (
            html.Div([html.I(className="fa-solid fa-circle-xmark"), f" Erreur : {str(e)}"],
                     className="alert alert-danger"),
            no_update, no_update,
        )


# ── Afficher / cacher modal suppression ───────────────────────────────────────
@callback(
    Output("delete-course-overlay", "style"),
    Output("course-delete-id",      "data"),
    Input({"type": "course-btn-delete", "index": ALL}, "n_clicks"),
    Input("delete-course-cancel",   "n_clicks"),
    Input("delete-course-close",    "n_clicks"),
    State({"type": "course-btn-delete", "index": ALL}, "id"),
    prevent_initial_call=True,
)
def toggle_delete_modal(n_deletes, n_cancel, n_close, delete_ids):
    triggered = ctx.triggered_id
    if triggered in ("delete-course-cancel", "delete-course-close"):
        return {"display": "none"}, None
    if isinstance(triggered, dict) and triggered.get("type") == "course-btn-delete":
        for clicks, button_id in zip(n_deletes or [], delete_ids or []):
            if button_id == triggered:
                if clicks and clicks > 0:
                    return {"display": "flex"}, triggered["index"]
                break
        return {"display": "none"}, None
    return {"display": "none"}, None


# ── Confirmer la suppression ──────────────────────────────────────────────────
@callback(
    Output("course-feedback",           "children", allow_duplicate=True),
    Output("courses-refresh-trigger",   "data",     allow_duplicate=True),
    Output("delete-course-overlay",     "style",    allow_duplicate=True),
    Input("delete-course-confirm",      "n_clicks"),
    State("course-delete-id",           "data"),
    State("courses-refresh-trigger",    "data"),
    prevent_initial_call=True,
)
def confirm_delete_course(n_clicks, course_id, trigger):
    if not course_id:
        return no_update, no_update, {"display": "none"}
    try:
        with get_db() as db:
            course = db.query(Course).filter(Course.id == course_id).first()
            if course:
                course.is_active = False   # Soft delete
                code = course.code
            else:
                raise ValueError("Cours introuvable.")

        return (
            html.Div([html.I(className="fa-solid fa-circle-check"),
                      f" Cours « {code} » supprimé."],
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
# CALLBACKS — Vue Progression
# ═══════════════════════════════════════════════════════════════════════════════

@callback(
    Output("progress-kpis",       "children"),
    Output("chart-progress-bars", "figure"),
    Output("progress-cards-grid", "children"),
    Input("progress-interval",    "n_intervals"),
)
def update_progress_view(n):
    try:
        with get_db() as db:
            courses = db.query(Course).filter(Course.is_active == True).all()

            if not courses:
                empty = empty_state("fa-chart-line", "Aucun cours",
                                    "Ajoutez des cours pour voir la progression.")
                return [], go.Figure(), [empty]

            # FIX : calcul DANS la session (accès aux relations sessions)
            total_h_prev  = sum(c.total_hours for c in courses)
            total_h_done  = sum(c.completed_hours for c in courses)
            avg_progress  = round(sum(c.progress_percent for c in courses) / len(courses), 1)
            completed     = sum(1 for c in courses if c.progress_percent >= 100)

        # ── KPIs ──────────────────────────────────────────────────────
        kpi_data = [
            {"label": "Total Cours",           "value": len(courses),          "icon": "fa-book-open",     "color": "blue"},
            {"label": "Heures Prévues",        "value": f"{total_h_prev}h",    "icon": "fa-clock",         "color": "info"},
            {"label": "Heures Réalisées",      "value": f"{total_h_done}h",    "icon": "fa-circle-check",  "color": "green"},
            {"label": "Cours Terminés",        "value": completed,             "icon": "fa-flag-checkered","color": "orange"},
        ]
        kpis = [
            html.Div(className="kpi-card", children=[
                html.Div(html.I(className=f"fa-solid {k['icon']}"),
                         className=f"kpi-icon {k['color']}"),
                html.Div([
                    html.Div(str(k["value"]), className="kpi-value"),
                    html.Div(k["label"], className="kpi-label"),
                ], className="kpi-info"),
            ])
            for k in kpi_data
        ]

        # ── Graphique barres groupées ──────────────────────────────────
        labels = [c.code for c in courses]
        prevus = [c.total_hours for c in courses]
        realises = [c.completed_hours for c in courses]

        fig = go.Figure()
        fig.add_trace(go.Bar(name="Prévu", x=labels, y=prevus,
                             marker_color="#e8eaf6",
                             marker_line_color="#1a237e",
                             marker_line_width=1.5))
        fig.add_trace(go.Bar(name="Réalisé", x=labels, y=realises,
                             marker_color="#1a237e"))
        fig.update_layout(
            barmode="overlay",
            margin=dict(l=10, r=10, t=10, b=30),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font=dict(family="DM Sans", size=11, color="#6b7280"),
            xaxis=dict(showgrid=False),
            yaxis=dict(showgrid=True, gridcolor="#f1f5f9", title="Heures"),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0),
        )

        # ── Cartes par cours ───────────────────────────────────────────
        cards = []
        for c in sorted(courses, key=lambda x: x.progress_percent, reverse=True):
            pct = c.progress_percent
            badge_cls = "badge-success" if pct >= 100 else \
                        "badge-primary" if pct >= 50  else \
                        "badge-warning" if pct >= 20  else "badge-danger"
            badge_txt = "Terminé" if pct >= 100 else \
                        "En cours" if pct >= 20  else "Démarré"

            cards.append(html.Div(
                className="card",
                children=[
                    html.Div(className="card-header", children=[
                        html.Div([
                            html.Span(c.code,
                                      style={"fontFamily": "monospace", "fontWeight": "700",
                                             "fontSize": "0.85rem", "color": "#1a237e",
                                             "background": "#e8eaf6", "padding": "2px 8px",
                                             "borderRadius": "5px"}),
                        ], className="card-title"),
                        html.Span(badge_txt, className=f"badge {badge_cls}"),
                    ]),
                    html.Div(className="card-body", children=[
                        html.Div(c.label,
                                 style={"fontWeight": "500", "marginBottom": "4px"}),
                        html.Div(
                            [html.I(className="fa-solid fa-chalkboard-user",
                                    style={"marginRight": "4px", "color": "#9ca3af",
                                           "fontSize": "0.78rem"}),
                             c.teacher or "—"],
                            style={"fontSize": "0.8rem", "color": "#9ca3af", "marginBottom": "14px"},
                        ),
                        progress_bar(pct, label=f"{c.completed_hours}h / {c.total_hours}h",
                                     size="lg"),
                        html.Div(
                            [
                                html.Span(f"{len(c.sessions)} séance(s)",
                                          style={"fontSize": "0.78rem", "color": "#9ca3af"}),
                                html.Span(f"{c.total_hours - c.completed_hours:.1f}h restantes",
                                          style={"fontSize": "0.78rem", "color": "#9ca3af"}),
                            ],
                            style={"display": "flex", "justifyContent": "space-between",
                                   "marginTop": "10px"},
                        ),
                    ]),
                ],
            ))

        return kpis, fig, cards

    except Exception as e:
        err = html.Div(f"Erreur : {e}", className="alert alert-danger")
        return [], go.Figure(), [err]
    
    
    

