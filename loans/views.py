from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.contrib import messages
from django.http import FileResponse, Http404
from django.utils import timezone
from django.core.files import File
from clients.models import Client
from .models import Loan, LoanApplication, AmortizationSchedule
from users.decorators import staff_required, require_role
from decimal import Decimal
from datetime import date, timedelta
from dateutil.relativedelta import relativedelta
import os

# Create your views here.
@login_required
def loan_list_view(request):
    # Staff/Admin see all loans, Borrowers see only their own
    if request.user.role in ['admin', 'staff']:
        applications = LoanApplication.objects.all().order_by('-application_date')
        active_loans = Loan.objects.filter(status='active').order_by('-start_date')
    elif hasattr(request.user, 'client'):
        applications = LoanApplication.objects.filter(client=request.user.client).order_by('-application_date')
        active_loans = Loan.objects.filter(application__client=request.user.client, status='active').order_by('-start_date')
    else:
        applications = LoanApplication.objects.none()
        active_loans = Loan.objects.none()
    
    # Update status for active loans
    for loan in active_loans:
        loan.update_schedule_status()
    
    context = {
        'applications': applications,
        'active_loans': active_loans,
    }
    return render(request, 'loans/loan_list.html', context)

@login_required
def loan_detail_view(request, id):
    loan = get_object_or_404(Loan, loan_id=id)
    
    # Check permission: Owner or Staff/Admin
    is_owner = hasattr(request.user, 'client') and loan.client == request.user.client
    is_staff = request.user.role in ['admin', 'staff']
    
    if not (is_owner or is_staff):
        raise PermissionDenied("You do not have permission to view this loan.")
    
    # Update schedule status
    loan.update_schedule_status()
        
    schedule = loan.schedules.all()
    context = {
        'loan': loan,
        'schedule': schedule,
    }
    return render(request, 'loans/loan_detail.html', context)

@login_required
def loan_application_view(request):
    client = None
    eligibility_data = None
    
    if hasattr(request.user, 'client'):
        client = request.user.client
        # Use comprehensive eligibility calculation
        from loans.utils import calculate_eligibility_score, get_improvement_suggestions
        
        eligibility_data = calculate_eligibility_score(client)
        eligibility_data['suggestions'] = get_improvement_suggestions(eligibility_data)
            
    if request.method == 'POST':
        if not client:
            raise PermissionDenied("You must be a client to apply for a loan.")
            
        loan_amount = Decimal(request.POST.get('loan_amount'))
        purpose = request.POST.get('purpose')
        custom_purpose = request.POST.get('custom_purpose')
        term_months = request.POST.get('term_months')
        
        if purpose == 'Other' and custom_purpose:
            purpose = custom_purpose
            
        # Create application
        application = LoanApplication.objects.create(
            client=client,
            loan_amount=loan_amount,
            purpose=purpose,
            term_months=term_months,
        )
        
        # Calculate eligibility score immediately
        application.update_eligibility_score()
        
        return redirect('loans:loan_list')

    context = {
        'client': client,
        'eligibility_data': eligibility_data
    }
    return render(request, 'loans/loan_application.html', context)

@login_required
def loan_eligibility_check_view(request):
    """
    View for clients to check their loan eligibility without applying.
    """
    client = None
    eligibility_data = None
    requested_amount = None
    
    if hasattr(request.user, 'client'):
        client = request.user.client
        
        if request.method == 'POST':
            amount_str = request.POST.get('requested_amount')
            if amount_str:
                try:
                    requested_amount = Decimal(amount_str)
                except:
                    pass
        
        from loans.utils import calculate_eligibility_score, get_improvement_suggestions
        
        eligibility_data = calculate_eligibility_score(client, requested_amount)
        eligibility_data['suggestions'] = get_improvement_suggestions(eligibility_data)
    
    context = {
        'client': client,
        'eligibility_data': eligibility_data,
        'requested_amount': requested_amount
    }
    return render(request, 'loans/loan_eligibility.html', context)

@staff_required
def loan_application_list_view(request):
    """View for staff/admin to review all loan applications"""
    applications = LoanApplication.objects.all().order_by('-application_date')
    context = {
        'applications': applications,
    }
    return render(request, 'loans/loan_application_list.html', context)

