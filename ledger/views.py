from django.shortcuts import render, get_object_or_404
from django.utils import timezone
from datetime import datetime
from users.decorators import staff_required
from .services import FinancialReportService
from .models import GLAccount

@staff_required
def financial_report_view(request):
    """
    Display the Income Statement (Financial Report).
    Restricted to staff members.
    """
    # Get date filters from request if any
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    
    # Generate report
    report_data = FinancialReportService.get_income_statement(start_date, end_date)
    
    context = {
        'report': report_data,
        'start_date': start_date,
        'end_date': end_date,
        'today': timezone.now().date(),
        'request': request # Needed for base_url in PDF
    }
    
    if request.GET.get('export') == 'pdf':
        from utils.pdf_generator import generate_financial_report_pdf
        return generate_financial_report_pdf(report_data, start_date, end_date)
    elif request.GET.get('export') == 'excel':
        from utils.excel_generator import generate_financial_report_excel
        return generate_financial_report_excel(report_data, start_date, end_date)
    
    return render(request, 'ledger/financial_report.html', context)

@staff_required
def balance_sheet_view(request):
    """
    View for Balance Sheet Report.
    """
    as_of_date_str = request.GET.get('as_of_date')
    as_of_date = None
    
    if as_of_date_str:
        try:
            as_of_date = datetime.strptime(as_of_date_str, '%Y-%m-%d').date()
        except ValueError:
            pass
            
    report_data = FinancialReportService.get_balance_sheet(as_of_date)
    
    context = {
        'report': report_data,
        'as_of_date': report_data['as_of_date'],
    }
    
    if request.GET.get('export') == 'pdf':
        from utils.pdf_generator import generate_balance_sheet_pdf
        return generate_balance_sheet_pdf(report_data)
    elif request.GET.get('export') == 'excel':
        from utils.excel_generator import generate_balance_sheet_excel
        return generate_balance_sheet_excel(report_data)
    
    return render(request, 'ledger/balance_sheet.html', context)

@staff_required
def general_ledger_view(request):
    """
    List of all GL Accounts.
    """
    accounts = GLAccount.objects.all().order_by('code')
    context = {
        'accounts': accounts
    }
    return render(request, 'ledger/general_ledger.html', context)

@staff_required
def gl_account_detail_view(request, code):
    """
    Detail view for a specific GL Account showing transaction history.
    """
    account = get_object_or_404(GLAccount, code=code)
    entries = account.entries.all().select_related('transaction_ref').order_by('-created_at')
    
    context = {
        'account': account,
        'entries': entries
    }
    return render(request, 'ledger/gl_account_detail.html', context)
