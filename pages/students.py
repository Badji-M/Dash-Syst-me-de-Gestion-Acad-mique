"""
pages/students.py — Module 3 : Gestion des Étudiants & Évaluations
- Liste CRUD des étudiants
- Fiche individuelle : infos + absentéisme + moyenne générale
- Gestion des notes par matière
- Workflow Excel : download template → saisie → upload → import DB
"""

from dash import html, dcc, callback, Output, Input, State, no_update, ctx, ALL
from datetime import date, datetime
import base64

from database.db import get_db
from database.models import Student, Course, Grade, Attendance, Session
from components.tables import empty_state, progress_bar
from components.modals import confirm_modal
from sqlalchemy import func
from sqlalchemy.orm import joinedload


# ═══════════════════════════════════════════════════════════════════════════════
# LAYOUT PRINCIPAL — Liste des étudiants
# ═══════════════════════════════════════════════════════════════════════════════
def layout():
    return html.Div(
        className="fade-in",
        children=[
            html.Div(className="page-header", children=[
                html.Div([
                    html.H1("Étudiants", className="page-title"),
                    html.P("Gestion des inscriptions et suivi académique",
                           className="page-subtitle"),
                ], className="page-header-left"),
                html.Div(className="page-header-actions", children=[
                    html.Button(
                        [html.I(className="fa-solid fa-file-excel"), " Exporter"],
                        id="btn-export-students",
                        className="btn btn-outline btn-sm",
                        **{"data-tooltip": "Exporter la liste en Excel"},
                        n_clicks=0,
                    ),
                    html.Button(
                        [html.I(className="fa-solid fa-plus"), " Nouvel Étudiant"],
                        id="btn-open-add-student",
                        className="btn btn-primary btn-sm",
                        n_clicks=0,
                    ),
                    dcc.Download(id="download-students-excel"),
                ]),
            ]),

            html.Div(id="student-feedback"),
            html.Div(id="student-form-container", children=_empty_student_form(),
                     style={"marginBottom": "20px"}),

            # ── Tableau étudiants ─────────────────────────────────────────
            html.Div(className="table-container", children=[
                html.Div(className="table-header", children=[
                    html.Div(
                        [html.I(className="fa-solid fa-users"), " Liste des Étudiants"],
                        className="table-title",
                    ),
                    html.Div(
                        style={"display": "flex", "gap": "10px", "alignItems": "center"},
                        children=[
                            html.Div(
                                [html.I(className="fa-solid fa-magnifying-glass",
                                        style={"position": "absolute", "left": "10px",
                                               "top": "50%", "transform": "translateY(-50%)",
                                               "color": "#9ca3af", "fontSize": "0.8rem",
                                               "pointerEvents": "none"}),
                                 dcc.Input(
                                     id="student-search",
                                     type="text",
                                     placeholder="Rechercher un étudiant...",
                                     debounce=True,
                                     className="form-control",
                                     style={"paddingLeft": "32px", "width": "220px",
                                            "fontSize": "0.85rem"},
                                 )],
                                style={"position": "relative"},
                            ),
                            html.Button(
                                html.I(className="fa-solid fa-rotate"),
                                id="btn-refresh-students",
                                className="btn btn-ghost btn-icon btn-sm",
                                **{"data-tooltip": "Actualiser"},
                                n_clicks=0,
                            ),
                        ],
                    ),
                ]),
                html.Div(id="students-table-body", style={"padding": "0"}),
            ]),

            confirm_modal(
                "delete-student",
                "Supprimer l'étudiant",
                "Cet étudiant sera désactivé. Ses notes et présences seront conservées.",
                confirm_label="Désactiver",
                confirm_icon="fa-user-slash",
                confirm_class="btn-danger",
            ),

            dcc.Store(id="student-edit-id",        data=None),
            dcc.Store(id="student-delete-id",      data=None),
            dcc.Store(id="students-refresh-trigger", data=0),
        ],
    )


# ═══════════════════════════════════════════════════════════════════════════════
# LAYOUT FICHE ÉTUDIANT
# ═══════════════════════════════════════════════════════════════════════════════
def layout_profile():
    return html.Div(
        className="fade-in",
        children=[
            html.Div(className="page-header", children=[
                html.Div([
                    html.H1("Fiche Étudiant", className="page-title"),
                    html.P("Détail du parcours académique", className="page-subtitle"),
                ], className="page-header-left"),
                html.Div([
                    dcc.Link(
                        [html.I(className="fa-solid fa-arrow-left"), " Retour"],
                        href="/students", className="btn btn-outline btn-sm",
                    ),
                ], className="page-header-actions"),
            ]),

            # Sélecteur étudiant
            html.Div(className="card mb-24", children=[
                html.Div(className="card-body", children=[
                    html.Div(className="grid-2", children=[
                        html.Div([
                            html.Label(
                                [html.I(className="fa-solid fa-user-graduate",
                                        style={"marginRight": "5px"}), "Sélectionner un étudiant"],
                                className="form-label",
                            ),
                            dcc.Dropdown(
                                id="profile-student-select",
                                placeholder="Choisir un étudiant...",
                                clearable=True,
                            ),
                        ], className="form-group"),
                    ]),
                ]),
            ]),

            html.Div(id="student-profile-content"),
            dcc.Interval(id="profile-interval", interval=60_000, n_intervals=0),
        ],
    )


