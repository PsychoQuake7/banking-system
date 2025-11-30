from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from django.http import HttpResponse
from io import BytesIO
from django.utils import timezone

def generate_financial_report_pdf(report_data, start_date, end_date):
    """
    Generate Financial Report PDF using ReportLab.
    """
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    elements = []
    styles = getSampleStyleSheet()
    
    # Title
    title = Paragraph("Kayamanan Banking System - Income Statement", styles['Title'])
    elements.append(title)
    
    # Date Range
    date_str = f"Period: {start_date or 'Beginning'} to {end_date or 'Today'}"
    elements.append(Paragraph(date_str, styles['Normal']))
    elements.append(Spacer(1, 0.25*inch))
    
    # Revenues
    elements.append(Paragraph("Revenues", styles['Heading2']))
    if report_data['revenues']:
        data = [['Account', 'Code', 'Amount']]
        for acc in report_data['revenues']:
            data.append([acc['name'], acc['code'], f"P {acc['balance']:,.2f}"])
        data.append(['Total Revenue', '', f"P {report_data['total_revenue']:,.2f}"])
        
        t = Table(data, colWidths=[4*inch, 1*inch, 1.5*inch])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('ALIGN', (-1, 0), (-1, -1), 'RIGHT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, -1), (-1, -1), colors.lightgrey),
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        elements.append(t)
    else:
        elements.append(Paragraph("No revenue recorded.", styles['Normal']))
        
    elements.append(Spacer(1, 0.25*inch))
    
    # Expenses
    elements.append(Paragraph("Expenses", styles['Heading2']))
    if report_data['expenses']:
        data = [['Account', 'Code', 'Amount']]
        for acc in report_data['expenses']:
            data.append([acc['name'], acc['code'], f"P {acc['balance']:,.2f}"])
        data.append(['Total Expenses', '', f"P {report_data['total_expenses']:,.2f}"])
        
        t = Table(data, colWidths=[4*inch, 1*inch, 1.5*inch])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('ALIGN', (-1, 0), (-1, -1), 'RIGHT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, -1), (-1, -1), colors.lightgrey),
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        elements.append(t)
    else:
        elements.append(Paragraph("No expenses recorded.", styles['Normal']))
        
    elements.append(Spacer(1, 0.5*inch))
    
    # Net Income
    net_income = report_data['net_income']
    color = colors.green if net_income >= 0 else colors.red
    ni_style = ParagraphStyle('NetIncome', parent=styles['Heading2'], textColor=color)
    elements.append(Paragraph(f"Net Income: P {net_income:,.2f}", ni_style))
    
    doc.build(elements)
    pdf = buffer.getvalue()
    buffer.close()
    
    response = HttpResponse(pdf, content_type='application/pdf')
    response['Content-Disposition'] = 'inline; filename="financial_report.pdf"'
    return response

def generate_loan_report_pdf(active_loans, delinquent_loans, recent_repayments):
    """
    Generate Loan Reports PDF using ReportLab.
    """
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=landscape(letter))
    elements = []
    styles = getSampleStyleSheet()
    
    # Title
    title = Paragraph(f"Kayamanan Banking System - Loan Reports ({timezone.now().date()})", styles['Title'])
    elements.append(title)
    elements.append(Spacer(1, 0.25*inch))
    
    # Active Loans
    elements.append(Paragraph(f"Active Loans ({active_loans.count()})", styles['Heading2']))
    if active_loans:
        data = [['Loan ID', 'Client', 'Start Date', 'Term', 'Amount', 'Balance']]
        for loan in active_loans:
            data.append([
                str(loan.loan_id),
                f"{loan.application.client.first_name} {loan.application.client.last_name}",
                str(loan.start_date),
                f"{loan.term_months} mos",
                f"P {loan.loan_amount:,.2f}",
                f"P {loan.remaining_balance:,.2f}"
            ])
            
        t = Table(data, colWidths=[1*inch, 2.5*inch, 1.5*inch, 1*inch, 1.5*inch, 1.5*inch])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.blue),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('ALIGN', (4, 0), (-1, -1), 'RIGHT'), # Amount columns right aligned
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        elements.append(t)
    else:
        elements.append(Paragraph("No active loans.", styles['Normal']))
        
    elements.append(Spacer(1, 0.25*inch))
    
    # Delinquent Loans
    elements.append(Paragraph(f"Delinquent Accounts ({len(delinquent_loans)})", styles['Heading2']))
    if delinquent_loans:
        data = [['Loan ID', 'Client', 'Days Overdue', 'Total Overdue']]
        for item in delinquent_loans:
            data.append([
                str(item['loan'].loan_id),
                f"{item['loan'].application.client.first_name} {item['loan'].application.client.last_name}",
                str(item['days_overdue']),
                f"P {item['total_overdue']:,.2f}"
            ])
            
        t = Table(data, colWidths=[1*inch, 3*inch, 1.5*inch, 2*inch])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.red),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('ALIGN', (-1, 0), (-1, -1), 'RIGHT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        elements.append(t)
    else:
        elements.append(Paragraph("No delinquent accounts.", styles['Normal']))
        
    elements.append(Spacer(1, 0.25*inch))
    
    # Repayments
    elements.append(Paragraph("Recent Repayments (Last 30 Days)", styles['Heading2']))
    if recent_repayments:
        data = [['Date', 'Client', 'Loan ID', 'Amount']]
        for trans in recent_repayments:
            loan_id = str(trans.loan.loan_id) if trans.loan else '-'
            data.append([
                str(trans.transaction_date.date()),
                f"{trans.account.client.first_name} {trans.account.client.last_name}",
                loan_id,
                f"P {trans.amount:,.2f}"
            ])
            
        t = Table(data, colWidths=[1.5*inch, 3*inch, 1.5*inch, 2*inch])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.green),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('ALIGN', (-1, 0), (-1, -1), 'RIGHT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        elements.append(t)
    else:
        elements.append(Paragraph("No recent repayments.", styles['Normal']))
        
    doc.build(elements)
    pdf = buffer.getvalue()
    buffer.close()
    
    response = HttpResponse(pdf, content_type='application/pdf')
    response['Content-Disposition'] = 'inline; filename="loan_reports.pdf"'
    return response

def generate_balance_sheet_pdf(report_data):
    """
    Generate Balance Sheet PDF using ReportLab.
    """
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    elements = []
    styles = getSampleStyleSheet()
    
    # Title
    title = Paragraph("Kayamanan Banking System - Balance Sheet", styles['Title'])
    elements.append(title)
    
    # Date
    date_str = f"As of {report_data['as_of_date']}"
    elements.append(Paragraph(date_str, styles['Normal']))
    elements.append(Spacer(1, 0.25*inch))
    
    # Assets
    elements.append(Paragraph("Assets", styles['Heading2']))
    if report_data['assets']:
        data = [['Account', 'Code', 'Amount']]
        for acc in report_data['assets']:
            data.append([acc['name'], acc['code'], f"P {acc['balance']:,.2f}"])
        data.append(['Total Assets', '', f"P {report_data['total_assets']:,.2f}"])
        
        t = Table(data, colWidths=[4*inch, 1*inch, 1.5*inch])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.blue),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('ALIGN', (-1, 0), (-1, -1), 'RIGHT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, -1), (-1, -1), colors.lightgrey),
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        elements.append(t)
    else:
        elements.append(Paragraph("No assets recorded.", styles['Normal']))
        
    elements.append(Spacer(1, 0.25*inch))
    
    # Liabilities
    elements.append(Paragraph("Liabilities", styles['Heading2']))
    if report_data['liabilities']:
        data = [['Account', 'Code', 'Amount']]
        for acc in report_data['liabilities']:
            data.append([acc['name'], acc['code'], f"P {acc['balance']:,.2f}"])
        data.append(['Total Liabilities', '', f"P {report_data['total_liabilities']:,.2f}"])
        
        t = Table(data, colWidths=[4*inch, 1*inch, 1.5*inch])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.red),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('ALIGN', (-1, 0), (-1, -1), 'RIGHT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, -1), (-1, -1), colors.lightgrey),
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        elements.append(t)
    else:
        elements.append(Paragraph("No liabilities recorded.", styles['Normal']))
        
    elements.append(Spacer(1, 0.25*inch))
    
    # Equity
    elements.append(Paragraph("Equity", styles['Heading2']))
    if report_data['equity']:
        data = [['Account', 'Code', 'Amount']]
        for acc in report_data['equity']:
            data.append([acc['name'], acc['code'], f"P {acc['balance']:,.2f}"])
        data.append(['Total Equity', '', f"P {report_data['total_equity']:,.2f}"])
        
        t = Table(data, colWidths=[4*inch, 1*inch, 1.5*inch])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.green),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('ALIGN', (-1, 0), (-1, -1), 'RIGHT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, -1), (-1, -1), colors.lightgrey),
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        elements.append(t)
    else:
        elements.append(Paragraph("No equity recorded.", styles['Normal']))
        
    elements.append(Spacer(1, 0.25*inch))
    
    # Total Liabilities & Equity
    elements.append(Paragraph(f"Total Liabilities & Equity: P {report_data['total_liabilities_equity']:,.2f}", styles['Heading3']))
    
    doc.build(elements)
    pdf = buffer.getvalue()
    buffer.close()
    
    response = HttpResponse(pdf, content_type='application/pdf')
    response['Content-Disposition'] = 'inline; filename="balance_sheet.pdf"'
    return response
