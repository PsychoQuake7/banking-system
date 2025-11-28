from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from clients.models import Client
from .models import Loan, LoanApplication, AmortizationSchedule
from users.decorators import staff_required, require_role

# Create your views here.
@login_required
def loan_list_view(request):
    # Staff/Admin see all loans, Borrowers see only their own
    if request.user.role in ['admin', 'staff']:
        applications = LoanApplication.objects.all().order_by('-application_date')
        active_loans = Loan.objects.filter(status='active').order_by('-start_date')
    elif hasattr(request.user, 'client'):
        applications = LoanApplication.objects.filter(client=request.user.client).order_by('-application_date')
        active_loans = Loan.objects.filter(client=request.user.client, status='active').order_by('-start_date')
    else:
        applications = LoanApplication.objects.none()
        active_loans = Loan.objects.none()
    
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
        
    schedule = loan.schedules.all()
    context = {
        'loan': loan,
        'schedule': schedule,
    }
    return render(request, 'loans/loan_detail.html', context)

@login_required
def loan_application_view(request):
    client = None
    eligibility_score = 0
    
    if hasattr(request.user, 'client'):
        client = request.user.client
        # Calculate simple eligibility score
        if client.credit_score >= 800:
            eligibility_score = 95
        elif client.credit_score >= 700:
            eligibility_score = 85
        elif client.credit_score >= 600:
            eligibility_score = 65
        else:
            eligibility_score = 45
            
    context = {
        'client': client,
        'eligibility_score': eligibility_score
    }
    return render(request, 'loans/loan_application.html', context)

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
    is_owner = hasattr(request.user, 'client') and loan.client == request.user.client
    is_staff = request.user.role in ['admin', 'staff']
    
    if not (is_owner or is_staff):
        raise PermissionDenied("You do not have permission to make payments for this loan.")
        
    context = {
        'loan': loan,
    }
    return render(request, 'loans/make_payment.html', context)

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