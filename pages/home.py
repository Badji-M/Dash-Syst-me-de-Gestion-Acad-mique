"""
pages/home.py — Dashboard principal du SGA
Vue d'ensemble : KPIs, activité récente, graphiques de synthèse.
"""

from dash import html, dcc, callback, Output, Input
import plotly.graph_objects as go
import plotly.express as px


# ─── Layout de la page ────────────────────────────────────────────────────────
def layout():
    return html.Div(
        className="fade-in",
        children=[

            # ── Page Header ────────────────────────────────────────────────
            html.Div(
                className="page-header",
                children=[
                    html.Div(
                        className="page-header-left",
                        children=[
                            html.H1("Tableau de Bord", className="page-title"),
                            html.P(
                                "Vue d'ensemble du système académique",
                                className="page-subtitle",
                            ),
                        ],
                    ),
                    html.Div(
                        className="page-header-actions",
                        children=[
                            html.Button(
                                [html.I(className="fa-solid fa-rotate"), " Actualiser"],
                                className="btn btn-outline btn-sm",
                                id="btn-refresh-dashboard",
                                **{"data-tooltip": "Actualiser les données"},
                            ),
                            html.Button(
                                [html.I(className="fa-solid fa-file-pdf"), " Rapport PDF"],
                                className="btn btn-primary btn-sm",
                                id="btn-export-dashboard-pdf",
                                **{"data-tooltip": "Exporter en PDF"},
                            ),
                        ],
                    ),
                ],
            ),

            # ── KPI Cards (Row 1) ──────────────────────────────────────────
            html.Div(id="kpi-row", className="grid-4 mb-24"),

            # ── Charts Row ────────────────────────────────────────────────
            html.Div(
                className="grid-2 mb-24",
                children=[
                    # Graphique distribution des notes
                    html.Div(
                        className="chart-container",
                        children=[
                            html.Div(
                                [
                                    html.I(className="fa-solid fa-chart-bar"),
                                    " Distribution des Notes",
                                ],
                                className="chart-title",
                            ),
                            dcc.Graph(
                                id="chart-grades-distribution",
                                config={"displayModeBar": False},
                                style={"height": "280px"},
                            ),
                        ],
                    ),
                    # Graphique progression des cours
                    html.Div(
                        className="chart-container",
                        children=[
                            html.Div(
                                [
                                    html.I(className="fa-solid fa-chart-line"),
                                    " Progression des Cours",
                                ],
                                className="chart-title",
                            ),
                            dcc.Graph(
                                id="chart-courses-progress",
                                config={"displayModeBar": False},
                                style={"height": "280px"},
                            ),
                        ],
                    ),
                ],
            ),

            # ── Row 3 : Activité récente + Taux présence ──────────────────
            html.Div(
                className="grid-2",
                children=[
                    # Tableau activités récentes
                    html.Div(
                        className="table-container",
                        children=[
                            html.Div(
                                className="table-header",
                                children=[
                                    html.Div(
                                        [html.I(className="fa-solid fa-clock-rotate-left"),
                                         " Activité Récente"],
                                        className="table-title",
                                    ),
                                    dcc.Link(
                                        [html.I(className="fa-solid fa-arrow-right",
                                                style={"marginRight": "5px"}), "Voir tout"],
                                        href="/sessions",
                                        className="btn btn-ghost btn-sm",
                                    ),
                                ],
                            ),
                            html.Div(id="recent-activity-list", className="card-body"),
                        ],
                    ),

                    # Taux d'absentéisme par cours
                    html.Div(
                        className="chart-container",
                        children=[
                            html.Div(
                                [html.I(className="fa-solid fa-user-check"),
                                 " Taux de Présence par Cours"],
                                className="chart-title",
                            ),
                            dcc.Graph(
                                id="chart-attendance-rate",
                                config={"displayModeBar": False},
                                style={"height": "280px"},
                            ),
                        ],
                    ),
                ],
            ),

            # Store pour les données du dashboard
            dcc.Store(id="dashboard-data-store"),
            dcc.Interval(id="dashboard-interval", interval=30_000, n_intervals=0),
        ],
    )


# ─── Callbacks du Dashboard ───────────────────────────────────────────────────
from dash import callback, Output, Input
from database.db import get_db
from database.models import Student, Course, Session, Attendance, Grade
from sqlalchemy import func