@login_required
def make_payment_view(request, id):
    loan = get_object_or_404(Loan, loan_id=id)
    
    # Check permission: Owner or Staff/Admin
    is_owner = hasattr(request.user, 'client') and loan.application.client == request.user.client
    is_staff = request.user.role in ['admin', 'staff']
    
    if not (is_owner or is_staff):
        raise PermissionDenied("You do not have permission to make payments for this loan.")
    
    # Get client's accounts
    if hasattr(request.user, 'client'):
        from accounts.models import Account
        accounts = Account.objects.filter(client=request.user.client)
    else:
        accounts = []
    
    # Get next payment due
    next_payment = loan.get_next_payment_due()
    
    # Handle payment submission
    if request.method == 'POST':
        account_id = request.POST.get('account_id')
        payment_amount = Decimal(request.POST.get('payment_amount', '0'))
        
        # Validate account
        from accounts.models import Account
        try:
            account = Account.objects.get(account_id=account_id)
            # Verify account ownership
            if hasattr(request.user, 'client') and account.client != request.user.client:
                raise PermissionDenied("You do not have permission to use this account.")
        except Account.DoesNotExist:
            messages.error(request, 'Invalid account selected.')
            return redirect('loans:make_payment', id=id)
        
        # Process payment using Loan model method
        result = loan.apply_payment(payment_amount, account)
        
        if result['success']:
            messages.success(request, result['message'])
            return redirect('loans:loan_detail', id=loan.loan_id)
        else:
            messages.error(request, result['message'])
    
    context = {
        'loan': loan,
        'accounts': accounts,
        'next_payment': next_payment,
    }
    return render(request, 'loans/make_payment.html', context)

@login_required
@staff_required
def disburse_loan_view(request, id):
    loan = get_object_or_404(Loan, loan_id=id)
    
    if loan.is_disbursed:
        messages.warning(request, "This loan has already been disbursed.")
        return redirect('loan_detail', id=loan.loan_id)
        
    if request.method == 'POST':
        account_id = request.POST.get('account_id')
        account = get_object_or_404(Account, account_id=account_id, client=loan.application.client)
        
        result = loan.disburse_funds(account)
        
        if result['success']:
            messages.success(request, result['message'])
            return redirect('loan_detail', id=loan.loan_id)
        else:
            messages.error(request, result['message'])
    
    # Get client's accounts
    accounts = Account.objects.filter(client=loan.application.client)
    
    context = {
        'loan': loan,
        'accounts': accounts,
    }
    return render(request, 'loans/disburse_loan.html', context)


@login_required
def amortization_schedule_view(request, id):
    loan = get_object_or_404(Loan, loan_id=id)
    
    # Check permission: Owner or Staff/Admin
    is_owner = hasattr(request.user, 'client') and loan.client == request.user.client
    is_staff = request.user.role in ['admin', 'staff']
    
    if not (is_owner or is_staff):
        raise PermissionDenied("You do not have permission to view this schedule.")
        
    schedule = loan.schedules.all()
    context = {
        'loan': loan,
        'schedule': schedule,
    }
    return render(request, 'loans/amortization_schedule.html', context)

@staff_required
def loan_application_detail_view(request, id):
    """Detailed view of a loan application for staff review."""
    application = get_object_or_404(LoanApplication, application_id=id)
    
    # Calculate eligibility data
    from loans.utils import calculate_eligibility_score, get_improvement_suggestions
    eligibility_data = calculate_eligibility_score(application.client, application.loan_amount)
    eligibility_data['suggestions'] = get_improvement_suggestions(eligibility_data)
    
    # Calculate loan preview (assuming 12% annual interest rate)
    interest_rate = Decimal('0.12')
    monthly_payment = application.calculate_monthly_payment(interest_rate, application.term_months)
    total_payment = monthly_payment * application.term_months
    total_interest = total_payment - application.loan_amount
    
    context = {
        'application': application,
        'eligibility_data': eligibility_data,
        'interest_rate': interest_rate,
        'monthly_payment': monthly_payment,
        'total_payment': total_payment,
        'total_interest': total_interest,
    }
    return render(request, 'loans/loan_application_detail.html', context)

