"""
components/charts.py — Composants graphiques Plotly réutilisables
Fonctions standardisées pour tout le SGA.
"""

import plotly.graph_objects as go
import plotly.express as px

COLORS = {
    "primary":   "#1a237e",
    "secondary": "#283593",
    "accent":    "#e53935",
    "success":   "#2e7d32",
    "warning":   "#f57f17",
    "muted":     "#9ca3af",
    "border":    "#f1f5f9",
}
PALETTE = px.colors.qualitative.Plotly


def base_layout(xlabel="", ylabel="", height=300, legend=True):
    return dict(
        margin=dict(l=10, r=10, t=10, b=40),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="DM Sans", size=11, color="#6b7280"),
        xaxis=dict(showgrid=False, title=xlabel, zeroline=False),
        yaxis=dict(showgrid=True, gridcolor=COLORS["border"],
                   title=ylabel, zeroline=False),
        showlegend=legend,
        legend=dict(orientation="h", yanchor="bottom", y=1.02,
                    xanchor="right", x=1, font=dict(size=10)),
        height=height,
    )


def empty_figure(message="Aucune donnée disponible"):
    fig = go.Figure()
    fig.add_annotation(text=message, xref="paper", yref="paper",
                       x=0.5, y=0.5, showarrow=False,
                       font=dict(color=COLORS["muted"], size=13, family="DM Sans"))
    fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                      margin=dict(l=10, r=10, t=10, b=10),
                      xaxis=dict(visible=False), yaxis=dict(visible=False))
    return fig


def histogram_grades(values, bins=15):
    if not values:
        return empty_figure("Aucune note disponible")
    avg = sum(values) / len(values)
    fig = go.Figure()
    fig.add_trace(go.Histogram(x=values, nbinsx=bins,
        marker_color=COLORS["primary"], marker_line_color="white",
        marker_line_width=0.8, opacity=0.85, name="Notes",
        hovertemplate="Note : %{x}<br>Nb : %{y}<extra></extra>"))
    fig.add_vline(x=avg, line_dash="dash", line_color=COLORS["accent"], line_width=1.5,
                  annotation_text=f"Moy. {avg:.1f}", annotation_position="top right",
                  annotation_font=dict(size=10, color=COLORS["accent"]))
    fig.add_vline(x=10, line_dash="dot", line_color=COLORS["warning"], line_width=1,
                  annotation_text="Seuil 10", annotation_position="top left",
                  annotation_font=dict(size=10, color=COLORS["warning"]))
    fig.update_layout(**base_layout(xlabel="Note /20", ylabel="Nb étudiants"))
    return fig


def boxplot_by_course(course_grades_dict):
    if not course_grades_dict:
        return empty_figure("Aucune note par cours")
    fig = go.Figure()
    for i, (code, grades) in enumerate(course_grades_dict.items()):
        if grades:
            fig.add_trace(go.Box(y=grades, name=code,
                marker_color=PALETTE[i % len(PALETTE)],
                boxmean=True, jitter=0.3, pointpos=-1.8,
                hovertemplate=f"{code}<br>Note : %{{y:.1f}}<extra></extra>"))
    fig.update_layout(**base_layout(xlabel="Cours", ylabel="Note /20"))
    return fig


def bar_progress(labels, planned, completed):
    if not labels:
        return empty_figure("Aucun cours")
    fig = go.Figure()
    fig.add_trace(go.Bar(name="Prévu", x=labels, y=planned,
        marker_color="#e8eaf6", marker_line_color=COLORS["primary"],
        marker_line_width=1.5, hovertemplate="%{x}<br>Prévu : %{y}h<extra></extra>"))
    fig.add_trace(go.Bar(name="Réalisé", x=labels, y=completed,
        marker_color=COLORS["primary"],
        hovertemplate="%{x}<br>Réalisé : %{y}h<extra></extra>"))
    fig.update_layout(barmode="overlay",
                      **base_layout(xlabel="Cours", ylabel="Heures"))
    return fig


