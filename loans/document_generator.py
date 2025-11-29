"""
Loan Agreement PDF Document Generator

This module provides utilities to generate professional loan agreement PDF documents
using ReportLab library. The generated documents include all loan terms, client information,
payment schedules, and legal clauses.
"""

from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_JUSTIFY
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib import colors
from datetime import datetime, timedelta
from decimal import Decimal
import os
from django.conf import settings


def generate_loan_agreement(loan):
    """
    Generate a professional loan agreement PDF document.
    
    Args:
        loan: Loan model instance
        
    Returns:
        str: Path to the generated PDF file relative to MEDIA_ROOT
    """
    # Create media directory if it doesn't exist
    agreements_dir = os.path.join(settings.MEDIA_ROOT, 'loan_agreements')
    os.makedirs(agreements_dir, exist_ok=True)
    
    # Generate filename
    filename = loan.get_agreement_filename()
    filepath = os.path.join(agreements_dir, filename)
    
    # Create PDF document
    doc = SimpleDocTemplate(
        filepath,
        pagesize=letter,
        rightMargin=0.75*inch,
        leftMargin=0.75*inch,
        topMargin=0.75*inch,
        bottomMargin=0.75*inch
    )
    
    # Container for the 'Flowable' objects
    elements = []
    
    # Define styles
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=18,
        textColor=colors.HexColor('#1a5490'),
        spaceAfter=30,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=14,
        textColor=colors.HexColor('#1a5490'),
        spaceAfter=12,
        spaceBefore=12,
        fontName='Helvetica-Bold'
    )
    
    normal_style = styles['Normal']
    normal_style.alignment = TA_JUSTIFY
    
    # Add header
    elements.extend(create_agreement_header(loan, title_style, normal_style))
    elements.append(Spacer(1, 0.2*inch))
    
    # Add client section
    elements.append(Paragraph("BORROWER INFORMATION", heading_style))
    elements.extend(create_client_section(loan, normal_style))
    elements.append(Spacer(1, 0.2*inch))
    
    # Add loan terms section
    elements.append(Paragraph("LOAN TERMS AND CONDITIONS", heading_style))
    elements.extend(create_loan_terms_section(loan, normal_style))
    elements.append(Spacer(1, 0.2*inch))
    
    # Add payment schedule summary
    elements.append(Paragraph("PAYMENT SCHEDULE", heading_style))
    elements.extend(create_payment_schedule_summary(loan, normal_style))
    elements.append(Spacer(1, 0.2*inch))
    
    # Add legal clauses
    elements.append(Paragraph("TERMS AND CONDITIONS", heading_style))
    elements.extend(create_legal_clauses(normal_style))
    elements.append(Spacer(1, 0.3*inch))
    
    # Add signature section
    elements.extend(create_signature_section(loan, normal_style))
    
    # Build PDF
    doc.build(elements)
    
    # Return relative path for FileField
    return os.path.join('loan_agreements', filename)


def create_agreement_header(loan, title_style, normal_style):
    """Create document header with bank name and agreement details."""
    elements = []
    
    # Bank name
    elements.append(Paragraph("KAYAMANAN BANK", title_style))
    elements.append(Paragraph("LOAN AGREEMENT", title_style))
    elements.append(Spacer(1, 0.1*inch))
    
    # Agreement details
    agreement_date = loan.start_date.strftime("%B %d, %Y")
    agreement_number = f"LA-{loan.loan_id:06d}"
    
    details_text = f"""
    <para alignment="center">
    <b>Agreement Number:</b> {agreement_number}<br/>
    <b>Date:</b> {agreement_date}
    </para>
    """
    elements.append(Paragraph(details_text, normal_style))
    
    return elements


def create_client_section(loan, normal_style):
    """Create client information section."""
    elements = []
    
    client = loan.application.client
    
    # Client information table
    client_data = [
        ['Full Name:', f"{client.first_name} {client.last_name}"],
        ['Client ID:', f"{client.client_id}"],
        ['Date of Birth:', client.date_of_birth.strftime("%B %d, %Y")],
        ['Address:', client.address or 'N/A'],
        ['Credit Score:', str(client.credit_score)],
        ['Monthly Income:', f"₱{client.monthly_income:,.2f}"],
    ]
    
    client_table = Table(client_data, colWidths=[2*inch, 4.5*inch])
    client_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#1a5490')),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
    ]))
    
    elements.append(client_table)
    
    return elements


