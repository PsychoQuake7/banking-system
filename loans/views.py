from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from clients.models import Client
from .models import Loan, LoanApplication, AmortizationSchedule

# Create your views here.
def loan_list_view(request):
    # For testing purposes, we'll show all loans if not authenticated or no client
    # In production, this should be filtered by the logged-in user's client
    applications = LoanApplication.objects.all().order_by('-application_date')
    active_loans = Loan.objects.filter(status='active').order_by('-start_date')
    
    context = {
        'applications': applications,
        'active_loans': active_loans,
    }
    return render(request, 'loans/loan_list.html', context)

def loan_detail_view(request, id):
    loan = get_object_or_404(Loan, loan_id=id)
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

def loan_application_list_view(request):
    applications = LoanApplication.objects.all().order_by('-application_date')
    context = {
        'applications': applications,
    }
    return render(request, 'loans/loan_application_list.html', context)

def make_payment_view(request, id):
    loan = get_object_or_404(Loan, loan_id=id)
    context = {
        'loan': loan,
    }
    return render(request, 'loans/make_payment.html', context)

def amortization_schedule_view(request, id):
    loan = get_object_or_404(Loan, loan_id=id)
    schedule = loan.schedules.all()
    context = {
        'loan': loan,
        'schedule': schedule,
    }
    return render(request, 'loans/amortization_schedule.html', context)