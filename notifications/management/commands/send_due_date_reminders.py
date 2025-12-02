from django.core.management.base import BaseCommand
from django.utils import timezone
from loans.models import Loan
from notifications.services import NotificationService
from datetime import timedelta

class Command(BaseCommand):
    help = 'Send reminders for loans due within the next 7 days (daily in the final week)'

    def handle(self, *args, **kwargs):
        today = timezone.now().date()
        window_end = today + timedelta(days=7)

        self.stdout.write(f"Checking for loans due between {today} and {window_end}...")

        # Find pending schedules due within the next 7 days
        from loans.models import AmortizationSchedule
        schedules_due = AmortizationSchedule.objects.filter(
            due_date__range=(today, window_end),
            status='pending',
            loan__status='active'
        ).select_related('loan', 'loan__application__client__user')
        
        count = 0
        for schedule in schedules_due:
            loan = schedule.loan
            user = loan.application.client.user
            amount_due = schedule.total_payment

            days_until_due = (schedule.due_date - today).days

            subject = "Payment Reminder: Loan Payment Coming Up"
            message = (
                f"Dear {loan.application.client.first_name}, this is a reminder that your loan payment of "
                f"P{amount_due:,.2f} for Loan #{loan.loan_id} is due on {schedule.due_date}. "
                f"(in {days_until_due} day{'s' if days_until_due != 1 else ''}). "
                "Please ensure your account has sufficient funds."
            )

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