def create_loan_terms_section(loan, normal_style):
    """Create loan terms and conditions section."""
    elements = []
    
    monthly_payment = loan.get_monthly_payment()
    total_payment = monthly_payment * loan.term_months
    total_interest = total_payment - loan.loan_amount
    
    # Format currency
    def format_currency(amount):
        return f"₱{amount:,.2f}"
    
    # Loan terms table
    terms_data = [
        ['Loan Amount:', format_currency(loan.loan_amount)],
        ['Interest Rate:', f"{float(loan.interest_rate * 100):.2f}% per annum"],
        ['Loan Term:', f"{loan.term_months} months"],
        ['Monthly Payment:', format_currency(monthly_payment)],
        ['Total Interest:', format_currency(total_interest)],
        ['Total Amount Payable:', format_currency(total_payment)],
        ['Start Date:', loan.start_date.strftime("%B %d, %Y")],
        ['Maturity Date:', loan.end_date.strftime("%B %d, %Y")],
    ]
    
    terms_table = Table(terms_data, colWidths=[2.5*inch, 4*inch])
    terms_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#1a5490')),
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#e8f4f8')),
        ('BACKGROUND', (0, 5), (-1, 5), colors.HexColor('#e8f4f8')),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
    ]))
    
    elements.append(terms_table)
    
    return elements


def create_payment_schedule_summary(loan, normal_style):
    """Create payment schedule summary section."""
    elements = []
    
    monthly_payment = loan.get_monthly_payment()
    
    summary_text = f"""
    The Borrower agrees to repay the loan in {loan.term_months} equal monthly installments 
    of {monthly_payment:,.2f} Philippine Pesos (₱{monthly_payment:,.2f}), commencing on 
    {(loan.start_date + timedelta(days=30)).strftime("%B %d, %Y")} and continuing on the 
    same day of each subsequent month until the loan is fully repaid.
    """
    
    elements.append(Paragraph(summary_text, normal_style))
    elements.append(Spacer(1, 0.1*inch))
    
    # Payment details
    payment_text = """
    <b>Payment Method:</b> Payments shall be made by cash, check, or electronic transfer 
    to the Bank's designated account. All payments must be received by the Bank on or 
    before the due date to avoid late payment charges.
    """
    
    elements.append(Paragraph(payment_text, normal_style))
    
    return elements


def create_legal_clauses(normal_style):
    """Create standard legal terms and conditions."""
    elements = []
    
    clauses = [
        {
            'title': '1. Late Payment',
            'text': 'If any payment is not received within 5 days of the due date, a late fee of 2% of the overdue amount will be charged. Continued non-payment may result in default proceedings.'
        },
        {
            'title': '2. Prepayment',
            'text': 'The Borrower may prepay the loan in full or in part at any time without penalty. Prepayments will be applied first to accrued interest and then to principal.'
        },
        {
            'title': '3. Default',
            'text': 'The loan shall be considered in default if: (a) any payment is more than 30 days overdue, (b) the Borrower files for bankruptcy, or (c) the Borrower provides false information. Upon default, the entire outstanding balance becomes immediately due and payable.'
        },
        {
            'title': '4. Governing Law',
            'text': 'This agreement shall be governed by and construed in accordance with the laws of the Republic of the Philippines.'
        },
        {
            'title': '5. Amendments',
            'text': 'No amendment or modification of this agreement shall be valid unless made in writing and signed by both parties.'
        },
        {
            'title': '6. Entire Agreement',
            'text': 'This agreement constitutes the entire agreement between the parties and supersedes all prior negotiations, representations, or agreements, whether written or oral.'
        }
    ]
    
    for clause in clauses:
        clause_text = f"<b>{clause['title']}</b><br/>{clause['text']}"
        elements.append(Paragraph(clause_text, normal_style))
        elements.append(Spacer(1, 0.1*inch))
    
    return elements


def create_signature_section(loan, normal_style):
    """Create signature blocks for client and bank officer."""
    elements = []
    
    elements.append(Spacer(1, 0.3*inch))
    
    # Acknowledgment text
    ack_text = """
    By signing below, the Borrower acknowledges that they have read, understood, and agree 
    to all terms and conditions set forth in this Loan Agreement.
    """
    elements.append(Paragraph(ack_text, normal_style))
    elements.append(Spacer(1, 0.3*inch))
    
    # Signature table
    sig_data = [
        ['BORROWER', 'LOAN OFFICER'],
        ['', ''],
        ['', ''],
        ['_' * 30, '_' * 30],
        [f"{loan.application.client.first_name} {loan.application.client.last_name}", 
         loan.application.loan_officer.username if loan.application.loan_officer else 'Bank Officer'],
        ['Signature over Printed Name', 'Signature over Printed Name'],
        ['', ''],
        ['Date: _______________', 'Date: _______________'],
    ]
    
    sig_table = Table(sig_data, colWidths=[3.25*inch, 3.25*inch])
    sig_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 11),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('ALIGN', (0, 3), (-1, 3), 'CENTER'),
        ('ALIGN', (0, 4), (-1, 4), 'CENTER'),
        ('ALIGN', (0, 5), (-1, 5), 'CENTER'),
        ('FONTNAME', (0, 4), (-1, 4), 'Helvetica-Bold'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
    ]))
    
    elements.append(sig_table)
    
    return elements
