from django.core.management.base import BaseCommand
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from django.utils import timezone
from loans.models import AmortizationSchedule
from datetime import timedelta

class Command(BaseCommand):
    help = 'Send email reminders for upcoming loan payments'

    def handle(self, *args, **options):
        # Calculate target date (3 days from now)
        today = timezone.now().date()
        target_date = today + timedelta(days=3)
        
        self.stdout.write(f'Checking for payments due on {target_date}...')
        
        # Find payments due in 3 days that haven't been reminded
        upcoming_payments = AmortizationSchedule.objects.filter(
            status='pending',
            due_date=target_date,
            reminder_sent=False
        ).select_related('loan', 'loan__application__client', 'loan__application__client__user')
        
        count = upcoming_payments.count()
        if count == 0:
            self.stdout.write('No upcoming payments found requiring reminders.')
            return
            
        self.stdout.write(f'Found {count} payments. Sending reminders...')
        
        sent_count = 0
        for payment in upcoming_payments:
            try:
                client = payment.loan.application.client
                user = client.user
                
                if not user.email:
                    self.stdout.write(self.style.WARNING(f'  Skipping Loan #{payment.loan.loan_id}: No email for user {user.username}'))
                    continue
                
                # Prepare email content
                context = {
                    'client_name': f"{client.first_name} {client.last_name}",
                    'loan_id': payment.loan.loan_id,
                    'installment_number': payment.installment_number,
                    'amount': payment.total_payment,
                    'due_date': payment.due_date,
                }
                
                email_body = render_to_string('emails/payment_reminder.txt', context)
                email_subject = f"Payment Reminder: Loan #{payment.loan.loan_id} Due Soon"
                
                # Send email
                send_mail(
                    email_subject,
                    email_body,
                    settings.DEFAULT_FROM_EMAIL,
                    [user.email],
                    fail_silently=False,
                )
                
                # Mark as sent
                payment.reminder_sent = True
                payment.save()
                sent_count += 1
                self.stdout.write(f'  Sent reminder to {user.email} for Loan #{payment.loan.loan_id}')
                
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'  Failed to send reminder for Loan #{payment.loan.loan_id}: {str(e)}'))
        
        self.stdout.write(self.style.SUCCESS(f'Successfully sent {sent_count} reminders.'))
