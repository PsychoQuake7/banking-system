from django.core.management.base import BaseCommand
from django.utils import timezone
from loans.models import Loan
from notifications.services import NotificationService
from datetime import timedelta

class Command(BaseCommand):
    help = 'Send reminders for loans due in 3 days'

    def handle(self, *args, **kwargs):
        today = timezone.now().date()
        target_date = today + timedelta(days=3)
        
        self.stdout.write(f"Checking for loans due on {target_date}...")
        
        # Find pending schedules due on target_date
        from loans.models import AmortizationSchedule
        schedules_due = AmortizationSchedule.objects.filter(
            due_date=target_date,
            status='pending',
            loan__status='active'
        )
        
        count = 0
        for schedule in schedules_due:
            loan = schedule.loan
            user = loan.application.client.user
            amount_due = schedule.total_payment
            
            subject = "Payment Reminder: Loan Due Soon"
            message = f"Dear {loan.application.client.first_name}, this is a reminder that your loan payment of P{amount_due:,.2f} for Loan #{loan.loan_id} is due on {target_date}. Please ensure your account has sufficient funds."
            
            NotificationService.send_notification(
                user=user,
                subject=subject,
                message=message,
                notification_type='payment_reminder',
                related_entity_type='loan',
                related_entity_id=loan.loan_id
            )
            count += 1
            
        self.stdout.write(self.style.SUCCESS(f"Sent {count} reminders."))
