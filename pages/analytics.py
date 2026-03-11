"""
pages/analytics.py — Module Analyses & Rapports
- Distribution des notes (histogramme + boîte à moustaches)
- Évolution des moyennes dans le temps
- Rapport de présence global et par cours
- Export PDF : bulletins et rapports de présence
"""

from dash import html, dcc, callback, Output, Input, State, no_update
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime

from database.db import get_db
from database.models import Student, Course, Grade, Session, Attendance
from components.tables import empty_state
from sqlalchemy import case, func


# ═══════════════════════════════════════════════════════════════════════════════
# LAYOUT DISTRIBUTION DES NOTES
# ═══════════════════════════════════════════════════════════════════════════════
def layout_grades():
    return html.Div(
        className="fade-in",
        children=[
            html.Div(className="page-header", children=[
                html.Div([
                    html.H1("Distribution des Notes", className="page-title"),
                    html.P("Analyse statistique des résultats académiques",
                           className="page-subtitle"),
                ], className="page-header-left"),
                html.Div(className="page-header-actions", children=[
                    dcc.Link([html.I(className="fa-solid fa-chart-line"), " Évolution"],
                             href="/analytics/trends",
                             className="btn btn-outline btn-sm"),
                    html.Button(
                        [html.I(className="fa-solid fa-file-pdf"), " Exporter PDF"],
                        id="btn-export-bulletin-pdf",
                        className="btn btn-primary btn-sm",
                        n_clicks=0,
                    ),
                    dcc.Download(id="download-bulletin-pdf"),
                ]),
            ]),

            html.Div(id="analytics-grades-feedback"),

            # ── Filtres ───────────────────────────────────────────────
            html.Div(className="card mb-24", children=[
                html.Div(className="card-body", children=[
                    html.Div(className="grid-2", children=[
                        html.Div([
                            html.Label([html.I(className="fa-solid fa-book-open",
                                               style={"marginRight": "5px"}), "Cours"],
                                       className="form-label"),
                            dcc.Dropdown(id="analytics-filter-course",
                                         placeholder="Tous les cours", clearable=True),
                        ], className="form-group"),
                        html.Div([
                            html.Label([html.I(className="fa-solid fa-user-graduate",
                                               style={"marginRight": "5px"}),
                                        "Étudiant (pour export bulletin)"],
                                       className="form-label"),
                            dcc.Dropdown(id="analytics-filter-student",
                                         placeholder="Sélectionner un étudiant",
                                         clearable=True),
                        ], className="form-group"),
                    ]),
                ]),
            ]),

            # ── KPIs statistiques ──────────────────────────────────────
            html.Div(id="analytics-stats-kpis", className="grid-4 mb-24"),

            # ── Graphiques ────────────────────────────────────────────
            html.Div(className="grid-2 mb-24", children=[
                html.Div(className="chart-container", children=[
                    html.Div([html.I(className="fa-solid fa-chart-bar"),
                              " Distribution des Notes"],
                             className="chart-title"),
                    dcc.Graph(id="chart-histogram",
                              config={"displayModeBar": True,
                                      "modeBarButtonsToRemove": ["lasso2d", "select2d"]},
                              style={"height": "320px"}),
                ]),
                html.Div(className="chart-container", children=[
                    html.Div([html.I(className="fa-solid fa-chart-simple"),
                              " Boîte à Moustaches par Cours"],
                             className="chart-title"),
                    dcc.Graph(id="chart-boxplot",
                              config={"displayModeBar": True,
                                      "modeBarButtonsToRemove": ["lasso2d", "select2d"]},
                              style={"height": "320px"}),
                ]),
            ]),

            # ── Tableau récapitulatif par cours ───────────────────────
            html.Div(className="table-container", children=[
                html.Div(className="table-header", children=[
                    html.Div([html.I(className="fa-solid fa-table"),
                              " Statistiques par Cours"],
                             className="table-title"),
                ]),
                html.Div(id="analytics-stats-table", style={"padding": "0"}),
            ]),

            dcc.Interval(id="analytics-interval", interval=60_000, n_intervals=0),
            dcc.Store(id="analytics-grades-store"),
        ],
    )


