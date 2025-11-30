from django.shortcuts import render
from django.contrib.admin.views.decorators import staff_member_required
from django.utils import timezone
from .reports import LoanReportService

@staff_member_required
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
