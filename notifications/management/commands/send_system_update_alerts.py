from django.core.management.base import BaseCommand
from django.utils import timezone
from notifications.services import NotificationService
from users.models import CustomUser
import subprocess
import sys

class Command(BaseCommand):
    help = 'Send admin alerts for system updates (e.g., security patches, maintenance)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--message',
            type=str,
            help='Custom message for the system update alert',
        )
        parser.add_argument(
            '--subject',
            type=str,
            help='Custom subject for the system update alert',
        )
        parser.add_argument(
            '--type',
            type=str,
            choices=['maintenance', 'security', 'update', 'general'],
            default='general',
            help='Type of system update alert',
        )

    def handle(self, *args, **options):
        today = timezone.now()
        self.stdout.write(f"Sending system update alerts on {today.date()}...")

        # Get all admin users
        admin_users = CustomUser.objects.filter(role='admin', is_active=True)
        
        if not admin_users.exists():
            self.stdout.write(self.style.WARNING("No admin users found. Skipping alerts."))
            return

        # Determine subject and message
        if options['subject']:
            subject = options['subject']
        else:
            subject_map = {
                'maintenance': 'System Maintenance Scheduled',
                'security': 'Security Update Required',
                'update': 'System Update Available',
                'general': 'System Update Notification'
            }
            subject = subject_map.get(options['type'], 'System Update Notification')

        if options['message']:
            message = options['message']
        else:
            # Default messages based on type
            default_messages = {
                'maintenance': (
                    f"System Maintenance Notification\n\n"
                    f"A scheduled maintenance window has been planned. "
                    f"Please review the maintenance schedule and inform affected users.\n\n"
                    f"Date: {today.date()}\n"
                    f"Time: {today.time()}"
                ),
                'security': (
                    f"Security Update Alert\n\n"
                    f"A security update is available and should be applied as soon as possible. "
                    f"Please review and apply the security patch.\n\n"
                    f"Date: {today.date()}\n"
                    f"Time: {today.time()}"
                ),
                'update': (
                    f"System Update Available\n\n"
                    f"A new system update is available. Please review the changelog and schedule "
                    f"the update at your convenience.\n\n"
                    f"Date: {today.date()}\n"
                    f"Time: {today.time()}"
                ),
                'general': (
                    f"System Update Notification\n\n"
                    f"This is a general system update notification. Please review the system "
                    f"status and any pending updates.\n\n"
                    f"Date: {today.date()}\n"
                    f"Time: {today.time()}"
                )
            }
            message = default_messages.get(options['type'], default_messages['general'])

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

        self.stdout.write(self.style.SUCCESS(f"Sent system update alerts to {count} admin(s)."))

