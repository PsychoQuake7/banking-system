from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Q, Count
from django.utils import timezone
from datetime import timedelta
from clients.models import Client
from accounts.models import Account
from loans.models import Loan, LoanApplication, AmortizationSchedule
from transactions.models import Transaction

@login_required
def dashboard_view(request):
    """
    Dashboard view that displays user-specific banking data.
    Shows account balances, loan information, recent transactions, and notifications.
    """
    context = {}
    
    try:
        # Get the client profile for the logged-in user
        client = Client.objects.get(user=request.user)
        context['client'] = client
        
        # Get all accounts for this client
        accounts = Account.objects.filter(client=client, is_active=True)
        
        # Calculate total balance across all accounts
        total_balance = accounts.aggregate(total=Sum('current_balance'))['total'] or 0
        context['total_balance'] = total_balance
        
        # Count total accounts
        context['accounts_count'] = accounts.count()
        
        # Get loan applications for this client
        loan_applications = LoanApplication.objects.filter(client=client)
        
        # Count active loans (approved applications with active loan status)
        active_loans = Loan.objects.filter(
            application__client=client,
            status='active'
        )
        context['active_loans_count'] = active_loans.count()
        
        # Count pending loan applications
        context['pending_loans_count'] = loan_applications.filter(status='pending').count()
        
        # Get recent transactions (last 10 transactions from user's accounts)
        recent_transactions = Transaction.objects.filter(
            account__client=client
        ).select_related('account').order_by('-transaction_date')[:10]
        context['recent_transactions'] = recent_transactions
        
        # Get upcoming loan payments (next 5 upcoming payments)
        today = timezone.now().date()
        upcoming_payments = AmortizationSchedule.objects.filter(
            loan__application__client=client,
            status='pending',
            due_date__gte=today
        ).select_related('loan').order_by('due_date')[:5]
        context['upcoming_payments'] = upcoming_payments
        
        # Placeholder for notifications (you can implement a Notification model later)
        # For now, we'll create dynamic notifications based on loan status
        notifications = []
        
        # Check for overdue payments
        overdue_payments = AmortizationSchedule.objects.filter(
            loan__application__client=client,
            status='overdue'
        ).count()
        
        if overdue_payments > 0:
            notifications.append({
                'subject': 'Overdue Payment Alert',
                'message': f'You have {overdue_payments} overdue payment(s). Please settle them as soon as possible.',
                'notification_type': 'payment_reminder',
                'sent_date': timezone.now()
            })
        
        # Check for pending loan applications
        pending_apps = loan_applications.filter(status='pending').count()
        if pending_apps > 0:
            notifications.append({
                'subject': 'Loan Application Status',
                'message': f'You have {pending_apps} loan application(s) pending review.',
                'notification_type': 'info',
                'sent_date': timezone.now()
            })
        
        # Check for upcoming payments in next 7 days
        upcoming_soon = AmortizationSchedule.objects.filter(
            loan__application__client=client,
            status='pending',
            due_date__gte=today,
            due_date__lte=today + timedelta(days=7)
        ).count()
        
        if upcoming_soon > 0:
            notifications.append({
                'subject': 'Upcoming Payment Reminder',
                'message': f'You have {upcoming_soon} payment(s) due in the next 7 days.',
                'notification_type': 'payment_reminder',
                'sent_date': timezone.now()
            })
        
        context['notifications'] = notifications
        
    except Client.DoesNotExist:
        # If user doesn't have a client profile, show empty dashboard
        context['total_balance'] = 0
        context['accounts_count'] = 0
        context['active_loans_count'] = 0
        context['pending_loans_count'] = 0
        context['recent_transactions'] = []
        context['upcoming_payments'] = []
        context['notifications'] = [{
            'subject': 'Complete Your Profile',
            'message': 'Please complete your client profile to access banking services.',
            'notification_type': 'info',
            'sent_date': timezone.now()
        }]
    
    return render(request, 'dashboard.html', context)