# ═══════════════════════════════════════════════════════════════════════════════
# LAYOUT GESTION DES NOTES
# ═══════════════════════════════════════════════════════════════════════════════
def layout_grades():
    return html.Div(
        className="fade-in",
        children=[
            html.Div(className="page-header", children=[
                html.Div([
                    html.H1("Gestion des Notes", className="page-title"),
                    html.P("Saisie et consultation des évaluations", className="page-subtitle"),
                ], className="page-header-left"),
                html.Div([
                    dcc.Link(
                        [html.I(className="fa-solid fa-file-excel"), " Import Excel"],
                        href="/students/excel",
                        className="btn btn-outline btn-sm",
                    ),
                ], className="page-header-actions"),
            ]),

            html.Div(id="grades-feedback"),

            # Filtres
            html.Div(className="card mb-24", children=[
                html.Div(className="card-header", children=[
                    html.Div(
                        [html.I(className="fa-solid fa-filter"), " Filtres"],
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
                                id="grades-filter-course",
                                placeholder="Tous les cours",
                                clearable=True,
                            ),
                        ], className="form-group"),
                        html.Div([
                            html.Label(
                                [html.I(className="fa-solid fa-user-graduate",
                                        style={"marginRight": "5px"}), "Étudiant"],
                                className="form-label",
                            ),
                            dcc.Dropdown(
                                id="grades-filter-student",
                                placeholder="Tous les étudiants",
                                clearable=True,
                            ),
                        ], className="form-group"),
                    ]),
                ]),
            ]),

            # Formulaire saisie de note
            html.Div(id="grade-form-inline", className="mb-24"),

            html.Button(
                [html.I(className="fa-solid fa-plus"), " Ajouter une note"],
                id="btn-open-add-grade",
                className="btn btn-primary btn-sm mb-24",
                n_clicks=0,
            ),

            # Tableau des notes
            html.Div(className="table-container", children=[
                html.Div(className="table-header", children=[
                    html.Div(
                        [html.I(className="fa-solid fa-star-half-stroke"), " Notes"],
                        className="table-title",
                    ),
                ]),
                html.Div(id="grades-table-body", style={"padding": "0"}),
            ]),

            confirm_modal(
                "delete-grade",
                "Supprimer la note",
                "Cette note sera définitivement supprimée.",
                confirm_label="Supprimer",
                confirm_icon="fa-trash",
            ),

            dcc.Store(id="grade-delete-id",       data=None),
            dcc.Store(id="grade-edit-id",          data=None),
            dcc.Store(id="grades-refresh-trigger", data=0),
        ],
    )


# ═══════════════════════════════════════════════════════════════════════════════
# LAYOUT IMPORT / EXPORT EXCEL
# ═══════════════════════════════════════════════════════════════════════════════
def layout_excel():
    return html.Div(
        className="fade-in",
        children=[
            html.Div(className="page-header", children=[
                html.Div([
                    html.H1("Import / Export Excel", className="page-title"),
                    html.P("Workflow de saisie des notes via fichier Excel",
                           className="page-subtitle"),
                ], className="page-header-left"),
                html.Div([
                    dcc.Link(
                        [html.I(className="fa-solid fa-arrow-left"), " Retour"],
                        href="/students/grades",
                        className="btn btn-outline btn-sm",
                    ),
                ], className="page-header-actions"),
            ]),

            html.Div(id="excel-feedback"),

            html.Div(className="grid-2", children=[

                # ── Étape 1 : Télécharger le template ────────────────
                html.Div(className="card", children=[
                    html.Div(className="card-header", children=[
                        html.Div(
                            [html.I(className="fa-solid fa-circle-1",
                                    style={"background": "#1a237e", "color": "#fff",
                                           "borderRadius": "50%", "width": "22px",
                                           "height": "22px", "display": "inline-flex",
                                           "alignItems": "center", "justifyContent": "center",
                                           "fontSize": "0.75rem", "marginRight": "8px"}),
                             "Télécharger le Template"],
                            className="card-title",
                        ),
                    ]),
                    html.Div(className="card-body", children=[
                        html.Div([
                            html.Label(
                                [html.I(className="fa-solid fa-book-open",
                                        style={"marginRight": "5px"}), "Cours"],
                                className="form-label required",
                            ),
                            dcc.Dropdown(
                                id="excel-course-select",
                                placeholder="Sélectionner un cours",
                                clearable=False,
                            ),
                        ], className="form-group"),
                        html.Div([
                            html.Label(
                                [html.I(className="fa-solid fa-tag",
                                        style={"marginRight": "5px"}),
                                 "Libellé de l'évaluation"],
                                className="form-label required",
                            ),
                            dcc.Input(
                                id="excel-eval-label",
                                type="text",
                                placeholder="ex: Contrôle 1, Examen final...",
                                className="form-control",
                            ),
                        ], className="form-group"),
                        html.Button(
                            [html.I(className="fa-solid fa-download"), " Télécharger le Template"],
                            id="btn-download-template",
                            className="btn btn-primary",
                            style={"width": "100%", "justifyContent": "center"},
                            n_clicks=0,
                        ),
                        dcc.Download(id="download-grade-template"),
                        html.Div(
                            [html.I(className="fa-solid fa-circle-info",
                                    style={"marginRight": "5px"}),
                             "Le template est pré-rempli avec les noms et IDs des étudiants. "
                             "Remplissez uniquement la colonne Note /20."],
                            className="alert alert-info",
                            style={"marginTop": "14px", "fontSize": "0.82rem"},
                        ),
                    ]),
                ]),

                # ── Étape 2 : Importer le fichier rempli ─────────────
                html.Div(className="card", children=[
                    html.Div(className="card-header", children=[
                        html.Div(
                            [html.I(className="fa-solid fa-circle-2",
                                    style={"background": "#1a237e", "color": "#fff",
                                           "borderRadius": "50%", "width": "22px",
                                           "height": "22px", "display": "inline-flex",
                                           "alignItems": "center", "justifyContent": "center",
                                           "fontSize": "0.75rem", "marginRight": "8px"}),
                             "Importer le Fichier Rempli"],
                            className="card-title",
                        ),
                    ]),
                    html.Div(className="card-body", children=[
                        html.Div([
                            html.Label(
                                [html.I(className="fa-solid fa-book-open",
                                        style={"marginRight": "5px"}),
                                 "Cours concerné par l'import"],
                                className="form-label required",
                            ),
                            dcc.Dropdown(
                                id="excel-import-course",
                                placeholder="Sélectionner le cours",
                                clearable=False,
                            ),
                        ], className="form-group"),
                        html.Div([
                            html.Label(
                                [html.I(className="fa-solid fa-tag",
                                        style={"marginRight": "5px"}),
                                 "Libellé de l'évaluation"],
                                className="form-label required",
                            ),
                            dcc.Input(
                                id="excel-import-label",
                                type="text",
                                placeholder="Doit correspondre au template",
                                className="form-control",
                            ),
                        ], className="form-group"),
                        dcc.Upload(
                            id="upload-grades-excel",
                            children=html.Div(
                                [
                                    html.I(className="fa-solid fa-cloud-arrow-up",
                                           style={"fontSize": "2rem", "color": "#9ca3af",
                                                  "marginBottom": "8px"}),
                                    html.Br(),
                                    html.Strong("Glisser-déposer ou cliquer"),
                                    html.Br(),
                                    html.Span(".xlsx uniquement",
                                              style={"fontSize": "0.78rem", "color": "#9ca3af"}),
                                ],
                                style={"textAlign": "center"},
                            ),
                            style={
                                "width": "100%", "padding": "28px",
                                "border": "2px dashed #e2e8f0",
                                "borderRadius": "10px", "cursor": "pointer",
                                "textAlign": "center", "marginBottom": "14px",
                                "transition": "border-color 0.2s",
                            },
                            accept=".xlsx,.xls",
                            max_size=5 * 1024 * 1024,
                        ),
                        html.Div(id="upload-preview"),
                        html.Button(
                            [html.I(className="fa-solid fa-database"), " Importer dans la DB"],
                            id="btn-import-grades",
                            className="btn btn-success",
                            style={"width": "100%", "justifyContent": "center",
                                   "display": "none"},
                            n_clicks=0,
                        ),
                        dcc.Store(id="upload-parsed-data"),
                    ]),
                ]),
            ]),
            dcc.Store(id="excel-refresh-trigger", data=0),
        ],
    )