# ═══════════════════════════════════════════════════════════════════════════════
# LAYOUT ÉVOLUTION DES MOYENNES
# ═══════════════════════════════════════════════════════════════════════════════
def layout_trends():
    return html.Div(
        className="fade-in",
        children=[
            html.Div(className="page-header", children=[
                html.Div([
                    html.H1("Évolution des Moyennes", className="page-title"),
                    html.P("Tendances académiques dans le temps",
                           className="page-subtitle"),
                ], className="page-header-left"),
                html.Div([
                    dcc.Link([html.I(className="fa-solid fa-chart-bar"), " Distribution"],
                             href="/analytics/grades",
                             className="btn btn-outline btn-sm"),
                ], className="page-header-actions"),
            ]),

            # ── Filtre cours ──────────────────────────────────────────
            html.Div(className="card mb-24", children=[
                html.Div(className="card-body", children=[
                    html.Div([
                        html.Label([html.I(className="fa-solid fa-book-open",
                                           style={"marginRight": "5px"}), "Cours"],
                                   className="form-label"),
                        dcc.Dropdown(id="trends-filter-course",
                                     placeholder="Tous les cours",
                                     multi=True, clearable=True),
                    ], className="form-group"),
                ]),
            ]),

            # ── Graphiques évolution ──────────────────────────────────
            html.Div(className="chart-container mb-24", children=[
                html.Div([html.I(className="fa-solid fa-chart-line"),
                          " Évolution des Moyennes par Cours"],
                         className="chart-title"),
                dcc.Graph(id="chart-trends-line",
                          config={"displayModeBar": True},
                          style={"height": "380px"}),
            ]),

            html.Div(className="grid-2", children=[
                html.Div(className="chart-container", children=[
                    html.Div([html.I(className="fa-solid fa-ranking-star"),
                              " Classement des Étudiants"],
                             className="chart-title"),
                    dcc.Graph(id="chart-student-ranking",
                              config={"displayModeBar": False},
                              style={"height": "340px"}),
                ]),
                html.Div(className="chart-container", children=[
                    html.Div([html.I(className="fa-solid fa-chart-pie"),
                              " Répartition par Mention"],
                             className="chart-title"),
                    dcc.Graph(id="chart-mentions-pie",
                              config={"displayModeBar": False},
                              style={"height": "340px"}),
                ]),
            ]),

            dcc.Interval(id="trends-interval", interval=60_000, n_intervals=0),
        ],
    )


# ═══════════════════════════════════════════════════════════════════════════════
# LAYOUT RAPPORT DE PRÉSENCE
# ═══════════════════════════════════════════════════════════════════════════════
def layout_attendance():
    return html.Div(
        className="fade-in",
        children=[
            html.Div(className="page-header", children=[
                html.Div([
                    html.H1("Analyse des Présences", className="page-title"),
                    html.P("Absentéisme et assiduité par cours et étudiant",
                           className="page-subtitle"),
                ], className="page-header-left"),
                html.Div(className="page-header-actions", children=[
                    html.Button(
                        [html.I(className="fa-solid fa-file-pdf"), " Rapport PDF"],
                        id="btn-export-attendance-pdf",
                        className="btn btn-primary btn-sm",
                        n_clicks=0,
                    ),
                    dcc.Download(id="download-attendance-pdf"),
                ]),
            ]),

            html.Div(id="attendance-analytics-feedback"),

            # Filtre cours pour export
            html.Div(className="card mb-24", children=[
                html.Div(className="card-body", children=[
                    html.Div([
                        html.Label([html.I(className="fa-solid fa-book-open",
                                           style={"marginRight": "5px"}),
                                    "Cours (pour export PDF)"],
                                   className="form-label"),
                        dcc.Dropdown(id="attendance-analytics-course",
                                     placeholder="Sélectionner un cours", clearable=True),
                    ], className="form-group"),
                ]),
            ]),

            # KPIs présence globale
            html.Div(id="attendance-analytics-kpis", className="grid-4 mb-24"),

            # Graphiques
            html.Div(className="grid-2 mb-24", children=[
                html.Div(className="chart-container", children=[
                    html.Div([html.I(className="fa-solid fa-chart-bar"),
                              " Absences par Cours"],
                             className="chart-title"),
                    dcc.Graph(id="chart-absences-by-course",
                              config={"displayModeBar": False},
                              style={"height": "300px"}),
                ]),
                html.Div(className="chart-container", children=[
                    html.Div([html.I(className="fa-solid fa-user-xmark"),
                              " Top Absentéisme Étudiants"],
                             className="chart-title"),
                    dcc.Graph(id="chart-absences-by-student",
                              config={"displayModeBar": False},
                              style={"height": "300px"}),
                ]),
            ]),

            dcc.Interval(id="att-analytics-interval", interval=60_000, n_intervals=0),
        ],
    )


