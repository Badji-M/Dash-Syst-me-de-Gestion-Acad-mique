"""
utils/pdf_generator.py — Génération de documents PDF académiques
- Bulletin de notes individuel
- Rapport de présence par cours / étudiant
Utilise ReportLab pour un rendu professionnel et institutionnel.
"""

import io
from datetime import datetime

try:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import cm, mm
    from reportlab.lib.colors import (
        HexColor, white, black, Color
    )
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
    from reportlab.platypus import (
        SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
        HRFlowable, KeepTogether
    )
    from reportlab.platypus.flowables import HRFlowable
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False

from config import SCHOOL_NAME, SCHOOL_ADDRESS


# ─── Palette institutionnelle ─────────────────────────────────────────────────
C_PRIMARY    = HexColor("#1A237E") if REPORTLAB_AVAILABLE else None
C_SECONDARY  = HexColor("#283593") if REPORTLAB_AVAILABLE else None
C_ACCENT     = HexColor("#E53935") if REPORTLAB_AVAILABLE else None
C_LIGHT      = HexColor("#E8EAF6") if REPORTLAB_AVAILABLE else None
C_SUCCESS    = HexColor("#2E7D32") if REPORTLAB_AVAILABLE else None
C_DANGER     = HexColor("#C62828") if REPORTLAB_AVAILABLE else None
C_MUTED      = HexColor("#757575") if REPORTLAB_AVAILABLE else None
C_BORDER     = HexColor("#E0E0E0") if REPORTLAB_AVAILABLE else None
C_BG_ROW     = HexColor("#F5F6FA") if REPORTLAB_AVAILABLE else None


def _check_reportlab():
    if not REPORTLAB_AVAILABLE:
        raise ImportError(
            "ReportLab est requis pour générer des PDF. "
            "Installez-le avec : pip install reportlab"
        )


