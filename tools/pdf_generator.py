"""
PDF Report Generator for Smart Traffic Management System.
Generates formal city traffic, emergency corridor, and CO2 carbon footprint PDF summaries.
"""
import io
from datetime import datetime
from typing import List, Dict, Any

try:
    from reportlab.lib.pagesizes import letter
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib import colors
    REPORTLAB_AVAILABLE = True
except Exception:
    REPORTLAB_AVAILABLE = False


def generate_traffic_pdf_report(road_name: str, reports: List[Dict[str, Any]], analytics: List[Dict[str, Any]], alerts: List[Dict[str, Any]]) -> bytes:
    """
    Generates a formal PDF summary report for city traffic management.
    
    Args:
        road_name: Selected junction/road.
        reports: List of recent CrewAI reports.
        analytics: List of analytics records.
        alerts: List of system alerts.
        
    Returns:
        PDF file bytes suitable for Streamlit st.download_button.
    """
    if not REPORTLAB_AVAILABLE:
        # Fallback text if reportlab is missing
        text_content = f"AI Smart Traffic System Report for {road_name}\nGenerated at: {datetime.utcnow().isoformat()}\n"
        return text_content.encode('utf-8')

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

    # Custom Color Palette
    PRIMARY = colors.HexColor("#0284C7") # Sky Blue
    SECONDARY = colors.HexColor("#0F172A") # Dark Slate
    TEXT_DARK = colors.HexColor("#1E293B")
    ACCENT_RED = colors.HexColor("#EF4444")
    ACCENT_GREEN = colors.HexColor("#10B981")
    BG_LIGHT = colors.HexColor("#F8FAFC")

    # Custom Styles
    title_style = ParagraphStyle(
        'ReportTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=20,
        leading=24,
        textColor=PRIMARY,
        spaceAfter=4
    )

    subtitle_style = ParagraphStyle(
        'ReportSubTitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10,
        leading=13,
        textColor=colors.HexColor("#64748B"),
        spaceAfter=12
    )

    heading2_style = ParagraphStyle(
        'SectionHeading',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=13,
        leading=16,
        textColor=SECONDARY,
        spaceBefore=10,
        spaceAfter=6
    )

    body_style = ParagraphStyle(
        'BodyDark',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        leading=12,
        textColor=TEXT_DARK
    )

    table_header_style = ParagraphStyle(
        'TableHeader',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=9,
        leading=11,
        textColor=colors.white
    )

    story = []

    # 1. Header Title
    story.append(Paragraph("🚦 AI Smart Traffic Management System", title_style))
    story.append(Paragraph(f"Executive Traffic & Sustainability Report — <b>{road_name}</b> | Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}", subtitle_style))
    story.append(HRFlowable(width="100%", thickness=1.5, color=PRIMARY, spaceAfter=12))

    # 2. Executive KPI Overview Cards Table
    latest_analytics = analytics[0] if analytics else {}
    total_vehicles = latest_analytics.get("total_vehicles", 0)
    avg_speed = latest_analytics.get("average_speed", 0.0)
    congestion_idx = latest_analytics.get("congestion_index", 0.0)
    carbon_kg = latest_analytics.get("carbon_emission_kg", 0.0)
    perf_score = latest_analytics.get("road_performance_score", 0.0)

    kpi_data = [
        [
            Paragraph(f"<b>Monitored Vehicles</b><br/><font size=12 color='#0284C7'><b>{total_vehicles}</b></font>", body_style),
            Paragraph(f"<b>Average Speed</b><br/><font size=12 color='#8B5CF6'><b>{avg_speed} km/h</b></font>", body_style),
            Paragraph(f"<b>Congestion Index</b><br/><font size=12 color='#EC4899'><b>{congestion_idx} / 100</b></font>", body_style),
            Paragraph(f"<b>Carbon Footprint</b><br/><font size=12 color='#EF4444'><b>{carbon_kg} kg CO₂</b></font>", body_style),
            Paragraph(f"<b>Road Efficiency</b><br/><font size=12 color='#10B981'><b>{perf_score} / 100</b></font>", body_style),
        ]
    ]

    kpi_table = Table(kpi_data, colWidths=[105, 105, 110, 110, 110])
    kpi_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), BG_LIGHT),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor("#CBD5E1")),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
    ]))
    story.append(kpi_table)
    story.append(Spacer(1, 14))

    # 3. Emergency Corridors & System Alerts
    story.append(Paragraph("🚨 Recent Emergency Corridors & System Alerts", heading2_style))
    
    alert_rows = [[
        Paragraph("Timestamp", table_header_style),
        Paragraph("Severity", table_header_style),
        Paragraph("Alert Title", table_header_style),
        Paragraph("Road Name", table_header_style),
        Paragraph("Alternate Detour", table_header_style)
    ]]

    for a in alerts[:6]:
        sev_color = "#EF4444" if a.get("severity") in ["CRITICAL", "EMERGENCY"] else "#F59E0B"
        alert_rows.append([
            Paragraph(str(a.get("timestamp", ""))[:19].replace("T", " "), body_style),
            Paragraph(f"<font color='{sev_color}'><b>{a.get('severity')}</b></font>", body_style),
            Paragraph(str(a.get("title", "")), body_style),
            Paragraph(str(a.get("road_name", "")), body_style),
            Paragraph(str(a.get("alternate_route", "N/A")), body_style)
        ])

    if len(alert_rows) == 1:
        alert_rows.append([Paragraph("No active alerts logged.", body_style), Paragraph("-", body_style), Paragraph("-", body_style), Paragraph("-", body_style), Paragraph("-", body_style)])

    alert_table = Table(alert_rows, colWidths=[95, 65, 170, 100, 110])
    alert_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), SECONDARY),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, BG_LIGHT]),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
    ]))
    story.append(alert_table)
    story.append(Spacer(1, 14))

    # 4. Multi-Agent Decision Reports Summary
    story.append(Paragraph("🤖 CrewAI Multi-Agent Execution Log", heading2_style))

    report_rows = [[
        Paragraph("Timestamp", table_header_style),
        Paragraph("Density", table_header_style),
        Paragraph("Congestion Score", table_header_style),
        Paragraph("Signal Control Mode", table_header_style),
        Paragraph("Green Corridor", table_header_style)
    ]]

    for r in reports[:6]:
        g_corr = "🚨 ACTIVE" if r.get("green_corridor_active") else "🟢 Normal"
        report_rows.append([
            Paragraph(str(r.get("timestamp", ""))[:19].replace("T", " "), body_style),
            Paragraph(str(r.get("density")), body_style),
            Paragraph(f"{r.get('congestion_score', 0):.1f} / 100", body_style),
            Paragraph(str(r.get("signal_mode")), body_style),
            Paragraph(g_corr, body_style)
        ])

    report_table = Table(report_rows, colWidths=[100, 80, 100, 150, 110])
    report_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), PRIMARY),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, BG_LIGHT]),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
    ]))
    story.append(report_table)
    story.append(Spacer(1, 18))

    # 5. Footer & System Certification Stamp
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#94A3B8"), spaceAfter=8))
    footer_style = ParagraphStyle(
        'FooterText',
        parent=styles['Normal'],
        fontName='Helvetica-Oblique',
        fontSize=8,
        leading=10,
        textColor=colors.HexColor("#64748B"),
        alignment=1
    )
    story.append(Paragraph("Automated Report generated by CrewAI Multi-Agent Traffic System | Smart City Urban Mobility Division", footer_style))

    doc.build(story)
    pdf_bytes = buffer.getvalue()
    buffer.close()
    return pdf_bytes
