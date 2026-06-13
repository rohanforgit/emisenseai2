import io
import re
from datetime import datetime
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, PageBreak
)
from reportlab.lib.units import inch
import charts

def generate_pdf_report(loan_data, base_details, sim_emi, sim_annual, sim_lump, combined_sim, refinance, health_score, health_status, score_deductions, alerts, ai_recommendations):
    """
    Generates a professional PDF report containing baseline stats, health metrics, 
    comparison of prepayments, static charts, and AI advisor notes.
    """
    buffer = io.BytesIO()
    
    # 0.5 inch margins (36 points) for a modern, content-dense look
    doc = SimpleDocTemplate(
        buffer, 
        pagesize=letter,
        leftMargin=36,
        rightMargin=36,
        topMargin=36,
        bottomMargin=36
    )
    
    styles = getSampleStyleSheet()
    
    # Professional, high-contrast color scheme for print
    primary_blue = colors.HexColor('#1E3A8A')  # Classic navy for header styling
    slate_border = colors.HexColor('#CBD5E1')
    bg_light_row = colors.HexColor('#F8FAFC')
    danger_red = colors.HexColor('#DC2626')
    warning_orange = colors.HexColor('#D97706')
    info_blue = colors.HexColor('#2563EB')
    
    # Typography Styles
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=22,
        textColor=primary_blue,
        spaceAfter=2,
        alignment=0
    )
    
    subtitle_style = ParagraphStyle(
        'DocSubTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Oblique',
        fontSize=11,
        textColor=colors.HexColor('#475569'),
        spaceAfter=12,
        alignment=0
    )
    
    h1_style = ParagraphStyle(
        'SectionHeading',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=13,
        textColor=colors.white,
        spaceBefore=12,
        spaceAfter=6,
        backColor=primary_blue,
        borderPadding=5,
        borderRadius=3
    )
    
    body_style = ParagraphStyle(
        'BodyTextDark',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9.5,
        textColor=colors.HexColor('#1E293B'),
        spaceBefore=3,
        spaceAfter=3
    )
    
    body_bold = ParagraphStyle(
        'BodyBoldText',
        parent=body_style,
        fontName='Helvetica-Bold'
    )
    
    story = []
    
    # --- REPORT HEADER ---
    story.append(Paragraph("EMI Sense AI", title_style))
    story.append(Paragraph("Financial Report & Custom Loan Optimization Plan", subtitle_style))
    story.append(Paragraph(f"Generated On: {datetime.now().strftime('%d %B %Y, %I:%M %p')}", body_style))
    story.append(Spacer(1, 10))
    
    # --- GENERAL EXECUTIVE SUMMARY ---
    currency = loan_data.get("currency", "₹")
    loan_type = loan_data.get("loan_type", "Custom Loan")
    
    summary_text = (
        f"This advisory report is prepared specifically for your <b>{loan_type}</b>. "
        f"Using standard mathematical compound interest modeling combined with strategic prepayment paths, "
        f"the report details how you can minimize interest, optimize cash flows, and accelerate your debt-free target."
    )
    story.append(Paragraph(summary_text, body_style))
    story.append(Spacer(1, 10))
    
    # --- BASELINE VS OPTIMIZED LOAN SUMMARY TABLE ---
    story.append(Paragraph("1. Loan Structure & Optimization Comparison", h1_style))
    
    total_interest_opt = sum(m["interest"] for m in combined_sim)
    total_savings_opt = base_details["total_interest"] - total_interest_opt
    years_saved_opt = (base_details["actual_tenure_months"] - len(combined_sim)) / 12.0
    
    summary_table_data = [
        [
            Paragraph("<b>Core Parameter</b>", body_bold), 
            Paragraph("<b>Baseline Loan</b>", body_bold), 
            Paragraph("<b>Optimized Strategy</b>", body_bold), 
            Paragraph("<b>Expected Savings</b>", body_bold)
        ],
        ["Loan Type", loan_type, "Combined Plan", "-"],
        ["Principal Borrowed", f"{currency}{loan_data['loan_amount']:,.2f}", f"{currency}{loan_data['loan_amount']:,.2f}", "-"],
        ["Annual Rate", f"{loan_data['interest_rate']}%", f"{loan_data['interest_rate']}%", "-"],
        ["Monthly EMI", f"{currency}{base_details['emi']:,.2f}", f"{currency}{(base_details['emi'] + loan_data.get('extra_monthly_budget', 0.0)):,.2f}", f"Extra budget: {currency}{loan_data.get('extra_monthly_budget', 0.0):,.2f}/mo"],
        ["Total Interest", f"{currency}{base_details['total_interest']:,.2f}", f"{currency}{total_interest_opt:,.2f}", f"Saved: {currency}{total_savings_opt:,.2f}"],
        ["Total Payment", f"{currency}{base_details['total_payment']:,.2f}", f"{currency}{(loan_data['loan_amount'] + total_interest_opt):,.2f}", f"Saved: {currency}{total_savings_opt:,.2f}"],
        ["Loan Tenure", f"{base_details['actual_tenure_months']} months", f"{len(combined_sim)} months", f"Saved: {years_saved_opt:.1f} years"]
    ]
    
    t1 = Table(summary_table_data, colWidths=[2.1*inch, 1.6*inch, 1.8*inch, 1.9*inch])
    t1.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#E2E8F0')),
        ('GRID', (0,0), (-1,-1), 0.5, slate_border),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BACKGROUND', (0,1), (-1,-1), bg_light_row),
    ]))
    story.append(t1)
    story.append(Spacer(1, 10))
    
    # --- FINANCIAL HEALTH & SECURITY MATRIX ---
    story.append(Paragraph("2. Financial Health Score & Risk Flags", h1_style))
    
    health_text = (
        f"Your custom <b>Loan Health Score is {health_score}/100</b>, placing you in the <b>{health_status}</b> tier.<br/>"
        f"Your Debt Ratio (EMI to Income) is <b>{loan_data['emi_ratio']}%</b>. A healthy target is typically under 30%."
    )
    story.append(Paragraph(health_text, body_style))
    story.append(Spacer(1, 6))
    
    if alerts:
        alert_rows = [[Paragraph("<b>Severity</b>", body_bold), Paragraph("<b>Warning / Opportunity Alert Description</b>", body_bold)]]
        for a in alerts:
            sev = a["type"].upper()
            sev_color = danger_red if sev == "DANGER" else warning_orange if sev == "WARNING" else info_blue
            alert_rows.append([
                Paragraph(f"<font color='{sev_color}'><b>{sev}</b></font>", body_bold),
                Paragraph(a["message"], body_style)
            ])
            
        t_alerts = Table(alert_rows, colWidths=[1.1*inch, 6.3*inch])
        t_alerts.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#FEE2E2')),
            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#FECDD3')),
            ('ALIGN', (0,0), (-1,-1), 'LEFT'),
            ('BOTTOMPADDING', (0,0), (-1,-1), 4),
            ('TOPPADDING', (0,0), (-1,-1), 4),
            ('BACKGROUND', (0,1), (-1,-1), colors.HexColor('#FFF5F5')),
        ]))
        story.append(t_alerts)
        story.append(Spacer(1, 10))
        
    story.append(PageBreak())  # Align visual charts to the top of page 2
    
    # --- STATIC CHARTS SECTION ---
    story.append(Paragraph("3. Visual Amortization & Portfolio Balance Timelines", h1_style))
    
    pie_bytes = charts.generate_static_pie_chart(loan_data['loan_amount'], base_details['total_interest'])
    timeline_bytes = charts.generate_static_timeline_chart(base_details['schedule'], combined_sim)
    
    img_pie = Image(io.BytesIO(pie_bytes), width=3.3*inch, height=2.1*inch)
    img_time = Image(io.BytesIO(timeline_bytes), width=4.0*inch, height=2.1*inch)
    
    chart_layout_table = Table([[img_pie, img_time]], colWidths=[3.4*inch, 4.0*inch])
    chart_layout_table.setStyle(TableStyle([
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('LEFTPADDING', (0,0), (-1,-1), 0),
        ('RIGHTPADDING', (0,0), (-1,-1), 0),
    ]))
    story.append(chart_layout_table)
    story.append(Spacer(1, 10))
    
    # --- OPTIMIZATION SIMULATION COMPARISONS TABLE ---
    story.append(Paragraph("4. Breakdown of Prepayment Scenarios", h1_style))
    
    opt_table_data = [
        [
            Paragraph("<b>Scenario Run</b>", body_bold),
            Paragraph("<b>New EMI</b>", body_bold),
            Paragraph("<b>Tenure (Months)</b>", body_bold),
            Paragraph("<b>Interest Saved</b>", body_bold),
            Paragraph("<b>Years Saved</b>", body_bold)
        ],
        [
            "Baseline Plan", 
            f"{currency}{base_details['emi']:,.2f}", 
            f"{base_details['actual_tenure_months']}", 
            "-", 
            "-"
        ],
        [
            f"EMI Increase (+{loan_data.get('emi_increase_pct', 10)}%)", 
            f"{currency}{sim_emi['new_emi']:,.2f}", 
            f"{sim_emi['new_tenure_months']}", 
            f"{currency}{sim_emi['interest_saved']:,.2f}", 
            f"{sim_emi['years_saved']} yrs"
        ],
        [
            "Annual Prepayment Schedule", 
            f"{currency}{base_details['emi']:,.2f}", 
            f"{sim_annual['new_tenure_months']}", 
            f"{currency}{sim_annual['interest_saved']:,.2f}", 
            f"{sim_annual['years_saved']} yrs"
        ],
        [
            "Lump Sum Prepayment", 
            f"{currency}{sim_lump['new_emi']:,.2f}", 
            f"{sim_lump['new_tenure_months']}", 
            f"{currency}{sim_lump['interest_saved']:,.2f}", 
            f"{sim_lump['years_saved']} yrs"
        ],
        [
            "Combined Strategy (All Options)",
            f"{currency}{(base_details['emi'] + loan_data.get('extra_monthly_budget', 0.0)):,.2f}",
            f"{len(combined_sim)}",
            f"{currency}{total_savings_opt:,.2f}",
            f"{years_saved_opt:.1f} yrs"
        ]
    ]
    
    t_opt = Table(opt_table_data, colWidths=[2.2*inch, 1.2*inch, 1.2*inch, 1.5*inch, 1.3*inch])
    t_opt.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#F1F5F9')),
        ('GRID', (0,0), (-1,-1), 0.5, slate_border),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BACKGROUND', (0,1), (-1,-2), bg_light_row),
        ('BACKGROUND', (0,-1), (-1,-1), colors.HexColor('#FEF08A')),  # Highlight optimized row in yellow
    ]))
    story.append(t_opt)
    story.append(Spacer(1, 10))
    
    # --- REFINANCING ASSESSMENTS ---
    if refinance:
        story.append(Paragraph("5. Balance Transfer & Refinance Assessment", h1_style))
        ref_status = "RECOMMENDED" if refinance["worth_refinancing"] else "NOT RECOMMENDED"
        ref_color = colors.HexColor('#16A34A') if refinance["worth_refinancing"] else danger_red
        
        ref_text = (
            f"Refinance target simulation set at interest rate <b>{loan_data.get('refinance_rate', 0.0)}%</b> with closing/transfer fees of <b>{currency}{loan_data.get('refinance_cost', 0):,.2f}</b>:<br/>"
            f"Transfer Decision: <b><font color='{ref_color}'>{ref_status}</font></b><br/>"
            f"Monthly EMI reduction: <b>{currency}{refinance['monthly_saving']:,.2f}</b><br/>"
            f"Gross interest savings over tenure: <b>{currency}{refinance['gross_interest_saved']:,.2f}</b><br/>"
            f"Net financial savings (after transfer fees): <b>{currency}{refinance['net_savings']:,.2f}</b><br/>"
            f"Break-even timeline: <b>{refinance['break_even_months']} months</b>"
        )
        story.append(Paragraph(ref_text, body_style))
        story.append(Spacer(1, 10))
        
    story.append(PageBreak())
    
    # --- AI ADVISOR RECOMMENDATIONS & ACTIONS ---
    story.append(Paragraph("6. AI Recommendations & Strategic Action Plan", h1_style))
    
    # Escape XML characters for ReportLab compatibility
    clean_ai = ai_recommendations.replace("&", "&amp;")
    
    # Convert markdown patterns to HTML tags supported by ReportLab Paragraphs
    clean_ai = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', clean_ai)
    clean_ai = re.sub(r'### (.*?)(?:\n|$)', r'<b>\1</b><br/>', clean_ai)
    clean_ai = re.sub(r'## (.*?)(?:\n|$)', r'<b>\1</b><br/>', clean_ai)
    
    # Swap out complex emojis that standard PDF fonts can't render
    emoji_swap = {
        "💡": "*", "🏆": "*", "✅": "*", "🚨": "*", "⚠️": "*",
        "🥇": "1.", "🥈": "2.", "🥉": "3.", "💵": "INR", "📊": "Analysis:"
    }
    for emo, rep in emoji_swap.items():
        clean_ai = clean_ai.replace(emo, rep)
        
    clean_ai = clean_ai.replace("\n", "<br/>")
    
    story.append(Paragraph(clean_ai, body_style))
    story.append(Spacer(1, 15))
    
    # --- DISCLAIMERS ---
    disclaimer_style = ParagraphStyle(
        'DisclaimerStyle',
        parent=styles['Normal'],
        fontName='Helvetica-Oblique',
        fontSize=7.5,
        textColor=colors.HexColor('#64748B'),
        alignment=1
    )
    story.append(Spacer(1, 5))
    story.append(Paragraph("Disclaimer: This financial optimization report is constructed using mathematical compound amortization models and AI logic. It is generated for educational and advisory purposes and does not constitute certified legal or financial investment planning. Consult a professional advisor before executing prepayments or balance transfers.", disclaimer_style))
    
    # Build the document template
    doc.build(story)
    
    pdf_contents = buffer.getvalue()
    buffer.close()
    return pdf_contents