# ═══════════════════════════════════════════════════════════════════════════════
# BULLETIN DE NOTES
# ═══════════════════════════════════════════════════════════════════════════════
def generate_bulletin(student, grades_by_course, attendance_summary,
                      academic_year="", supervisor=""):
    """
    Génère un bulletin de notes PDF officiel.

    Paramètres :
        student           : objet Student
        grades_by_course  : list de dicts {course_code, course_label,
                             teacher, grades: [{label, grade, coefficient}],
                             average}
        attendance_summary: dict {total, absences, presence_rate}
        academic_year     : str (ex: "2024-2025")
        supervisor        : str (nom du responsable pédagogique)

    Retourne : bytes (contenu PDF)
    """
    _check_reportlab()

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=1.8 * cm,
        leftMargin=1.8 * cm,
        topMargin=1.5 * cm,
        bottomMargin=1.8 * cm,
        title=f"Bulletin — {student.full_name}",
        author=SCHOOL_NAME,
    )

    styles = getSampleStyleSheet()
    story  = []

    # ── En-tête institutionnel ────────────────────────────────────────
    story.append(_build_header_table(academic_year))
    story.append(Spacer(1, 0.4 * cm))

    # ── Titre du document ──────────────────────────────────────────────
    story.append(Paragraph(
        "BULLETIN DE NOTES",
        ParagraphStyle("BulletinTitle",
                       fontSize=16, fontName="Helvetica-Bold",
                       textColor=C_PRIMARY, alignment=TA_CENTER,
                       spaceAfter=4),
    ))
    story.append(HRFlowable(width="100%", thickness=2,
                             color=C_PRIMARY, spaceAfter=0.3 * cm))

    # ── Informations étudiant ─────────────────────────────────────────
    story.append(_build_student_info_table(student))
    story.append(Spacer(1, 0.5 * cm))

    # ── Résultats académiques ─────────────────────────────────────────
    story.append(Paragraph(
        "RÉSULTATS ACADÉMIQUES",
        ParagraphStyle("SectionTitle", fontSize=10, fontName="Helvetica-Bold",
                       textColor=C_PRIMARY, spaceBefore=4, spaceAfter=6),
    ))

    # Tableau des notes
    story.append(_build_grades_table(grades_by_course))
    story.append(Spacer(1, 0.4 * cm))

    # ── Moyenne générale ──────────────────────────────────────────────
    all_grades  = [g for c in grades_by_course for g in c.get("grades", [])]
    if all_grades:
        total_w = sum(g["grade"] * g["coefficient"] for g in all_grades)
        total_c = sum(g["coefficient"] for g in all_grades)
        avg_gen = total_w / total_c if total_c > 0 else 0
    else:
        avg_gen = 0

    avg_color = C_SUCCESS if avg_gen >= 10 else C_DANGER
    mention   = _get_mention(avg_gen)

    avg_data = [
        ["MOYENNE GÉNÉRALE", f"{avg_gen:.2f} / 20", f"Mention : {mention}"],
    ]
    avg_table = Table(avg_data, colWidths=[7 * cm, 4 * cm, 6 * cm])
    avg_table.setStyle(TableStyle([
        ("BACKGROUND",  (0, 0), (-1, 0), C_PRIMARY),
        ("TEXTCOLOR",   (0, 0), (-1, 0), white),
        ("FONTNAME",    (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE",    (0, 0), (-1, 0), 10),
        ("ALIGN",       (0, 0), (0,  0), "LEFT"),
        ("ALIGN",       (1, 0), (1,  0), "CENTER"),
        ("ALIGN",       (2, 0), (2,  0), "CENTER"),
        ("ROWBACKGROUNDS", (0, 0), (-1, 0), [C_PRIMARY]),
        ("PADDING",     (0, 0), (-1, -1), 8),
        ("GRID",        (0, 0), (-1, -1), 0.5, white),
        ("ROUNDEDCORNERS", [4]),
    ]))
    story.append(avg_table)
    story.append(Spacer(1, 0.5 * cm))

    # ── Assiduité ─────────────────────────────────────────────────────
    story.append(Paragraph(
        "ASSIDUITÉ",
        ParagraphStyle("SectionTitle", fontSize=10, fontName="Helvetica-Bold",
                       textColor=C_PRIMARY, spaceBefore=4, spaceAfter=6),
    ))
    story.append(_build_attendance_table(attendance_summary))
    story.append(Spacer(1, 0.8 * cm))

    # ── Appréciations / Pied de page ──────────────────────────────────
    story.append(_build_footer_table(supervisor))

    doc.build(story, onFirstPage=_add_watermark, onLaterPages=_add_watermark)
    buffer.seek(0)
    return buffer.getvalue()


def _build_header_table(academic_year):
    """En-tête avec logo texte et infos de l'établissement."""
    data = [[
        Paragraph(
            f"<b>{SCHOOL_NAME.upper()}</b><br/>"
            f"<font size='8' color='#757575'>{SCHOOL_ADDRESS}</font>",
            ParagraphStyle("SchoolName", fontSize=11, fontName="Helvetica-Bold",
                           textColor=C_PRIMARY),
        ),
        Paragraph(
            f"<font size='8' color='#757575'>Année académique</font><br/>"
            f"<b>{academic_year or datetime.now().strftime('%Y-%Y')}</b><br/>"
            f"<font size='8' color='#757575'>Édité le {datetime.now().strftime('%d/%m/%Y')}</font>",
            ParagraphStyle("DateInfo", fontSize=9, alignment=TA_RIGHT),
        ),
    ]]
    t = Table(data, colWidths=[11 * cm, 6.5 * cm])
    t.setStyle(TableStyle([
        ("VALIGN",    (0, 0), (-1, -1), "MIDDLE"),
        ("LINEBELOW", (0, 0), (-1, 0), 1.5, C_PRIMARY),
        ("PADDING",   (0, 0), (-1, -1), 4),
    ]))
    return t


def _build_student_info_table(student):
    """Bloc d'informations sur l'étudiant."""
    bdate = str(student.birth_date) if student.birth_date else "—"
    data = [
        [
            Paragraph("<font color='#757575' size='8'>NOM ET PRÉNOM</font><br/>"
                      f"<b>{student.full_name.upper()}</b>",
                      ParagraphStyle("Info", fontSize=10)),
            Paragraph("<font color='#757575' size='8'>IDENTIFIANT</font><br/>"
                      f"<b>{student.id}</b>",
                      ParagraphStyle("Info", fontSize=10)),
            Paragraph("<font color='#757575' size='8'>DATE DE NAISSANCE</font><br/>"
                      f"<b>{bdate}</b>",
                      ParagraphStyle("Info", fontSize=10)),
            Paragraph("<font color='#757575' size='8'>EMAIL</font><br/>"
                      f"<b>{student.email}</b>",
                      ParagraphStyle("Info", fontSize=9)),
        ]
    ]
    t = Table(data, colWidths=[5.5 * cm, 2.5 * cm, 3.5 * cm, 6 * cm])
    t.setStyle(TableStyle([
        ("BACKGROUND",  (0, 0), (-1, 0), C_LIGHT),
        ("GRID",        (0, 0), (-1, -1), 0.5, C_BORDER),
        ("PADDING",     (0, 0), (-1, -1), 8),
        ("VALIGN",      (0, 0), (-1, -1), "MIDDLE"),
        ("ROUNDEDCORNERS", [4]),
    ]))
    return t


def _build_grades_table(grades_by_course):
    """Tableau détaillé des notes par matière."""
    header = ["Matière", "Enseignant", "Évaluation", "Note /20", "Coeff.", "Moy. Mat."]
    data   = [header]

    for course in grades_by_course:
        course_grades = course.get("grades", [])
        avg = course.get("average", 0)

        if not course_grades:
            data.append([
                course.get("course_code", "—"),
                course.get("teacher", "—"),
                "—", "—", "—",
                f"{avg:.2f}",
            ])
            continue

        for i, g in enumerate(course_grades):
            if i == 0:
                data.append([
                    Paragraph(f"<b>{course.get('course_code','')}</b><br/>"
                              f"<font size='7' color='#757575'>{course.get('course_label','')}</font>",
                              ParagraphStyle("CourseCell", fontSize=9)),
                    course.get("teacher", "—"),
                    g.get("label", "—"),
                    f"{g['grade']:.1f}",
                    f"× {g['coefficient']:.1f}",
                    Paragraph(
                        f"<b>{avg:.2f}</b>",
                        ParagraphStyle("AvgCell", fontSize=10, alignment=TA_CENTER,
                                       textColor=C_SUCCESS if avg >= 10 else C_DANGER),
                    ),
                ])
            else:
                data.append(["", "", g.get("label", "—"),
                             f"{g['grade']:.1f}", f"× {g['coefficient']:.1f}", ""])

    col_widths = [4.5 * cm, 3.5 * cm, 3.5 * cm, 2 * cm, 1.8 * cm, 2.2 * cm]
    t = Table(data, colWidths=col_widths, repeatRows=1)

    style = [
        # En-tête
        ("BACKGROUND",  (0, 0), (-1, 0), C_SECONDARY),
        ("TEXTCOLOR",   (0, 0), (-1, 0), white),
        ("FONTNAME",    (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE",    (0, 0), (-1, 0), 8),
        ("ALIGN",       (0, 0), (-1, 0), "CENTER"),
        # Corps
        ("FONTSIZE",    (0, 1), (-1, -1), 9),
        ("VALIGN",      (0, 0), (-1, -1), "MIDDLE"),
        ("ALIGN",       (3, 1), (5, -1), "CENTER"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [white, C_BG_ROW]),
        ("GRID",        (0, 0), (-1, -1), 0.3, C_BORDER),
        ("PADDING",     (0, 0), (-1, -1), 5),
        ("LINEBELOW",   (0, 0), (-1, 0), 1, C_PRIMARY),
    ]
    t.setStyle(TableStyle(style))
    return t


def _build_attendance_table(att):
    """Résumé de l'assiduité."""
    total    = att.get("total",    0)
    absences = att.get("absences", 0)
    rate     = att.get("presence_rate", 100)
    presents = total - absences

    data = [
        ["Séances totales", "Présences", "Absences", "Taux de présence"],
        [str(total), str(presents), str(absences), f"{rate:.1f} %"],
    ]
    t = Table(data, colWidths=[4.5 * cm, 4.5 * cm, 4.5 * cm, 4 * cm])
    t.setStyle(TableStyle([
        ("BACKGROUND",  (0, 0), (-1, 0), C_LIGHT),
        ("FONTNAME",    (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE",    (0, 0), (-1, 0), 8),
        ("TEXTCOLOR",   (0, 0), (-1, 0), C_PRIMARY),
        ("ALIGN",       (0, 0), (-1, -1), "CENTER"),
        ("FONTSIZE",    (0, 1), (-1, 1), 12),
        ("FONTNAME",    (0, 1), (-1, 1), "Helvetica-Bold"),
        ("TEXTCOLOR",   (2, 1), (2, 1), C_DANGER if absences > 0 else C_SUCCESS),
        ("TEXTCOLOR",   (3, 1), (3, 1), C_SUCCESS if rate >= 75 else C_DANGER),
        ("GRID",        (0, 0), (-1, -1), 0.5, C_BORDER),
        ("PADDING",     (0, 0), (-1, -1), 8),
    ]))
    return t


def _build_footer_table(supervisor):
    """Pied de page avec signatures."""
    today = datetime.now().strftime("%d/%m/%Y")
    data = [[
        Paragraph(
            f"<font size='8' color='#757575'>Responsable pédagogique</font><br/><br/>"
            f"<b>{supervisor or '________________________'}</b><br/>"
            f"<font size='7' color='#9ca3af'>Signature et cachet</font>",
            ParagraphStyle("SignL", fontSize=9),
        ),
        Paragraph(
            f"<font size='8' color='#757575'>Fait à</font><br/><br/>"
            f"<b>________________________</b><br/>"
            f"<font size='8' color='#9ca3af'>le {today}</font>",
            ParagraphStyle("SignR", fontSize=9, alignment=TA_CENTER),
        ),
        Paragraph(
            f"<font size='8' color='#757575'>Lu et approuvé par l'étudiant(e)</font><br/><br/>"
            f"<b>________________________</b><br/>"
            f"<font size='7' color='#9ca3af'>Signature</font>",
            ParagraphStyle("SignRR", fontSize=9, alignment=TA_RIGHT),
        ),
    ]]
    t = Table(data, colWidths=[6 * cm, 5 * cm, 6.5 * cm])
    t.setStyle(TableStyle([
        ("LINEABOVE",  (0, 0), (-1, 0), 0.5, C_BORDER),
        ("PADDING",    (0, 0), (-1, -1), 8),
        ("VALIGN",     (0, 0), (-1, -1), "TOP"),
    ]))
    return t


def _add_watermark(canvas, doc):
    """Ajoute un filigrane discret et un numéro de page."""
    canvas.saveState()
    # Numéro de page
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(C_MUTED)
    canvas.drawRightString(
        A4[0] - 1.5 * cm,
        0.8 * cm,
        f"Document officiel — {SCHOOL_NAME} — Page {doc.page}",
    )
    # Ligne de pied de page
    canvas.setStrokeColor(C_BORDER)
    canvas.setLineWidth(0.5)
    canvas.line(1.8 * cm, 1.2 * cm, A4[0] - 1.8 * cm, 1.2 * cm)
    canvas.restoreState()


def _get_mention(avg):
    if avg >= 16:   return "Très Bien"
    if avg >= 14:   return "Bien"
    if avg >= 12:   return "Assez Bien"
    if avg >= 10:   return "Passable"
    return "Insuffisant"


# ═══════════════════════════════════════════════════════════════════════════════
# RAPPORT DE PRÉSENCE
# ═══════════════════════════════════════════════════════════════════════════════
def generate_attendance_report(course, sessions_data, period=""):
    """
    Génère un rapport de présence par cours.

    Paramètres :
        course        : objet Course
        sessions_data : list de dicts {date, topic, duration,
                         attendances: [{student_name, is_absent}]}
        period        : str (ex: "Semestre 1")

    Retourne : bytes (contenu PDF)
    """
    _check_reportlab()

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=A4,
        rightMargin=1.8 * cm, leftMargin=1.8 * cm,
        topMargin=1.5 * cm,   bottomMargin=1.8 * cm,
        title=f"Rapport Présence — {course.code}",
        author=SCHOOL_NAME,
    )

    story = []

    # En-tête
    story.append(_build_header_table(period))
    story.append(Spacer(1, 0.4 * cm))

    story.append(Paragraph(
        "RAPPORT DE PRÉSENCE",
        ParagraphStyle("ReportTitle", fontSize=16, fontName="Helvetica-Bold",
                       textColor=C_PRIMARY, alignment=TA_CENTER, spaceAfter=4),
    ))
    story.append(HRFlowable(width="100%", thickness=2,
                             color=C_PRIMARY, spaceAfter=0.3 * cm))

    # Infos cours
    course_info = [
        [
            Paragraph(f"<font size='8' color='#757575'>COURS</font><br/><b>{course.code} — {course.label}</b>",
                      ParagraphStyle("CI", fontSize=10)),
            Paragraph(f"<font size='8' color='#757575'>ENSEIGNANT</font><br/><b>{course.teacher or '—'}</b>",
                      ParagraphStyle("CI", fontSize=10)),
            Paragraph(f"<font size='8' color='#757575'>VOLUME HORAIRE</font><br/><b>{course.total_hours}h prévues</b>",
                      ParagraphStyle("CI", fontSize=10)),
        ]
    ]
    t_info = Table(course_info, colWidths=[7 * cm, 5 * cm, 5.5 * cm])
    t_info.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), C_LIGHT),
        ("GRID",       (0, 0), (-1, -1), 0.5, C_BORDER),
        ("PADDING",    (0, 0), (-1, -1), 8),
        ("VALIGN",     (0, 0), (-1, -1), "MIDDLE"),
    ]))
    story.append(t_info)
    story.append(Spacer(1, 0.5 * cm))

    # Tableau de présences par séance
    if not sessions_data:
        story.append(Paragraph("Aucune séance enregistrée.",
                                ParagraphStyle("NoData", fontSize=10, textColor=C_MUTED)))
    else:
        for s in sessions_data:
            story.append(KeepTogether(_build_session_attendance_block(s)))
            story.append(Spacer(1, 0.3 * cm))

    doc.build(story, onFirstPage=_add_watermark, onLaterPages=_add_watermark)
    buffer.seek(0)
    return buffer.getvalue()