# ═══════════════════════════════════════════════════════════════════════════════
# CALLBACKS — Distribution des Notes
# ═══════════════════════════════════════════════════════════════════════════════

@callback(
    Output("analytics-filter-course",  "options"),
    Output("analytics-filter-student", "options"),
    Input("analytics-interval",        "n_intervals"),
)
def load_grades_options(n):
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
    Output("trends-filter-course", "options"),
    Input("trends-interval",       "n_intervals"),
)
def load_trends_options(n):
    try:
        with get_db() as db:
            courses = db.query(Course).filter(Course.is_active == True).all()
        return [{"label": f"{c.code} — {c.label}", "value": c.id} for c in courses]
    except Exception:
        return []


@callback(
    Output("attendance-analytics-course", "options"),
    Input("att-analytics-interval",       "n_intervals"),
)
def load_attendance_options(n):
    try:
        with get_db() as db:
            courses = db.query(Course).filter(Course.is_active == True).all()
        return [{"label": f"{c.code} — {c.label}", "value": c.id} for c in courses]
    except Exception:
        return []


@callback(
    Output("analytics-stats-kpis",  "children"),
    Output("chart-histogram",        "figure"),
    Output("chart-boxplot",          "figure"),
    Output("analytics-stats-table",  "children"),
    Output("analytics-grades-store", "data"),
    Input("analytics-interval",      "n_intervals"),
    Input("analytics-filter-course", "value"),
)
def update_grades_analytics(n, course_id):
    try:
        with get_db() as db:
            q = db.query(Grade)
            if course_id:
                q = q.filter(Grade.course_id == course_id)
            grades = q.all()

            # Données par cours pour le boxplot
            courses = db.query(Course).filter(Course.is_active == True).all()
            course_grades = {}
            for c in courses:
                cg = db.query(Grade.grade).filter(Grade.course_id == c.id).all()
                if cg:
                    course_grades[c.code] = [g[0] for g in cg]

        values = [g.grade for g in grades if g.grade is not None]

        if not values:
            empty_fig = _empty_fig("Aucune note disponible")
            return [], empty_fig, empty_fig, \
                   empty_state("fa-star", "Aucune note", "Ajoutez des notes pour voir les statistiques."), \
                   {}

        # ── Statistiques ──────────────────────────────────────────────
        avg  = sum(values) / len(values)
        mn   = min(values)
        mx   = max(values)
        vals_sorted = sorted(values)
        med  = vals_sorted[len(vals_sorted) // 2]
        above_10 = sum(1 for v in values if v >= 10)
        rate_10  = round(above_10 / len(values) * 100, 1)

        kpis = [
            _stat_kpi("fa-calculator",   "Moyenne",       f"{avg:.2f}/20",   "#1a237e"),
            _stat_kpi("fa-arrow-up",     "Note Max",      f"{mx:.1f}/20",    "#2e7d32"),
            _stat_kpi("fa-arrow-down",   "Note Min",      f"{mn:.1f}/20",    "#e53935"),
            _stat_kpi("fa-circle-check", "Taux Réussite", f"{rate_10}%",
                      "#2e7d32" if rate_10 >= 50 else "#e53935"),
        ]

        # ── Histogramme ───────────────────────────────────────────────
        fig_hist = go.Figure()
        fig_hist.add_trace(go.Histogram(
            x=values, nbinsx=20,
            marker_color="#1a237e",
            marker_line_color="white",
            marker_line_width=0.5,
            opacity=0.85,
            name="Notes",
        ))
        # Ligne moyenne
        fig_hist.add_vline(x=avg, line_dash="dash", line_color="#e53935",
                           annotation_text=f"Moy: {avg:.1f}",
                           annotation_position="top right")
        fig_hist.add_vline(x=10, line_dash="dot", line_color="#f57f17",
                           annotation_text="Seuil 10",
                           annotation_position="top left")
        fig_hist.update_layout(**_chart_layout("Notes /20", "Nb étudiants"))

        # ── Boxplot ───────────────────────────────────────────────────
        fig_box = go.Figure()
        colors = px.colors.qualitative.Set3
        for i, (code, gvals) in enumerate(course_grades.items()):
            fig_box.add_trace(go.Box(
                y=gvals, name=code,
                marker_color=colors[i % len(colors)],
                boxmean=True,
                jitter=0.3,
                pointpos=-1.8,
            ))
        fig_box.update_layout(**_chart_layout("Cours", "Note /20"))

        # ── Tableau stats par cours ───────────────────────────────────
        stats_rows = _build_stats_table(course_grades)

        return kpis, fig_hist, fig_box, stats_rows, {"updated": True}

    except Exception as e:
        err = html.Div(f"Erreur : {e}", className="alert alert-danger")
        return [], _empty_fig(), _empty_fig(), err, {}


# ── Export bulletin PDF ───────────────────────────────────────────────────────
@callback(
    Output("download-bulletin-pdf",       "data"),
    Output("analytics-grades-feedback",   "children"),
    Input("btn-export-bulletin-pdf",      "n_clicks"),
    State("analytics-filter-student",     "value"),
    prevent_initial_call=True,
)
def export_bulletin(n_clicks, student_id):
    if not student_id:
        return no_update, html.Div(
            [html.I(className="fa-solid fa-circle-exclamation"),
             " Sélectionnez un étudiant pour générer son bulletin."],
            className="alert alert-warning",
        )
    try:
        from utils.pdf_generator import generate_bulletin
        with get_db() as db:
            student = db.query(Student).filter(Student.id == student_id).first()
            if not student:
                return no_update, html.Div("Étudiant introuvable.",
                                           className="alert alert-danger")

            # Récupérer les notes par cours
            courses = db.query(Course).filter(Course.is_active == True).all()
            grades_by_course = []
            for c in courses:
                cg = db.query(Grade).filter(
                    Grade.student_id == student_id,
                    Grade.course_id  == c.id,
                ).all()
                if cg:
                    avg = sum(g.grade * g.coefficient for g in cg) / \
                          sum(g.coefficient for g in cg)
                    grades_by_course.append({
                        "course_code":  c.code,
                        "course_label": c.label,
                        "teacher":      c.teacher or "—",
                        "average":      avg,
                        "grades": [
                            {"label": g.label, "grade": g.grade,
                             "coefficient": g.coefficient}
                            for g in cg
                        ],
                    })

            # Assiduité
            nb_total = db.query(func.count(Attendance.id)).filter(
                Attendance.student_id == student_id
            ).scalar() or 0
            nb_abs = db.query(func.count(Attendance.id)).filter(
                Attendance.student_id == student_id,
                Attendance.is_absent  == True,
            ).scalar() or 0
            rate = round((nb_total - nb_abs) / nb_total * 100, 1) if nb_total > 0 else 100

        att_summary = {
            "total":         nb_total,
            "absences":      nb_abs,
            "presence_rate": rate,
        }

        pdf_bytes = generate_bulletin(
            student, grades_by_course, att_summary,
            academic_year=f"{datetime.now().year}-{datetime.now().year + 1}",
        )
        fname = f"bulletin_{student.last_name}_{student.first_name}.pdf"
        return dcc.send_bytes(pdf_bytes, fname), None

    except ImportError:
        return no_update, html.Div(
            [html.I(className="fa-solid fa-circle-xmark"),
             " ReportLab non installé. Exécutez : pip install reportlab"],
            className="alert alert-danger",
        )
    except Exception as e:
        return no_update, html.Div(
            [html.I(className="fa-solid fa-circle-xmark"), f" Erreur PDF : {str(e)}"],
            className="alert alert-danger",
        )


# ═══════════════════════════════════════════════════════════════════════════════
# CALLBACKS — Évolution des Moyennes
# ═══════════════════════════════════════════════════════════════════════════════

@callback(
    Output("chart-trends-line",     "figure"),
    Output("chart-student-ranking", "figure"),
    Output("chart-mentions-pie",    "figure"),
    Input("trends-interval",        "n_intervals"),
    Input("trends-filter-course",   "value"),
)
def update_trends(n, course_ids):
    try:
        with get_db() as db:
            # Moyennes des étudiants
            student_avgs = db.query(
                Student.id,
                Student.last_name,
                Student.first_name,
                func.avg(Grade.grade).label("avg"),
            ).join(Grade, Grade.student_id == Student.id)\
             .filter(Student.is_active == True)\
             .group_by(Student.id)\
             .order_by(func.avg(Grade.grade).desc())\
             .all()

            # Notes avec dates pour l'évolution
            q_grades = db.query(Grade.date, Grade.grade, Course.code)\
                         .join(Course, Course.id == Grade.course_id)
            if course_ids:
                q_grades = q_grades.filter(Grade.course_id.in_(course_ids))
            grades_dated = q_grades.filter(Grade.date != None)\
                                   .order_by(Grade.date).all()

        # ── Graphique évolution ────────────────────────────────────────
        fig_line = go.Figure()
        if grades_dated:
            from collections import defaultdict
            by_course = defaultdict(list)
            for g in grades_dated:
                by_course[g.code].append((str(g.date), g.grade))

            colors = px.colors.qualitative.Plotly
            for i, (code, pts) in enumerate(by_course.items()):
                pts_sorted = sorted(pts, key=lambda x: x[0])
                dates  = [p[0] for p in pts_sorted]
                grades_v = [p[1] for p in pts_sorted]
                fig_line.add_trace(go.Scatter(
                    x=dates, y=grades_v, mode="lines+markers",
                    name=code, line=dict(color=colors[i % len(colors)], width=2),
                    marker=dict(size=6),
                ))
        else:
            fig_line.add_annotation(text="Aucune donnée avec dates",
                                    xref="paper", yref="paper", x=0.5, y=0.5,
                                    showarrow=False, font=dict(color="#9ca3af"))
        fig_line.update_layout(**_chart_layout("Date", "Note /20"))

        # ── Classement étudiants ──────────────────────────────────────
        fig_rank = go.Figure()
        if student_avgs:
            top_n = student_avgs[:15]
            names  = [f"{s.first_name[0]}. {s.last_name}" for s in top_n]
            avgs_v = [round(float(s.avg), 2) for s in top_n]
            colors_r = ["#2e7d32" if a >= 10 else "#e53935" for a in avgs_v]
            fig_rank.add_trace(go.Bar(
                x=avgs_v, y=names, orientation="h",
                marker_color=colors_r,
                text=[f"{a:.1f}" for a in avgs_v],
                textposition="outside",
            ))
            fig_rank.add_vline(x=10, line_dash="dash", line_color="#f57f17")
        fig_rank.update_layout(**_chart_layout("Moyenne /20", "", height=340))
        fig_rank.update_yaxes(autorange="reversed")

        # ── Répartition mentions ──────────────────────────────────────
        fig_pie = go.Figure()
        if student_avgs:
            mention_counts = {"Très Bien": 0, "Bien": 0,
                              "Assez Bien": 0, "Passable": 0, "Insuffisant": 0}
            for s in student_avgs:
                avg = float(s.avg) if s.avg else 0
                m = ("Très Bien" if avg >= 16 else "Bien" if avg >= 14 else
                     "Assez Bien" if avg >= 12 else "Passable" if avg >= 10
                     else "Insuffisant")
                mention_counts[m] += 1

            labels = [k for k, v in mention_counts.items() if v > 0]
            vals   = [v for v in mention_counts.values() if v > 0]
            ment_colors = {
                "Très Bien": "#1a237e", "Bien": "#2e7d32",
                "Assez Bien": "#0277bd", "Passable": "#f57f17",
                "Insuffisant": "#e53935",
            }
            fig_pie.add_trace(go.Pie(
                labels=labels, values=vals, hole=0.5,
                marker_colors=[ment_colors.get(l, "#9ca3af") for l in labels],
                textinfo="percent+label",
                hovertemplate="%{label}: %{value} étudiant(s)<extra></extra>",
            ))
        fig_pie.update_layout(
            margin=dict(l=10, r=10, t=10, b=10),
            paper_bgcolor="rgba(0,0,0,0)",
            font=dict(family="DM Sans", size=11),
            showlegend=False,
        )

        return fig_line, fig_rank, fig_pie

    except Exception as e:
        ef = _empty_fig(str(e))
        return ef, ef, ef


# ═══════════════════════════════════════════════════════════════════════════════
# CALLBACKS — Analyse Présences
# ═══════════════════════════════════════════════════════════════════════════════

@callback(
    Output("attendance-analytics-kpis",     "children"),
    Output("chart-absences-by-course",      "figure"),
    Output("chart-absences-by-student",     "figure"),
    Input("att-analytics-interval",         "n_intervals"),
)
def update_attendance_analytics(n):
    try:
        with get_db() as db:
            total_att  = db.query(func.count(Attendance.id)).scalar() or 0
            total_abs  = db.query(func.count(Attendance.id)).filter(
                Attendance.is_absent == True).scalar() or 0
            total_sessions = db.query(func.count(Session.id)).scalar() or 0
            total_pres = total_att - total_abs
            rate_g     = round(total_pres / total_att * 100, 1) if total_att > 0 else 100

            # Absences par cours
            abs_by_course = db.query(
                Course.code,
                func.count(Attendance.id).label("total"),
                func.sum(
                    case((Attendance.is_absent == True, 1), else_=0)
                ).label("absences"),
            ).join(Session,    Session.course_id   == Course.id)\
             .join(Attendance, Attendance.session_id == Session.id)\
             .group_by(Course.id).all()

            # Top absents étudiants
            abs_by_student = db.query(
                Student.last_name,
                Student.first_name,
                func.count(Attendance.id).label("abs"),
            ).join(Attendance, Attendance.student_id == Student.id)\
             .filter(Attendance.is_absent == True)\
             .group_by(Student.id)\
             .order_by(func.count(Attendance.id).desc())\
             .limit(10).all()

        # KPIs
        kpis = [
            _stat_kpi("fa-users",       "Présences totales",    str(total_pres),  "#2e7d32"),
            _stat_kpi("fa-user-xmark",  "Absences totales",     str(total_abs),   "#e53935"),
            _stat_kpi("fa-chart-pie",   "Taux de présence",     f"{rate_g}%",
                      "#2e7d32" if rate_g >= 75 else "#f57f17"),
            _stat_kpi("fa-calendar",    "Séances enregistrées",
                      str(total_sessions), "#1a237e"),
        ]

        # Chart absences par cours
        fig_course = go.Figure()
        if abs_by_course:
            codes   = [r.code for r in abs_by_course]
            abs_v   = [int(r.absences or 0) for r in abs_by_course]
            total_v = [int(r.total or 0) for r in abs_by_course]
            rates_v = [round(a / t * 100, 1) if t > 0 else 0
                       for a, t in zip(abs_v, total_v)]
            colors  = ["#e53935" if r > 25 else "#f57f17" if r > 15 else "#2e7d32"
                       for r in rates_v]
            fig_course.add_trace(go.Bar(
                x=codes, y=rates_v, marker_color=colors,
                text=[f"{r}%" for r in rates_v], textposition="outside",
            ))
            fig_course.add_hline(y=20, line_dash="dash", line_color="#e53935",
                                  annotation_text="Seuil 20%")
        fig_course.update_layout(**_chart_layout("Cours", "Taux d'absence (%)"))

        # Chart top absentéisme étudiants
        fig_student = go.Figure()
        if abs_by_student:
            names  = [f"{s.first_name[0]}. {s.last_name}" for s in abs_by_student]
            abs_sv = [s.abs for s in abs_by_student]
            fig_student.add_trace(go.Bar(
                x=abs_sv, y=names, orientation="h",
                marker_color="#e53935",
                text=abs_sv, textposition="outside",
            ))
        fig_student.update_layout(**_chart_layout("Nb absences", ""))
        fig_student.update_yaxes(autorange="reversed")

        return kpis, fig_course, fig_student

    except Exception as e:
        ef = _empty_fig(str(e))
        return [], ef, ef


# Export rapport présence PDF
@callback(
    Output("download-attendance-pdf",         "data"),
    Output("attendance-analytics-feedback",   "children"),
    Input("btn-export-attendance-pdf",        "n_clicks"),
    State("attendance-analytics-course",      "value"),
    prevent_initial_call=True,
)
def export_attendance_report(n_clicks, course_id):
    if not course_id:
        return no_update, html.Div(
            [html.I(className="fa-solid fa-circle-exclamation"),
             " Sélectionnez un cours pour générer le rapport."],
            className="alert alert-warning",
        )
    try:
        from utils.pdf_generator import generate_attendance_report
        with get_db() as db:
            course = db.query(Course).filter(Course.id == course_id).first()
            if not course:
                return no_update, html.Div("Cours introuvable.",
                                           className="alert alert-danger")
            sessions = db.query(Session)\
                         .filter(Session.course_id == course_id)\
                         .order_by(Session.date).all()

            sessions_data = []
            for s in sessions:
                atts = db.query(Attendance)\
                         .filter(Attendance.session_id == s.id).all()
                sessions_data.append({
                    "date":     str(s.date),
                    "topic":    s.topic or "Séance",
                    "duration": s.duration,
                    "attendances": [
                        {
                            "student_name": att.student.full_name if att.student else "—",
                            "is_absent":    att.is_absent,
                        }
                        for att in atts
                    ],
                })

        pdf_bytes = generate_attendance_report(course, sessions_data)
        fname = f"rapport_presence_{course.code}.pdf"
        return dcc.send_bytes(pdf_bytes, fname), None

    except ImportError:
        return no_update, html.Div(
            [html.I(className="fa-solid fa-circle-xmark"),
             " ReportLab non installé. Exécutez : pip install reportlab"],
            className="alert alert-danger",
        )
    except Exception as e:
        return no_update, html.Div(
            [html.I(className="fa-solid fa-circle-xmark"), f" Erreur PDF : {str(e)}"],
            className="alert alert-danger",
        )


# ═══════════════════════════════════════════════════════════════════════════════
# HELPERS
# ═══════════════════════════════════════════════════════════════════════════════

def _stat_kpi(icon, label, value, color):
    return html.Div(className="kpi-card", children=[
        html.Div(html.I(className=f"fa-solid {icon}"),
                 style={"width": "44px", "height": "44px",
                        "background": f"{color}18", "color": color,
                        "borderRadius": "10px", "display": "flex",
                        "alignItems": "center", "justifyContent": "center",
                        "fontSize": "1.15rem", "flexShrink": "0"}),
        html.Div([
            html.Div(value, className="kpi-value", style={"color": color}),
            html.Div(label, className="kpi-label"),
        ], className="kpi-info"),
    ])


def _chart_layout(xlabel="", ylabel="", height=320):
    return dict(
        margin=dict(l=10, r=20, t=20, b=40),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="DM Sans", size=11, color="#6b7280"),
        xaxis=dict(showgrid=False, title=xlabel),
        yaxis=dict(showgrid=True, gridcolor="#f1f5f9", title=ylabel),
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        height=height,
    )


