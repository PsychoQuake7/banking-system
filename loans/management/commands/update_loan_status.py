from django.core.management.base import BaseCommand
from loans.models import Loan

class Command(BaseCommand):
    help = 'Update amortization schedule status for all active loans'

    def handle(self, *args, **options):
        active_loans = Loan.objects.filter(status='active')
        total_overdue = 0
        
        self.stdout.write(f'Checking {active_loans.count()} active loans...')
        
        for loan in active_loans:
            overdue_count = loan.update_schedule_status()
            if overdue_count > 0:
                self.stdout.write(f'  Loan #{loan.loan_id}: Marked {overdue_count} payments as overdue')
            total_overdue += overdue_count
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully updated {active_loans.count()} loans. '
                f'Total payments marked as overdue: {total_overdue}'
            )
        )
