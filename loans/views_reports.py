from django.shortcuts import render
from django.utils import timezone
from users.decorators import staff_required
from .reports import LoanReportService

@staff_required
def loan_reports_view(request):
    """
    Display comprehensive loan reports: Active, Delinquent, and Repayments.
    """
    active_loans = LoanReportService.get_active_loans()
    delinquent_loans = LoanReportService.get_delinquent_loans()
    recent_repayments = LoanReportService.get_recent_repayments()
    
    context = {
        'active_loans': active_loans,
        'delinquent_loans': delinquent_loans,
        'recent_repayments': recent_repayments,
        'today': timezone.now().date(),
        'request': request
    }
    
    if request.GET.get('export') == 'pdf':
        from utils.pdf_generator import generate_loan_report_pdf
        return generate_loan_report_pdf(active_loans, delinquent_loans, recent_repayments)
    elif request.GET.get('export') == 'excel':
        from utils.excel_generator import generate_loan_report_excel
        return generate_loan_report_excel(active_loans, delinquent_loans, recent_repayments)
    
    return render(request, 'loans/reports.html', context)

@staff_required
def delinquent_accounts_view(request):
    """
    Dedicated view for delinquent accounts report.
    """
    delinquent_loans = LoanReportService.get_delinquent_loans()
    
    # Calculate summary statistics
    total_delinquent_count = len(delinquent_loans)
    total_overdue_amount = sum(item['total_overdue'] for item in delinquent_loans)
    total_installments_overdue = sum(item['installments_overdue'] for item in delinquent_loans)
    
    context = {
        'delinquent_loans': delinquent_loans,
        'total_delinquent_count': total_delinquent_count,
        'total_overdue_amount': total_overdue_amount,
        'total_installments_overdue': total_installments_overdue,
        'today': timezone.now().date(),
        'request': request
    }
    
    if request.GET.get('export') == 'pdf':
        from utils.pdf_generator import generate_loan_report_pdf
        # Generate PDF with only delinquent loans
        return generate_loan_report_pdf([], delinquent_loans, [])
    elif request.GET.get('export') == 'excel':
        from utils.excel_generator import generate_loan_report_excel
        # Generate Excel with only delinquent loans
        return generate_loan_report_excel([], delinquent_loans, [])
    
    return render(request, 'loans/delinquent_accounts.html', context)

@staff_required
def repayment_reports_view(request):
    """
    Dedicated view for repayment reports.
    """
    from decimal import Decimal
    
    # Get date range filter (default to last 30 days)
    days = int(request.GET.get('days', 30))
    start_date = timezone.now() - timezone.timedelta(days=days)
    
    # Get repayments
    repayments = LoanReportService.get_recent_repayments(days=days)
    
    # Calculate summary statistics
    total_repayments = repayments.count()
    total_amount = sum(Decimal(str(trans.amount)) for trans in repayments)
    average_payment = total_amount / Decimal(str(total_repayments)) if total_repayments > 0 else Decimal('0.00')
    
    # Group by loan for loan-level statistics
    loan_stats = {}
    for trans in repayments:
        if trans.loan:
            loan_id = trans.loan.loan_id
            if loan_id not in loan_stats:
                loan_stats[loan_id] = {
                    'loan': trans.loan,
                    'count': 0,
                    'total': Decimal('0.00')
                }
            loan_stats[loan_id]['count'] += 1
            loan_stats[loan_id]['total'] += Decimal(str(trans.amount))
    
    context = {
        'repayments': repayments,
        'total_repayments': total_repayments,
        'total_amount': total_amount,
        'average_payment': average_payment,
        'loan_stats': loan_stats.values(),
        'days': days,
        'start_date': start_date.date(),
        'today': timezone.now().date(),
        'request': request
    }
    
    if request.GET.get('export') == 'pdf':
        from utils.pdf_generator import generate_loan_report_pdf
        # Generate PDF with only repayments
        return generate_loan_report_pdf([], [], repayments)
    elif request.GET.get('export') == 'excel':
        from utils.excel_generator import generate_loan_report_excel
        # Generate Excel with only repayments
        return generate_loan_report_excel([], [], repayments)
    
    return render(request, 'loans/repayment_reports.html', context)
