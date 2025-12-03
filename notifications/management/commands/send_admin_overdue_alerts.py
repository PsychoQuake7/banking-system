from django.core.management.base import BaseCommand
from django.utils import timezone
from loans.reports import LoanReportService
from notifications.services import NotificationService
from users.models import CustomUser

class Command(BaseCommand):
    help = 'Send admin alerts for overdue loans'

    def handle(self, *args, **kwargs):
        today = timezone.now().date()
        self.stdout.write(f"Checking for overdue loans on {today}...")

        # Get delinquent loans
        delinquent_loans = LoanReportService.get_delinquent_loans()
        
        if not delinquent_loans:
            self.stdout.write(self.style.SUCCESS("No overdue loans found. All accounts are current."))
            return

        # Get all admin users
        admin_users = CustomUser.objects.filter(role='admin', is_active=True)
        
        if not admin_users.exists():
            self.stdout.write(self.style.WARNING("No admin users found. Skipping alerts."))
            return

        # Calculate summary statistics
        total_delinquent = len(delinquent_loans)
        total_overdue_amount = sum(item['total_overdue'] for item in delinquent_loans)
        critical_count = sum(1 for item in delinquent_loans if item['days_overdue'] >= 90)
        severe_count = sum(1 for item in delinquent_loans if item['days_overdue'] >= 30)

        # Prepare alert message
        subject = f"Admin Alert: {total_delinquent} Overdue Loan(s) Requiring Attention"
        
        message_lines = [
            f"ADMIN ALERT: Overdue Loans Report",
            f"Generated on: {today}",
            "",
            f"Summary:",
            f"- Total Delinquent Accounts: {total_delinquent}",
            f"- Total Overdue Amount: ₱{total_overdue_amount:,.2f}",
            f"- Critical (90+ days): {critical_count}",
            f"- Severe (30+ days): {severe_count}",
            "",
            "Delinquent Loans:",
        ]
        
        for item in delinquent_loans[:10]:  # Show top 10
            loan = item['loan']
            message_lines.append(
                f"- Loan #{loan.loan_id}: {loan.application.client.first_name} {loan.application.client.last_name} "
                f"({item['days_overdue']} days overdue, ₱{item['total_overdue']:,.2f})"
            )
        
        if len(delinquent_loans) > 10:
            message_lines.append(f"\n... and {len(delinquent_loans) - 10} more delinquent accounts.")
        
        message_lines.append("\nPlease review the delinquent accounts report for details.")
        message = "\n".join(message_lines)

        # Send alert to all admins
        count = 0
        for admin in admin_users:
            try:
                NotificationService.send_notification(
                    user=admin,
                    subject=subject,
                    message=message,
                    notification_type='system_alert',
                    related_entity_type='system',
                    related_entity_id=0  # System-level alert
                )
                count += 1
                self.stdout.write(f"  Sent alert to {admin.username} ({admin.email})")
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"  Failed to send alert to {admin.username}: {e}"))

        self.stdout.write(self.style.SUCCESS(f"Sent overdue loan alerts to {count} admin(s)."))