# ═══════════════════════════════════════════════════════════════════════════════
# HELPERS UI
# ═══════════════════════════════════════════════════════════════════════════════
def _empty_student_form():
    return html.Div(
        style={"display": "none"},
        children=[
            html.Button(id="btn-close-student-form", n_clicks=0),
            html.Button(id="btn-cancel-student-form", n_clicks=0),
            html.Button(id="btn-save-student", n_clicks=0),
            dcc.Input(id="student-input-lastname", value=""),
            dcc.Input(id="student-input-firstname", value=""),
            dcc.Input(id="student-input-email", value=""),
            dcc.DatePickerSingle(id="student-input-birthdate", date=None),
        ],
    )


def _student_form(student=None):
    is_edit = student is not None
    return html.Div(
        className="card",
        style={"borderLeft": "3px solid #1a237e"},
        children=[
            html.Div(className="card-header", children=[
                html.Div(
                    [html.I(className=f"fa-solid {'fa-pen-to-square' if is_edit else 'fa-user-plus'}"),
                     f" {'Modifier' if is_edit else 'Nouvel'} Étudiant"],
                    className="card-title",
                ),
                html.Button(
                    html.I(className="fa-solid fa-xmark"),
                    id="btn-close-student-form",
                    className="btn btn-ghost btn-icon btn-sm",
                    n_clicks=0,
                ),
            ]),
            html.Div(className="card-body", children=[
                html.Div(className="grid-2", children=[
                    html.Div([
                        html.Label([html.I(className="fa-solid fa-id-card",
                                           style={"marginRight": "5px"}), "Nom"],
                                   className="form-label required"),
                        dcc.Input(id="student-input-lastname", type="text",
                                  placeholder="Nom de famille",
                                  value=student.last_name if is_edit else "",
                                  className="form-control"),
                    ], className="form-group"),
                    html.Div([
                        html.Label([html.I(className="fa-solid fa-id-card",
                                           style={"marginRight": "5px"}), "Prénom"],
                                   className="form-label required"),
                        dcc.Input(id="student-input-firstname", type="text",
                                  placeholder="Prénom",
                                  value=student.first_name if is_edit else "",
                                  className="form-control"),
                    ], className="form-group"),
                    html.Div([
                        html.Label([html.I(className="fa-solid fa-envelope",
                                           style={"marginRight": "5px"}), "Email"],
                                   className="form-label required"),
                        dcc.Input(id="student-input-email", type="email",
                                  placeholder="adresse@email.com",
                                  value=student.email if is_edit else "",
                                  className="form-control"),
                    ], className="form-group"),
                    html.Div([
                        html.Label([html.I(className="fa-solid fa-cake-candles",
                                           style={"marginRight": "5px"}),
                                    "Date de naissance"],
                                   className="form-label"),
                        dcc.DatePickerSingle(
                            id="student-input-birthdate",
                            date=str(student.birth_date) if (is_edit and student.birth_date) else None,
                            display_format="DD/MM/YYYY",
                            style={"width": "100%"},
                        ),
                    ], className="form-group"),
                ]),
                html.Div(
                    style={"display": "flex", "gap": "10px",
                           "justifyContent": "flex-end", "marginTop": "8px"},
                    children=[
                        html.Button([html.I(className="fa-solid fa-xmark"), " Annuler"],
                                    id="btn-cancel-student-form", className="btn btn-ghost",
                                    n_clicks=0),
                        html.Button([html.I(className="fa-solid fa-floppy-disk"),
                                     " Enregistrer"],
                                    id="btn-save-student", className="btn btn-primary",
                                    n_clicks=0),
                    ],
                ),
            ]),
        ],
    )