def _empty_fig(msg="Aucune donnée"):
    fig = go.Figure()
    fig.add_annotation(text=msg, xref="paper", yref="paper",
                       x=0.5, y=0.5, showarrow=False,
                       font=dict(color="#9ca3af", size=13))
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=10, r=10, t=10, b=10),
    )
    return fig


def _build_stats_table(course_grades):
    if not course_grades:
        return empty_state("fa-table", "Aucune statistique",
                           "Ajoutez des notes pour voir les statistiques.")

    header = html.Div(
        style={"display": "grid",
               "gridTemplateColumns": "80px 1fr 80px 80px 80px 100px 80px",
               "gap": "12px", "padding": "10px 20px",
               "background": "#f8fafc", "borderBottom": "1px solid #e2e8f0"},
        children=[
            *[html.Span(t, style={"fontSize": "0.75rem", "fontWeight": "700",
                                   "textTransform": "uppercase", "color": "#6b7280",
                                   "letterSpacing": "0.05em",
                                   "textAlign": "center" if i > 0 else "left"})
              for i, t in enumerate(["Cours", "Intitulé", "Nb notes",
                                      "Moy.", "Min", "Max", "Réussite"])],
        ],
    )

    rows = []
    for code, vals in course_grades.items():
        if not vals:
            continue
        avg_v  = round(sum(vals) / len(vals), 2)
        mn_v   = min(vals)
        mx_v   = max(vals)
        rate_v = round(sum(1 for v in vals if v >= 10) / len(vals) * 100, 1)
        avg_c  = "#2e7d32" if avg_v >= 10 else "#e53935"

        rows.append(html.Div(
            className="table-row-hover",
            style={"display": "grid",
                   "gridTemplateColumns": "80px 1fr 80px 80px 80px 100px 80px",
                   "gap": "12px", "padding": "12px 20px",
                   "borderBottom": "1px solid #f1f5f9", "alignItems": "center"},
            children=[
                html.Span(code, style={"fontFamily": "monospace", "fontWeight": "700",
                                        "fontSize": "0.8rem", "color": "#1a237e",
                                        "background": "#e8eaf6", "padding": "2px 7px",
                                        "borderRadius": "5px"}),
                html.Span("—", style={"fontSize": "0.85rem", "color": "#6b7280"}),
                *[html.Span(str(v), style={"textAlign": "center", "fontSize": "0.87rem",
                                            "color": c if c else "#1c1c2e",
                                            "fontWeight": "600" if c else "400"})
                  for v, c in [
                      (len(vals), None),
                      (f"{avg_v:.1f}", avg_c),
                      (f"{mn_v:.1f}", None),
                      (f"{mx_v:.1f}", None),
                      (f"{rate_v}%", "#2e7d32" if rate_v >= 50 else "#e53935"),
                  ]],
            ],
        ))

    return html.Div([header] + rows)