@callback(
    Output("kpi-row", "children"),
    Output("dashboard-data-store", "data"),
    Input("dashboard-interval", "n_intervals"),
    Input("btn-refresh-dashboard", "n_clicks"),
    prevent_initial_call=False,
)
def update_kpis(n_intervals, n_clicks):
    """Charge et affiche les KPIs du dashboard."""
    try:
        with get_db() as db:
            nb_students = db.query(func.count(Student.id)).filter(Student.is_active == True).scalar() or 0
            nb_courses  = db.query(func.count(Course.id)).filter(Course.is_active == True).scalar() or 0
            nb_sessions = db.query(func.count(Session.id)).scalar() or 0
            nb_absences = db.query(func.count(Attendance.id)).filter(Attendance.is_absent == True).scalar() or 0
            nb_att_total= db.query(func.count(Attendance.id)).scalar() or 1
            avg_grade   = db.query(func.avg(Grade.grade)).scalar()

        absence_rate = round((nb_absences / nb_att_total) * 100, 1) if nb_att_total > 0 else 0
        avg_grade_str = f"{avg_grade:.1f}/20" if avg_grade else "—"

        kpis = [
            {"label": "Étudiants Actifs",   "value": nb_students,    "icon": "fa-user-graduate",     "color": "blue",   "trend": None},
            {"label": "Cours Actifs",        "value": nb_courses,     "icon": "fa-book-open",         "color": "info",   "trend": None},
            {"label": "Séances Réalisées",   "value": nb_sessions,    "icon": "fa-chalkboard-user",   "color": "green",  "trend": None},
            {"label": "Taux d'Absentéisme",  "value": f"{absence_rate}%", "icon": "fa-user-xmark",   "color": "orange", "trend": None},
        ]

        cards = []
        for kpi in kpis:
            cards.append(
                html.Div(
                    className="kpi-card",
                    children=[
                        html.Div(
                            html.I(className=f"fa-solid {kpi['icon']}"),
                            className=f"kpi-icon {kpi['color']}",
                        ),
                        html.Div(
                            className="kpi-info",
                            children=[
                                html.Div(str(kpi["value"]), className="kpi-value"),
                                html.Div(kpi["label"],      className="kpi-label"),
                            ],
                        ),
                    ],
                )
            )

        store_data = {
            "nb_students": nb_students,
            "nb_courses": nb_courses,
            "avg_grade": float(avg_grade) if avg_grade else None,
        }
        return cards, store_data

    except Exception as e:
        error_card = html.Div(
            [html.I(className="fa-solid fa-triangle-exclamation"),
             f" Erreur de chargement : {str(e)}"],
            className="alert alert-danger",
        )
        return [error_card], {}


@callback(
    Output("chart-grades-distribution", "figure"),
    Input("dashboard-data-store", "data"),
)
def update_grades_chart(store_data):
    """Histogramme de distribution des notes."""
    try:
        with get_db() as db:
            grades = db.query(Grade.grade).all()
        values = [g[0] for g in grades if g[0] is not None]
    except Exception:
        values = []

    if not values:
        fig = go.Figure()
        fig.add_annotation(text="Aucune note disponible",
                           xref="paper", yref="paper", x=0.5, y=0.5,
                           showarrow=False, font=dict(color="#9ca3af", size=13))
    else:
        fig = px.histogram(
            x=values, nbins=10,
            color_discrete_sequence=["#1a237e"],
            labels={"x": "Note /20", "y": "Nombre d'étudiants"},
        )

    fig.update_layout(
        margin=dict(l=10, r=10, t=10, b=30),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="DM Sans", size=11, color="#6b7280"),
        xaxis=dict(showgrid=False, title="Note /20"),
        yaxis=dict(showgrid=True, gridcolor="#f1f5f9", title="Nb étudiants"),
        showlegend=False,
    )
    return fig