def _build_students_table(students):
    if not students:
        return empty_state("fa-user-graduate", "Aucun étudiant enregistré",
                           "Cliquez sur « Nouvel Étudiant » pour commencer.")

    header = html.Div(
        style={"display": "grid",
               "gridTemplateColumns": "50px 1fr 200px 80px 90px 90px",
               "gap": "12px", "padding": "10px 20px",
               "background": "#f8fafc", "borderBottom": "1px solid #e2e8f0"},
        children=[_th("#"), _th("Étudiant"), _th("Email"), _th("Moy."),
                  _th("Absences", center=True), _th("Actions", right=True)],
    )

    rows = []
    for i, s in enumerate(students, 1):
        try:
            with get_db() as db:
                avg = db.query(func.avg(Grade.grade)).filter(
                    Grade.student_id == s.id
                ).scalar()
                nb_abs = db.query(func.count(Attendance.id)).filter(
                    Attendance.student_id == s.id,
                    Attendance.is_absent == True,
                ).scalar() or 0
                nb_total = db.query(func.count(Attendance.id)).filter(
                    Attendance.student_id == s.id,
                ).scalar() or 1
        except Exception:
            avg, nb_abs, nb_total = None, 0, 1

        avg_str    = f"{avg:.1f}/20" if avg else "—"
        avg_color  = "#2e7d32" if (avg and avg >= 10) else "#e53935" if avg else "#9ca3af"
        abs_rate   = round(nb_abs / nb_total * 100)
        abs_color  = "#e53935" if abs_rate > 20 else "#f57f17" if abs_rate > 10 else "#2e7d32"

        rows.append(html.Div(
            className="table-row-hover",
            style={"display": "grid",
                   "gridTemplateColumns": "50px 1fr 200px 80px 90px 90px",
                   "gap": "12px", "padding": "13px 20px",
                   "borderBottom": "1px solid #f1f5f9", "alignItems": "center"},
            children=[
                html.Span(str(i), style={"color": "#9ca3af", "fontSize": "0.82rem",
                                          "textAlign": "center"}),
                html.Div([
                    html.Div(
                        style={"display": "flex", "alignItems": "center", "gap": "10px"},
                        children=[
                            html.Div(
                                f"{s.first_name[0]}{s.last_name[0]}".upper(),
                                style={"width": "34px", "height": "34px",
                                       "background": "#e8eaf6", "borderRadius": "50%",
                                       "display": "flex", "alignItems": "center",
                                       "justifyContent": "center", "fontSize": "0.78rem",
                                       "fontWeight": "700", "color": "#1a237e",
                                       "flexShrink": "0"},
                            ),
                            html.Div([
                                html.Div(s.full_name, style={"fontWeight": "500",
                                                              "fontSize": "0.88rem"}),
                                html.Div(f"ID: {s.id}",
                                         style={"fontSize": "0.75rem", "color": "#9ca3af"}),
                            ]),
                        ],
                    ),
                ]),
                html.Div(s.email, style={"fontSize": "0.83rem", "color": "#6b7280"}),
                html.Div(avg_str, style={"fontWeight": "700", "color": avg_color,
                                          "fontSize": "0.9rem"}),
                html.Div(
                    [html.I(className="fa-solid fa-user-xmark",
                             style={"marginRight": "4px", "fontSize": "0.78rem"}),
                     f"{nb_abs} abs."],
                    style={"color": abs_color, "fontSize": "0.83rem",
                           "fontWeight": "500", "textAlign": "center"},
                ),
                html.Div(
                    style={"display": "flex", "gap": "5px", "justifyContent": "flex-end"},
                    children=[
                        dcc.Link(
                            html.Button(
                                html.I(className="fa-solid fa-eye"),
                                className="btn btn-icon btn-sm btn-view",
                                **{"data-tooltip": "Voir la fiche"},
                                n_clicks=0,
                            ),
                            href="/students/profile",
                        ),
                        html.Button(
                            html.I(className="fa-solid fa-pen-to-square"),
                            id={"type": "student-btn-edit", "index": s.id},
                            className="btn btn-icon btn-sm btn-edit",
                            **{"data-tooltip": "Modifier"},
                            n_clicks=0,
                        ),
                        html.Button(
                            html.I(className="fa-solid fa-user-slash"),
                            id={"type": "student-btn-delete", "index": s.id},
                            className="btn btn-icon btn-sm btn-delete",
                            **{"data-tooltip": "Désactiver"},
                            n_clicks=0,
                        ),
                    ],
                ),
            ],
        ))

    return html.Div([header] + rows)


def _th(label, center=False, right=False):
    return html.Span(label, style={
        "fontSize": "0.75rem", "fontWeight": "700",
        "textTransform": "uppercase", "color": "#6b7280",
        "letterSpacing": "0.05em",
        "textAlign": "center" if center else ("right" if right else "left"),
    })


# ═══════════════════════════════════════════════════════════════════════════════
# CALLBACKS — Liste Étudiants
# ═══════════════════════════════════════════════════════════════════════════════

@callback(
    Output("students-table-body",     "children"),
    Input("students-refresh-trigger", "data"),
    Input("student-search",           "value"),
    Input("btn-refresh-students",     "n_clicks"),
)
def load_students_table(trigger, search, n_refresh):
    try:
        with get_db() as db:
            q = db.query(Student).filter(Student.is_active == True)
            if search:
                q = q.filter(
                    (Student.last_name.ilike(f"%{search}%")) |
                    (Student.first_name.ilike(f"%{search}%")) |
                    (Student.email.ilike(f"%{search}%"))
                )
            students = q.order_by(Student.last_name, Student.first_name).all()
            # FIX : construire le HTML DANS la session
            table_html = _build_students_table(students)
        return table_html
    except Exception as e:
        return html.Div(f"Erreur : {e}", className="alert alert-danger")


@callback(
    Output("student-form-container", "children"),
    Output("student-edit-id",        "data"),
    Input("btn-open-add-student",    "n_clicks"),
    Input("btn-close-student-form",  "n_clicks"),
    Input("btn-cancel-student-form", "n_clicks"),
    Input({"type": "student-btn-edit", "index": ALL}, "n_clicks"),
    State({"type": "student-btn-edit", "index": ALL}, "id"),
    prevent_initial_call=True,
)
def toggle_student_form(n_add, n_close, n_cancel, n_edits, edit_ids):
    triggered = ctx.triggered_id
    if triggered in ("btn-close-student-form", "btn-cancel-student-form"):
        return _empty_student_form(), None
    if triggered == "btn-open-add-student":
        return _student_form(None), None
    if isinstance(triggered, dict) and triggered.get("type") == "student-btn-edit":
        clicked = False
        for clicks, button_id in zip(n_edits or [], edit_ids or []):
            if button_id == triggered:
                clicked = bool(clicks and clicks > 0)
                break

        if not clicked:
            return no_update, no_update

        sid = triggered["index"]
        with get_db() as db:
            s = db.query(Student).filter(Student.id == sid).first()
        if s:
            return _student_form(s), sid
    return no_update, no_update