def donut_attendance(presents, absents):
    total = presents + absents
    if total == 0:
        return empty_figure("Aucune donnée de présence")
    rate = round(presents / total * 100)
    fig = go.Figure(go.Pie(
        labels=["Présents", "Absents"], values=[presents, absents],
        hole=0.62, marker_colors=[COLORS["success"], COLORS["accent"]],
        textinfo="percent",
        hovertemplate="%{label} : %{value} (%{percent})<extra></extra>",
        pull=[0, 0.04]))
    fig.add_annotation(text=f"<b>{rate}%</b>", x=0.5, y=0.5, showarrow=False,
                       font=dict(size=18, color="#1c1c2e", family="DM Sans"))
    fig.update_layout(margin=dict(l=10, r=10, t=10, b=10),
                      paper_bgcolor="rgba(0,0,0,0)",
                      font=dict(family="DM Sans", size=11), showlegend=True,
                      legend=dict(orientation="h", y=-0.1, x=0.5, xanchor="center"),
                      height=280)
    return fig


def line_chart_trends(data_by_course):
    if not data_by_course:
        return empty_figure("Aucune donnée temporelle")
    fig = go.Figure()
    for i, (code, points) in enumerate(data_by_course.items()):
        if not points: continue
        pts = sorted(points, key=lambda x: x[0])
        fig.add_trace(go.Scatter(
            x=[p[0] for p in pts], y=[p[1] for p in pts],
            mode="lines+markers", name=code,
            line=dict(color=PALETTE[i % len(PALETTE)], width=2.5),
            marker=dict(size=7),
            hovertemplate=f"{code}<br>%{{x}}<br>%{{y:.1f}}<extra></extra>"))
    fig.update_layout(**base_layout(xlabel="Date", ylabel="Note /20", height=380))
    return fig


def bar_ranking(names, values, threshold=10):
    if not names:
        return empty_figure("Aucun étudiant")
    colors = [COLORS["success"] if v >= threshold else COLORS["accent"] for v in values]
    fig = go.Figure(go.Bar(x=values, y=names, orientation="h",
        marker_color=colors, text=[f"{v:.1f}" for v in values],
        textposition="outside",
        hovertemplate="%{y}<br>Moy. : %{x:.1f}/20<extra></extra>"))
    if threshold:
        fig.add_vline(x=threshold, line_dash="dash",
                      line_color=COLORS["warning"], line_width=1)
    layout = base_layout(xlabel="Moyenne /20", height=340, legend=False)
    layout["yaxis"] = dict(autorange="reversed", showgrid=False)
    fig.update_layout(**layout)
    return fig


def pie_mentions(mention_counts):
    labels = [k for k, v in mention_counts.items() if v > 0]
    vals   = [v for v in mention_counts.values() if v > 0]
    if not vals:
        return empty_figure("Aucune mention")
    colors_map = {"Très Bien": COLORS["primary"], "Bien": COLORS["success"],
                  "Assez Bien": "#0277bd", "Passable": COLORS["warning"],
                  "Insuffisant": COLORS["accent"]}
    fig = go.Figure(go.Pie(labels=labels, values=vals, hole=0.5,
        marker_colors=[colors_map.get(l, COLORS["muted"]) for l in labels],
        textinfo="percent+label",
        hovertemplate="%{label} : %{value} étudiant(s)<extra></extra>"))
    fig.update_layout(margin=dict(l=10, r=10, t=10, b=10),
                      paper_bgcolor="rgba(0,0,0,0)",
                      font=dict(family="DM Sans", size=11),
                      showlegend=False, height=340)
    return fig


def bar_absences(labels, rates, threshold=20):
    if not labels:
        return empty_figure("Aucune donnée")
    colors = [COLORS["accent"] if r > threshold else
              COLORS["warning"] if r > 10 else COLORS["success"] for r in rates]
    fig = go.Figure(go.Bar(x=labels, y=rates, marker_color=colors,
        text=[f"{r}%" for r in rates], textposition="outside",
        hovertemplate="%{x}<br>Absent : %{y:.1f}%<extra></extra>"))
    if threshold:
        fig.add_hline(y=threshold, line_dash="dash", line_color=COLORS["accent"],
                      annotation_text=f"Seuil {threshold}%")
    fig.update_layout(**base_layout(xlabel="Cours", ylabel="Taux d'absence (%)"))
    return fig