@callback(
    Output("chart-courses-progress", "figure"),
    Input("dashboard-data-store", "data"),
)
def update_courses_chart(store_data):
    """Barres de progression des cours."""
    try:
        with get_db() as db:
            courses = db.query(Course).filter(Course.is_active == True).all()
            labels = [c.code for c in courses]
            progress = [c.progress_percent for c in courses]
    except Exception:
        labels, progress = [], []

    if not labels:
        fig = go.Figure()
        fig.add_annotation(text="Aucun cours disponible",
                           xref="paper", yref="paper", x=0.5, y=0.5,
                           showarrow=False, font=dict(color="#9ca3af", size=13))
    else:
        colors = ["#2e7d32" if p >= 80 else "#1a237e" if p >= 40 else "#f57f17"
                  for p in progress]
        fig = go.Figure(go.Bar(
            x=labels, y=progress,
            marker_color=colors,
            text=[f"{p}%" for p in progress],
            textposition="outside",
        ))

    fig.update_layout(
        margin=dict(l=10, r=10, t=20, b=30),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="DM Sans", size=11, color="#6b7280"),
        yaxis=dict(range=[0, 110], showgrid=True, gridcolor="#f1f5f9", title="%"),
        xaxis=dict(showgrid=False),
        showlegend=False,
    )
    return fig


@callback(
    Output("chart-attendance-rate", "figure"),
    Input("dashboard-data-store", "data"),
)
def update_attendance_chart(store_data):
    """Graphique donut du taux de présence global."""
    try:
        with get_db() as db:
            total   = db.query(func.count(Attendance.id)).scalar() or 0
            absents = db.query(func.count(Attendance.id)).filter(Attendance.is_absent == True).scalar() or 0
        presents = total - absents
    except Exception:
        total, absents, presents = 0, 0, 0

    if total == 0:
        fig = go.Figure()
        fig.add_annotation(text="Aucune donnée de présence",
                           xref="paper", yref="paper", x=0.5, y=0.5,
                           showarrow=False, font=dict(color="#9ca3af", size=13))
    else:
        fig = go.Figure(go.Pie(
            labels=["Présents", "Absents"],
            values=[presents, absents],
            hole=0.6,
            marker_colors=["#2e7d32", "#e53935"],
            textinfo="percent",
            hovertemplate="%{label}: %{value} (%{percent})<extra></extra>",
        ))
        fig.add_annotation(
            text=f"{round(presents/total*100)}%<br><span style='font-size:10px'>Présence</span>",
            x=0.5, y=0.5, showarrow=False,
            font=dict(size=16, color="#1c1c2e", family="DM Sans"),
        )

    fig.update_layout(
        margin=dict(l=10, r=10, t=10, b=10),
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(family="DM Sans", size=11),
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=-0.15, x=0.5, xanchor="center"),
    )
    return fig


@callback(
    Output("recent-activity-list", "children"),
    Input("dashboard-data-store", "data"),
)
def update_recent_activity(store_data):
    """Liste des séances récentes."""
    try:
        with get_db() as db:
            sessions = (
                db.query(Session)
                .order_by(Session.date.desc())
                .limit(6)
                .all()
            )
            items = []
            for s in sessions:
                course_code = s.course.code if s.course else "—"
                items.append(
                    html.Div(
                        style={"display": "flex", "alignItems": "center", "gap": "12px",
                               "padding": "10px 0", "borderBottom": "1px solid #f1f5f9"},
                        children=[
                            html.Div(
                                html.I(className="fa-solid fa-chalkboard-user"),
                                style={"width": "34px", "height": "34px",
                                       "background": "#e8eaf6", "color": "#1a237e",
                                       "borderRadius": "8px", "display": "flex",
                                       "alignItems": "center", "justifyContent": "center",
                                       "fontSize": "0.85rem", "flexShrink": "0"},
                            ),
                            html.Div(
                                [
                                    html.Div(f"{course_code} — {s.topic or 'Séance'}",
                                             style={"fontWeight": "500", "fontSize": "0.87rem"}),
                                    html.Div(
                                        [html.I(className="fa-regular fa-calendar",
                                                style={"marginRight": "4px"}),
                                         str(s.date)],
                                        style={"fontSize": "0.77rem", "color": "#9ca3af",
                                               "marginTop": "2px"},
                                    ),
                                ],
                            ),
                            html.Div(
                                f"{s.duration}h",
                                style={"marginLeft": "auto", "fontSize": "0.8rem",
                                       "color": "#6b7280", "flexShrink": "0"},
                            ),
                        ],
                    )
                )
            return items if items else html.P("Aucune séance enregistrée.",
                                              style={"color": "#9ca3af", "fontSize": "0.87rem",
                                                     "padding": "16px 0"})
    except Exception as e:
        return html.Div(f"Erreur : {e}", className="alert alert-danger")