@callback(
    Output("student-feedback",          "children"),
    Output("students-refresh-trigger",  "data"),
    Output("student-form-container",    "children", allow_duplicate=True),
    Input("btn-save-student",           "n_clicks"),
    State("student-input-lastname",     "value"),
    State("student-input-firstname",    "value"),
    State("student-input-email",        "value"),
    State("student-input-birthdate",    "date"),
    State("student-edit-id",            "data"),
    State("students-refresh-trigger",   "data"),
    prevent_initial_call=True,
)
def save_student(n, last, first, email, bdate, edit_id, trigger):
    if not n:
        return no_update, no_update, no_update

    errors = []
    if not last or not last.strip():   errors.append("Le nom est requis.")
    if not first or not first.strip(): errors.append("Le prénom est requis.")
    if not email or "@" not in email:  errors.append("L'email est invalide.")

    birth_date = None
    if bdate:
        try:
            birth_date = datetime.strptime(bdate, "%Y-%m-%d").date()
        except ValueError:
            errors.append("La date de naissance est invalide.")

    if errors:
        return (
            html.Div([html.I(className="fa-solid fa-circle-exclamation"),
                      html.Ul([html.Li(e) for e in errors],
                              style={"margin": "6px 0 0 16px"})],
                     className="alert alert-warning"),
            no_update, no_update,
        )
    try:
        with get_db() as db:
            if edit_id:
                s = db.query(Student).filter(Student.id == edit_id).first()
                ex = db.query(Student).filter(Student.email == email.strip(),
                                              Student.id != edit_id).first()
                if ex: raise ValueError("Email déjà utilisé.")
                s.last_name  = last.strip().upper()
                s.first_name = first.strip()
                s.email      = email.strip().lower()
                s.birth_date = birth_date
                msg = f"Étudiant « {s.full_name} » mis à jour."
            else:
                ex = db.query(Student).filter(Student.email == email.strip()).first()
                if ex: raise ValueError("Email déjà utilisé.")
                s = Student(last_name=last.strip().upper(),
                            first_name=first.strip(),
                            email=email.strip().lower(),
                            birth_date=birth_date)
                db.add(s)
                msg = f"Étudiant « {last} {first} » ajouté."

        return (
            html.Div([html.I(className="fa-solid fa-circle-check"), f" {msg}"],
                     className="alert alert-success"),
            (trigger or 0) + 1, _empty_student_form(),
        )
    except ValueError as ve:
        return (html.Div([html.I(className="fa-solid fa-circle-xmark"), f" {ve}"],
                         className="alert alert-danger"), no_update, no_update)
    except Exception as e:
        return (html.Div([html.I(className="fa-solid fa-circle-xmark"), f" Erreur : {e}"],
                         className="alert alert-danger"), no_update, no_update)


@callback(
    Output("delete-student-overlay", "style"),
    Output("student-delete-id",      "data"),
    Input({"type": "student-btn-delete", "index": ALL}, "n_clicks"),
    Input("delete-student-cancel",   "n_clicks"),
    Input("delete-student-close",    "n_clicks"),
    State({"type": "student-btn-delete", "index": ALL}, "id"),
    prevent_initial_call=True,
)
def toggle_student_delete(n_del, n_cancel, n_close, delete_ids):
    t = ctx.triggered_id
    if t in ("delete-student-cancel", "delete-student-close"):
        return {"display": "none"}, None
    if isinstance(t, dict) and t.get("type") == "student-btn-delete":
        for clicks, button_id in zip(n_del or [], delete_ids or []):
            if button_id == t:
                if clicks and clicks > 0:
                    return {"display": "flex"}, t["index"]
                break
        return {"display": "none"}, None
    return {"display": "none"}, None


@callback(
    Output("student-feedback",          "children", allow_duplicate=True),
    Output("students-refresh-trigger",  "data",     allow_duplicate=True),
    Output("delete-student-overlay",    "style",    allow_duplicate=True),
    Input("delete-student-confirm",     "n_clicks"),
    State("student-delete-id",          "data"),
    State("students-refresh-trigger",   "data"),
    prevent_initial_call=True,
)
def confirm_delete_student(n, sid, trigger):
    if not sid: return no_update, no_update, {"display": "none"}
    try:
        with get_db() as db:
            s = db.query(Student).filter(Student.id == sid).first()
            if s:
                s.is_active = False
                name = s.full_name
        return (
            html.Div([html.I(className="fa-solid fa-circle-check"),
                      f" Étudiant « {name} » désactivé."],
                     className="alert alert-success"),
            (trigger or 0) + 1, {"display": "none"},
        )
    except Exception as e:
        return (html.Div([html.I(className="fa-solid fa-circle-xmark"), f" {e}"],
                         className="alert alert-danger"),
                no_update, {"display": "none"})


# Export liste Excel
@callback(
    Output("download-students-excel", "data"),
    Input("btn-export-students",      "n_clicks"),
    prevent_initial_call=True,
)
def export_students(n_clicks):
    try:
        from utils.excel_handler import export_students_list
        with get_db() as db:
            students = db.query(Student).filter(Student.is_active == True)\
                         .order_by(Student.last_name).all()
        content = export_students_list(students)
        return dcc.send_bytes(content, "liste_etudiants.xlsx")
    except Exception as e:
        return no_update


# ═══════════════════════════════════════════════════════════════════════════════
# CALLBACKS — Fiche Étudiant
# ═══════════════════════════════════════════════════════════════════════════════

@callback(
    Output("profile-student-select", "options"),
    Input("profile-interval",        "n_intervals"),
)
def load_profile_students(n):
    try:
        with get_db() as db:
            students = db.query(Student).filter(Student.is_active == True)\
                         .order_by(Student.last_name).all()
        return [{"label": f"{s.full_name} (ID: {s.id})", "value": s.id}
                for s in students]
    except Exception:
        return []


