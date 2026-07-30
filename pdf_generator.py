import io
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

def generate_pdf_report(user_data, progress_data, badges_data, ai_summary=None):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36
    )

    styles = getSampleStyleSheet()

    # Custom styles
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=24,
        leading=28,
        textColor=colors.HexColor('#1E1B4B'),
        alignment=1, # Center
        spaceAfter=6
    )
    subtitle_style = ParagraphStyle(
        'DocSubTitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=12,
        leading=16,
        textColor=colors.HexColor('#4338CA'),
        alignment=1,
        spaceAfter=15
    )
    section_heading = ParagraphStyle(
        'SectionHeading',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=14,
        leading=18,
        textColor=colors.HexColor('#312E81'),
        spaceBefore=12,
        spaceAfter=6
    )
    body_style = ParagraphStyle(
        'BodyTextCustom',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10,
        leading=14,
        textColor=colors.HexColor('#1F2937')
    )

    elements = []

    # Title & Header Banner
    elements.append(Paragraph("🎓 AI Arithmetic Tutor", title_style))
    elements.append(Paragraph("Student Academic Performance & AI Analytics Report", subtitle_style))
    elements.append(HRFlowable(width="100%", thickness=2, color=colors.HexColor('#6366F1'), spaceAfter=15))

    # Student Summary Box Table
    username = user_data.get('username', 'Student')
    grade = user_data.get('grade_level', 'Grade 3')
    points = user_data.get('points', 0)
    streak = user_data.get('streak', 1)
    report_date = datetime.now().strftime("%B %d, %Y")

    user_info_data = [
        [
            Paragraph(f"<b>Student Name:</b> {username}", body_style),
            Paragraph(f"<b>Grade Level:</b> {grade}", body_style)
        ],
        [
            Paragraph(f"<b>Total XP Points:</b> {points} ⭐", body_style),
            Paragraph(f"<b>Practice Streak:</b> {streak} Days 🔥", body_style)
        ],
        [
            Paragraph(f"<b>Report Date:</b> {report_date}", body_style),
            Paragraph(f"<b>Status:</b> Active Learner 🚀", body_style)
        ]
    ]

    info_table = Table(user_info_data, colWidths=[270, 270])
    info_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#EEF2FF')),
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor('#C7D2FE')),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('PADDING', (0,0), (-1,-1), 8),
        ('BOTTOMPADDING', (0,0), (-1,-1), 8),
    ]))
    elements.append(info_table)
    elements.append(Spacer(1, 15))

    # Operation Performance Table
    elements.append(Paragraph("📊 Arithmetic Operation Mastery", section_heading))
    
    table_headers = ["Operation", "Attempted", "Correct", "Accuracy", "Mastery Level"]
    table_rows = [[Paragraph(f"<b>{h}</b>", body_style) for h in table_headers]]

    total_att = 0
    total_corr = 0

    for item in progress_data:
        op = item.get('operation', 'Unknown')
        att = item.get('total_attempted', 0)
        corr = item.get('correct_count', 0)
        total_att += att
        total_corr += corr
        acc = f"{(corr/att*100):.1f}%" if att > 0 else "0%"
        lvl = item.get('mastery_level', 1)
        lvl_stars = "★" * lvl + "☆" * (5 - lvl)

        table_rows.append([
            Paragraph(op, body_style),
            Paragraph(str(att), body_style),
            Paragraph(str(corr), body_style),
            Paragraph(acc, body_style),
            Paragraph(f"Lvl {lvl} ({lvl_stars})", body_style)
        ])

    overall_acc = f"{(total_corr/total_att*100):.1f}%" if total_att > 0 else "0%"
    table_rows.append([
        Paragraph("<b>Overall Total</b>", body_style),
        Paragraph(f"<b>{total_att}</b>", body_style),
        Paragraph(f"<b>{total_corr}</b>", body_style),
        Paragraph(f"<b>{overall_acc}</b>", body_style),
        Paragraph("<b>--</b>", body_style)
    ])

    perf_table = Table(table_rows, colWidths=[110, 80, 80, 90, 180])
    perf_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#4338CA')),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#E0E7FF')),
        ('ROWBACKGROUNDS', (0,1), (-1,-2), [colors.white, colors.HexColor('#F8FAFC')]),
        ('BACKGROUND', (0,-1), (-1,-1), colors.HexColor('#E0E7FF')),
        ('PADDING', (0,0), (-1,-1), 6),
    ]))
    elements.append(perf_table)
    elements.append(Spacer(1, 15))

    # Achievements / Badges Section
    elements.append(Paragraph("🏆 Achievement Badges Unlocked", section_heading))
    if badges_data:
        badge_text = ", ".join([f"{b.get('icon', '🏅')} {b.get('title', 'Badge')}" for b in badges_data])
        elements.append(Paragraph(badge_text, body_style))
    else:
        elements.append(Paragraph("No badges unlocked yet. Keep practicing!", body_style))
    
    elements.append(Spacer(1, 15))

    # AI Tutor Evaluation & Teacher Notes
    elements.append(Paragraph("🧠 AI Tutor Pedagogical Insights & Recommendations", section_heading))
    eval_text = (
        ai_summary or 
        f"The student <b>{username}</b> has solved a total of <b>{total_att}</b> practice questions with an overall accuracy of <b>{overall_acc}</b>. "
        f"They demonstrate solid consistency in fundamental arithmetic. "
        f"<b>Recommendation:</b> Focus on timed mixed quizzes and division regrouping exercises to unlock Level 4 & 5 mastery!"
    )
    
    eval_box = Table([[Paragraph(eval_text, body_style)]], colWidths=[540])
    eval_box.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#FEF3C7')),
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor('#F59E0B')),
        ('PADDING', (0,0), (-1,-1), 10),
    ]))
    elements.append(eval_box)
    
    elements.append(Spacer(1, 20))
    elements.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#CBD5E1'), spaceAfter=10))
    elements.append(Paragraph("Generated automatically by AI Arithmetic Tutor Mobile Application • Confidential Educational Document", ParagraphStyle('Foot', parent=styles['Normal'], fontSize=8, leading=10, textColor=colors.gray, alignment=1)))

    doc.build(elements)
    buffer.seek(0)
    return buffer.getvalue()
