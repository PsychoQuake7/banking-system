from django.db.models import Sum, F
from django.utils import timezone
from .models import Loan, AmortizationSchedule
from transactions.models import Transaction

class LoanReportService:
    @staticmethod
    def get_active_loans():
        """
        Get all currently active loans.
        """
        return Loan.objects.filter(status='active').select_related('application__client')

    @staticmethod
    def get_delinquent_loans():
        """
        Get loans with overdue payments.
        Returns a list of dictionaries containing loan details and overdue info.
        """
        # Find schedules that are overdue or pending but past due date
        today = timezone.now().date()
        overdue_schedules = AmortizationSchedule.objects.filter(
            status__in=['overdue', 'pending'],
            due_date__lt=today
        ).select_related('loan', 'loan__application__client')

        # Group by loan to avoid duplicates if multiple installments are overdue
        delinquent_map = {}
        
        for schedule in overdue_schedules:
            loan_id = schedule.loan.loan_id
            if loan_id not in delinquent_map:
                delinquent_map[loan_id] = {
                    'loan': schedule.loan,
                    'total_overdue': 0,
                    'days_overdue': 0,
                    'installments_overdue': 0
                }
            
            # Add up amounts
            amount_due = schedule.total_payment
            delinquent_map[loan_id]['total_overdue'] += amount_due
            delinquent_map[loan_id]['installments_overdue'] += 1
            
            # Calculate days overdue (max of all overdue schedules)
            days = (today - schedule.due_date).days
            if days > delinquent_map[loan_id]['days_overdue']:
                delinquent_map[loan_id]['days_overdue'] = days

        return list(delinquent_map.values())

    @staticmethod
    def get_recent_repayments(days=30):
        """
        Get recent loan repayments.
        """
        start_date = timezone.now() - timezone.timedelta(days=days)
        return Transaction.objects.filter(
            transaction_type='payment',
            transaction_date__gte=start_date
        ).select_related('account', 'loan', 'loan__application__client').order_by('-transaction_date')