@callback(
    Output("student-profile-content", "children"),
    Input("profile-student-select",   "value"),
)
def display_student_profile(student_id):
    if not student_id:
        return html.Div(
            style={"textAlign": "center", "padding": "40px", "color": "#9ca3af"},
            children=[
                html.I(className="fa-solid fa-user-graduate",
                       style={"fontSize": "2.5rem", "color": "#e2e8f0",
                              "marginBottom": "12px", "display": "block"}),
                "Sélectionnez un étudiant pour afficher sa fiche.",
            ],
        )

    try:
        with get_db() as db:
            s = db.query(Student).filter(Student.id == student_id).first()
            if not s:
                return html.Div("Étudiant introuvable.", className="alert alert-danger")

            grades    = db.query(Grade).filter(Grade.student_id == student_id).all()
            nb_abs    = db.query(func.count(Attendance.id)).filter(
                Attendance.student_id == student_id, Attendance.is_absent == True
            ).scalar() or 0
            nb_total  = db.query(func.count(Attendance.id)).filter(
                Attendance.student_id == student_id
            ).scalar() or 1

            # Moyennes par cours
            course_avgs = db.query(
                Course.code, Course.label,
                func.avg(Grade.grade).label("avg"),
                func.count(Grade.id).label("nb"),
            ).join(Grade, Grade.course_id == Course.id)\
             .filter(Grade.student_id == student_id)\
             .group_by(Course.id).all()

            # Calcul moyenne générale DANS la session
            if grades:
                total_w = sum(g.grade * g.coefficient for g in grades)
                total_c = sum(g.coefficient for g in grades)
                avg_general = total_w / total_c if total_c > 0 else None
            else:
                avg_general = None

        abs_rate     = round(nb_abs / nb_total * 100, 1)
        presence_rate = 100 - abs_rate

        # ── En-tête fiche ─────────────────────────────────────────────
        profile_header = html.Div(
            className="card mb-24",
            style={"background": "linear-gradient(135deg, #1a237e 0%, #283593 100%)"},
            children=[
                html.Div(className="card-body", children=[
                    html.Div(
                        style={"display": "flex", "alignItems": "center",
                               "gap": "20px", "color": "#fff"},
                        children=[
                            html.Div(
                                f"{s.first_name[0]}{s.last_name[0]}".upper(),
                                style={"width": "72px", "height": "72px",
                                       "background": "rgba(255,255,255,0.2)",
                                       "borderRadius": "50%", "display": "flex",
                                       "alignItems": "center", "justifyContent": "center",
                                       "fontSize": "1.6rem", "fontWeight": "700",
                                       "flexShrink": "0"},
                            ),
                            html.Div([
                                html.Div(s.full_name,
                                         style={"fontSize": "1.4rem", "fontWeight": "700",
                                                "fontFamily": "'DM Serif Display', serif"}),
                                html.Div(
                                    [html.I(className="fa-solid fa-envelope",
                                            style={"marginRight": "6px",
                                                   "opacity": "0.7"}),
                                     s.email],
                                    style={"fontSize": "0.88rem", "opacity": "0.85",
                                           "marginTop": "4px"},
                                ),
                                html.Div(
                                    [html.I(className="fa-solid fa-hashtag",
                                            style={"marginRight": "6px",
                                                   "opacity": "0.7"}),
                                     f"ID : {s.id}"],
                                    style={"fontSize": "0.82rem", "opacity": "0.7",
                                           "marginTop": "3px"},
                                ),
                            ]),
                        ],
                    ),
                ]),
            ],
        )

        # ── KPIs fiche ────────────────────────────────────────────────
        kpis = html.Div(className="grid-4 mb-24", children=[
            _kpi_mini("fa-star", "Moyenne générale",
                      f"{avg_general:.1f}/20" if avg_general else "—",
                      "#2e7d32" if (avg_general and avg_general >= 10) else "#e53935"),
            _kpi_mini("fa-book-open",     "Cours suivis",   str(len(course_avgs)), "#1a237e"),
            _kpi_mini("fa-clipboard-check", "Taux de présence",
                      f"{presence_rate:.0f}%",
                      "#2e7d32" if presence_rate >= 75 else "#f57f17"),
            _kpi_mini("fa-user-xmark",    "Absences",       str(nb_abs), "#e53935"),
        ])

        # ── Tableau notes par cours ───────────────────────────────────
        note_rows = []
        for ca in course_avgs:
            avg_val  = round(ca.avg, 2) if ca.avg else 0
            avg_col  = "#2e7d32" if avg_val >= 10 else "#e53935"
            note_rows.append(html.Div(
                style={"display": "grid",
                       "gridTemplateColumns": "80px 1fr 100px 100px",
                       "gap": "12px", "padding": "12px 20px",
                       "borderBottom": "1px solid #f1f5f9", "alignItems": "center"},
                children=[
                    html.Span(ca.code,
                              style={"fontFamily": "monospace", "fontWeight": "700",
                                     "fontSize": "0.8rem", "color": "#1a237e",
                                     "background": "#e8eaf6", "padding": "2px 8px",
                                     "borderRadius": "5px"}),
                    html.Span(ca.label, style={"fontSize": "0.87rem"}),
                    html.Span(f"{ca.nb} note(s)",
                              style={"fontSize": "0.8rem", "color": "#9ca3af",
                                     "textAlign": "center"}),
                    html.Span(f"{avg_val:.1f}/20",
                              style={"fontWeight": "700", "color": avg_col,
                                     "textAlign": "center", "fontSize": "0.9rem"}),
                ],
            ))

        grades_section = html.Div(className="table-container mb-24", children=[
            html.Div(className="table-header", children=[
                html.Div([html.I(className="fa-solid fa-star-half-stroke"),
                          " Résultats par Matière"], className="table-title"),
            ]),
            html.Div(
                style={"display": "grid",
                       "gridTemplateColumns": "80px 1fr 100px 100px",
                       "gap": "12px", "padding": "10px 20px",
                       "background": "#f8fafc", "borderBottom": "1px solid #e2e8f0"},
                children=[_th("Code"), _th("Cours"), _th("Évals", center=True),
                          _th("Moyenne", center=True)],
            ),
            html.Div(note_rows if note_rows else
                     [html.P("Aucune note.", style={"padding": "16px 20px",
                                                    "color": "#9ca3af"})]),
        ])

        # ── Présences ─────────────────────────────────────────────────
        presence_section = html.Div(className="card", children=[
            html.Div(className="card-header", children=[
                html.Div([html.I(className="fa-solid fa-clipboard-check"),
                          " Présences"], className="card-title"),
            ]),
            html.Div(className="card-body", children=[
                progress_bar(int(presence_rate),
                             label=f"{nb_total - nb_abs} présences / {nb_total} séances",
                             size="lg"),
            ]),
        ])

        return html.Div([profile_header, kpis, grades_section, presence_section])

    except Exception as e:
        return html.Div(f"Erreur : {e}", className="alert alert-danger")