@staff_required
def approve_loan_application_view(request, id):
    """Approve a loan application and generate loan agreement document."""
    if request.method != 'POST':
        return redirect('loans:loan_application_detail', id=id)
    
    application = get_object_or_404(LoanApplication, application_id=id)
    
    # Check if already approved
    if application.status == 'approved':
        messages.warning(request, 'This application has already been approved.')
        return redirect('loans:loan_application_detail', id=id)
    
    # Get interest rate from form or use default
    interest_rate = Decimal(request.POST.get('interest_rate', '0.12'))
    
    # Update application status
    application.status = 'approved'
    application.approval_date = timezone.now()
    application.loan_officer = request.user
    application.save()
    
    # Calculate loan dates
    start_date = date.today()
    end_date = start_date + relativedelta(months=application.term_months)
    
    # Create Loan object
    loan = Loan.objects.create(
        application=application,
        loan_amount=application.loan_amount,
        interest_rate=interest_rate,
        term_months=application.term_months,
        start_date=start_date,
        end_date=end_date,
        remaining_balance=application.loan_amount,
        status='active'
    )
    
    # Generate amortization schedule
    monthly_payment = loan.get_monthly_payment()
    remaining_balance = loan.loan_amount
    current_date = start_date
    
    for i in range(1, loan.term_months + 1):
        current_date = current_date + relativedelta(months=1)
        
        # Calculate interest and principal for this payment
        monthly_rate = loan.interest_rate / 12
        interest_amount = remaining_balance * monthly_rate
        principal_amount = monthly_payment - interest_amount
        
        # Adjust last payment to account for rounding
        if i == loan.term_months:
            principal_amount = remaining_balance
            total_payment = principal_amount + interest_amount
        else:
            total_payment = monthly_payment
        
        AmortizationSchedule.objects.create(
            loan=loan,
            installment_number=i,
            due_date=current_date,
            principal_amount=principal_amount,
            interest_amount=interest_amount,
            total_payment=total_payment,
            status='pending'
        )
        
        remaining_balance -= principal_amount
    
    # Generate loan agreement PDF
    try:
        from .document_generator import generate_loan_agreement
        agreement_path = generate_loan_agreement(loan)
        loan.agreement_document = agreement_path
        loan.save()
        messages.success(request, f'Loan application approved successfully! Agreement document generated.')
    except Exception as e:
        messages.warning(request, f'Loan approved but document generation failed: {str(e)}')
    
    return redirect('loans:loan_detail', id=loan.loan_id)

@staff_required
def reject_loan_application_view(request, id):
    """Reject a loan application with reason."""
    if request.method != 'POST':
        return redirect('loans:loan_application_detail', id=id)
    
    application = get_object_or_404(LoanApplication, application_id=id)
    
    # Check if already processed
    if application.status != 'pending':
        messages.warning(request, 'This application has already been processed.')
        return redirect('loans:loan_application_detail', id=id)
    
    # Update application status
    application.status = 'rejected'
    application.rejection_reason = request.POST.get('rejection_reason', '')
    application.loan_officer = request.user
    application.save()
    
    messages.success(request, 'Loan application rejected.')
    return redirect('loans:loan_application_list')

@login_required
def download_loan_agreement_view(request, loan_id):
    """Download loan agreement PDF document."""
    loan = get_object_or_404(Loan, loan_id=loan_id)
    
    # Check permission: Owner or Staff/Admin
    is_owner = hasattr(request.user, 'client') and loan.application.client == request.user.client
    is_staff = request.user.role in ['admin', 'staff']
    
    if not (is_owner or is_staff):
        raise PermissionDenied("You do not have permission to download this agreement.")
    
    # Check if agreement document exists
    if not loan.agreement_document:
        raise Http404("Agreement document not found.")
    
    # Serve the file
    try:
        file_path = loan.agreement_document.path
        response = FileResponse(open(file_path, 'rb'), content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="{loan.get_agreement_filename()}"'
        return response
    except FileNotFoundError:
        raise Http404("Agreement document file not found.")