def _build_session_attendance_block(session_data):
    """Bloc de présence pour une séance."""
    elements = []

    # Titre séance
    elements.append(Paragraph(
        f"<b>Séance du {session_data['date']}</b> — "
        f"{session_data.get('topic','—')} ({session_data.get('duration','?')}h)",
        ParagraphStyle("SessionTitle", fontSize=9, fontName="Helvetica-Bold",
                       textColor=C_SECONDARY, spaceBefore=4, spaceAfter=4),
    ))

    attendances = session_data.get("attendances", [])
    if not attendances:
        elements.append(Paragraph("Aucun appel enregistré.",
                                   ParagraphStyle("No", fontSize=8, textColor=C_MUTED)))
        return elements

    # Tableau en grille compacte (4 colonnes)
    rows    = []
    row_buf = []
    for i, att in enumerate(attendances):
        status = "ABS" if att["is_absent"] else "P"
        color  = "#E53935" if att["is_absent"] else "#2E7D32"
        cell   = Paragraph(
            f"{att['student_name']}<br/>"
            f"<font color='{color}' size='8'><b>{status}</b></font>",
            ParagraphStyle("AttCell", fontSize=8, alignment=TA_CENTER),
        )
        row_buf.append(cell)
        if len(row_buf) == 4:
            rows.append(row_buf)
            row_buf = []
    if row_buf:
        while len(row_buf) < 4:
            row_buf.append("")
        rows.append(row_buf)

    t = Table(rows, colWidths=[4.5 * cm] * 4)
    t.setStyle(TableStyle([
        ("GRID",   (0, 0), (-1, -1), 0.3, C_BORDER),
        ("ROWBACKGROUNDS", (0, 0), (-1, -1), [white, C_BG_ROW]),
        ("PADDING",(0, 0), (-1, -1), 5),
        ("ALIGN",  (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]))
    elements.append(t)
    return elements