def _kpi_mini(icon, label, value, color):
    return html.Div(className="kpi-card", children=[
        html.Div(html.I(className=f"fa-solid {icon}"),
                 className="kpi-icon",
                 style={"background": f"{color}18", "color": color,
                        "width": "42px", "height": "42px",
                        "borderRadius": "10px", "display": "flex",
                        "alignItems": "center", "justifyContent": "center",
                        "fontSize": "1.1rem"}),
        html.Div([
            html.Div(value, className="kpi-value", style={"color": color}),
            html.Div(label, className="kpi-label"),
        ], className="kpi-info"),
    ])


# ═══════════════════════════════════════════════════════════════════════════════
# CALLBACKS — Notes & Import Excel
# ═══════════════════════════════════════════════════════════════════════════════

@callback(
    Output("grades-filter-course",  "options"),
    Output("grades-filter-student", "options"),
    Input("grades-refresh-trigger", "data"),
)
def load_grade_filter_options(trigger):
    try:
        with get_db() as db:
            courses  = db.query(Course).filter(Course.is_active == True).all()
            students = db.query(Student).filter(Student.is_active == True)\
                         .order_by(Student.last_name).all()
        c_opts = [{"label": f"{c.code} — {c.label}", "value": c.id} for c in courses]
        s_opts = [{"label": s.full_name, "value": s.id} for s in students]
        return c_opts, s_opts
    except Exception:
        return [], []


@callback(
    Output("excel-course-select",  "options"),
    Output("excel-import-course",  "options"),
    Input("excel-refresh-trigger", "data"),
)
def load_excel_options(trigger):
    try:
        with get_db() as db:
            courses = db.query(Course).filter(Course.is_active == True).all()
        c_opts = [{"label": f"{c.code} — {c.label}", "value": c.id} for c in courses]
        return c_opts, c_opts
    except Exception:
        return [], []


@callback(
    Output("grades-table-body",     "children"),
    Input("grades-refresh-trigger", "data"),
    Input("grades-filter-course",   "value"),
    Input("grades-filter-student",  "value"),
)
def load_grades_table(trigger, course_id, student_id):
    try:
        with get_db() as db:
            q = db.query(Grade).options(
                joinedload(Grade.student),
                joinedload(Grade.course),
            )
            if course_id:   q = q.filter(Grade.course_id  == course_id)
            if student_id:  q = q.filter(Grade.student_id == student_id)
            grades = q.order_by(Grade.date.desc()).all()
            # Matérialiser les attributs dans la session
            rows_data = []
            for g in grades:
                rows_data.append({
                    "id": g.id, "grade": g.grade, "label": g.label,
                    "coefficient": g.coefficient,
                    "student_name": g.student.full_name if g.student else "—",
                    "course_code": g.course.code if g.course else "—",
                })

        if not rows_data:
            return empty_state("fa-star-half-stroke", "Aucune note",
                               "Utilisez le formulaire ou l'import Excel.")

        header = html.Div(
            style={"display": "grid",
                   "gridTemplateColumns": "1fr 140px 80px 60px 90px 70px",
                   "gap": "12px", "padding": "10px 20px",
                   "background": "#f8fafc", "borderBottom": "1px solid #e2e8f0"},
            children=[_th("Étudiant"), _th("Cours"), _th("Évaluation"),
                      _th("Note"), _th("Coeff"), _th("Actions", right=True)],
        )

        rows = []
        for g in rows_data:
            note_color = "#2e7d32" if g["grade"] >= 10 else "#e53935"
            rows.append(html.Div(
                className="table-row-hover",
                style={"display": "grid",
                       "gridTemplateColumns": "1fr 140px 80px 60px 90px 70px",
                       "gap": "12px", "padding": "12px 20px",
                       "borderBottom": "1px solid #f1f5f9", "alignItems": "center"},
                children=[
                    html.Div(g["student_name"],
                             style={"fontWeight": "500", "fontSize": "0.87rem"}),
                    html.Span(g["course_code"],
                              style={"fontFamily": "monospace", "fontSize": "0.82rem",
                                     "color": "#1a237e", "background": "#e8eaf6",
                                     "padding": "2px 7px", "borderRadius": "5px"}),
                    html.Div(g["label"] or "—",
                             style={"fontSize": "0.82rem", "color": "#6b7280"}),
                    html.Div(f"{g['grade']:.1f}",
                             style={"fontWeight": "700", "color": note_color,
                                    "fontSize": "0.95rem"}),
                    html.Div(f"× {g['coefficient']}",
                             style={"fontSize": "0.82rem", "color": "#9ca3af"}),
                    html.Div(
                        html.Button(
                            html.I(className="fa-solid fa-trash"),
                            id={"type": "grade-btn-delete", "index": g["id"]},
                            className="btn btn-icon btn-sm btn-delete",
                            **{"data-tooltip": "Supprimer"},
                            n_clicks=0,
                        ),
                        style={"display": "flex", "justifyContent": "flex-end"},
                    ),
                ],
            ))

        return html.Div([header] + rows)
    except Exception as e:
        return html.Div(f"Erreur : {e}", className="alert alert-danger")


# Télécharger template
@callback(
    Output("download-grade-template", "data"),
    Input("btn-download-template",    "n_clicks"),
    State("excel-course-select",      "value"),
    State("excel-eval-label",         "value"),
    prevent_initial_call=True,
)
def download_template(n_clicks, course_id, eval_label):
    if not course_id or not eval_label:
        return no_update
    try:
        from utils.excel_handler import generate_grade_template
        with get_db() as db:
            course   = db.query(Course).filter(Course.id == course_id).first()
            students = db.query(Student).filter(Student.is_active == True)\
                         .order_by(Student.last_name).all()
        content = generate_grade_template(
            students, course.code, course.label,
            eval_label=eval_label, teacher=course.teacher or "",
        )
        fname = f"template_notes_{course.code}_{eval_label.replace(' ','_')}.xlsx"
        return dcc.send_bytes(content, fname)
    except Exception:
        return no_update


# Parser le fichier uploadé
@callback(
    Output("upload-preview",        "children"),
    Output("upload-parsed-data",    "data"),
    Output("btn-import-grades",     "style"),
    Input("upload-grades-excel",    "contents"),
    State("upload-grades-excel",    "filename"),
    prevent_initial_call=True,
)
def parse_upload(contents, filename):
    if not contents:
        return no_update, no_update, {"display": "none"}
    try:
        from utils.excel_handler import parse_grade_upload
        success, result = parse_grade_upload(contents, filename)
        if success:
            preview = html.Div(
                [html.I(className="fa-solid fa-circle-check"),
                 f" {len(result)} note(s) prêtes à importer depuis « {filename} »"],
                className="alert alert-success",
            )
            return preview, result, {
                "width": "100%", "justifyContent": "center", "display": "flex"
            }
        else:
            return (
                html.Div([html.I(className="fa-solid fa-circle-xmark"), f" {result}"],
                         className="alert alert-danger"),
                None, {"display": "none"},
            )
    except Exception as e:
        return (
            html.Div([html.I(className="fa-solid fa-triangle-exclamation"), f" {e}"],
                     className="alert alert-danger"),
            None, {"display": "none"},
        )


# Importer les notes en DB
@callback(
    Output("excel-feedback",        "children"),
    Input("btn-import-grades",      "n_clicks"),
    State("upload-parsed-data",     "data"),
    State("excel-import-course",    "value"),
    State("excel-import-label",     "value"),
    prevent_initial_call=True,
)
def import_grades_to_db(n_clicks, records, course_id, eval_label):
    if not records or not course_id or not eval_label:
        return html.Div(
            [html.I(className="fa-solid fa-circle-exclamation"),
             " Sélectionnez un cours, un libellé et uploadez un fichier."],
            className="alert alert-warning",
        )
    try:
        imported, skipped, errors = 0, 0, []
        with get_db() as db:
            for rec in records:
                s = db.query(Student).filter(Student.id == rec["student_id"]).first()
                if not s:
                    errors.append(f"ID {rec['student_id']} introuvable.")
                    skipped += 1
                    continue
                # Upsert : supprimer l'ancienne note si elle existe
                from sqlalchemy import and_
                existing = db.query(Grade).filter(
                    and_(Grade.student_id == rec["student_id"],
                         Grade.course_id  == course_id,
                         Grade.label      == eval_label)
                ).first()
                if existing:
                    existing.grade       = rec["grade"]
                    existing.coefficient = rec["coefficient"]
                else:
                    grade = Grade(
                        student_id  = rec["student_id"],
                        course_id   = course_id,
                        grade       = rec["grade"],
                        coefficient = rec["coefficient"],
                        label       = eval_label,
                    )
                    db.add(grade)
                imported += 1

        msg = f"{imported} note(s) importée(s) avec succès."
        if skipped: msg += f" {skipped} ligne(s) ignorée(s)."
        return html.Div([html.I(className="fa-solid fa-circle-check"), f" {msg}"],
                        className="alert alert-success")
    except Exception as e:
        return html.Div([html.I(className="fa-solid fa-circle-xmark"), f" Erreur : {e}"],
                        className="alert alert-danger")


# Supprimer une note
@callback(
    Output("delete-grade-overlay",   "style"),
    Output("grade-delete-id",        "data"),
    Input({"type": "grade-btn-delete", "index": ALL}, "n_clicks"),
    Input("delete-grade-cancel",     "n_clicks"),
    Input("delete-grade-close",      "n_clicks"),
    State({"type": "grade-btn-delete", "index": ALL}, "id"),
    prevent_initial_call=True,
)
def toggle_grade_delete(n_del, n_cancel, n_close, delete_ids):
    t = ctx.triggered_id
    if t in ("delete-grade-cancel", "delete-grade-close"):
        return {"display": "none"}, None
    if isinstance(t, dict) and t.get("type") == "grade-btn-delete":
        for clicks, button_id in zip(n_del or [], delete_ids or []):
            if button_id == t:
                if clicks and clicks > 0:
                    return {"display": "flex"}, t["index"]
                break
        return {"display": "none"}, None
    return {"display": "none"}, None


@callback(
    Output("grades-feedback",        "children",  allow_duplicate=True),
    Output("grades-refresh-trigger", "data",      allow_duplicate=True),
    Output("delete-grade-overlay",   "style",     allow_duplicate=True),
    Input("delete-grade-confirm",    "n_clicks"),
    State("grade-delete-id",         "data"),
    State("grades-refresh-trigger",  "data"),
    prevent_initial_call=True,
)
def confirm_delete_grade(n, gid, trigger):
    if not gid: return no_update, no_update, {"display": "none"}
    try:
        with get_db() as db:
            g = db.query(Grade).filter(Grade.id == gid).first()
            if g: db.delete(g)
        return (
            html.Div([html.I(className="fa-solid fa-circle-check"), " Note supprimée."],
                     className="alert alert-success"),
            (trigger or 0) + 1, {"display": "none"},
        )
    except Exception as e:
        return (html.Div([html.I(className="fa-solid fa-circle-xmark"), f" {e}"],
                         className="alert alert-danger"),
                no_update, {"display": "none"})
