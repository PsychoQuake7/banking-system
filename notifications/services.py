from django.core.mail import send_mail
from django.conf import settings
from .models import Notification
import logging

logger = logging.getLogger(__name__)

class NotificationService:
    @staticmethod
    def send_notification(user, subject, message, notification_type, related_entity_type, related_entity_id):
        """
        Send a notification to a user via Email and SMS (if available).
        Creates a Notification record for each channel.
        """
        
        # 1. Send Email
        if user.email:
            try:
                NotificationService._send_email(user, subject, message)
                Notification.objects.create(
                    user=user,
                    type='email',
                    notification_type=notification_type,
                    related_entity_type=related_entity_type,
                    related_entity_id=related_entity_id,
                    subject=subject,
                    message=message,
                    status='sent'
                )
            except Exception as e:
                logger.error(f"Failed to send email to {user.email}: {e}")
                Notification.objects.create(
                    user=user,
                    type='email',
                    notification_type=notification_type,
                    related_entity_type=related_entity_type,
                    related_entity_id=related_entity_id,
                    subject=subject,
                    message=message,
                    status='failed'
                )
        else:
            logger.warning(f"Skipping email notification for {user.username}: No email address.")

        # 2. Send SMS (Mock)
        # In a real app, check if user has phone number and opted in
        phone = getattr(user, 'phone', None)
        if phone:
            try:
                NotificationService._send_sms(user, message)
                Notification.objects.create(
                    user=user,
                    type='sms',
                    notification_type=notification_type,
                    related_entity_type=related_entity_type,
                    related_entity_id=related_entity_id,
                    subject="SMS Notification", # SMS usually doesn't have subject
                    message=message,
                    status='sent'
                )
            except Exception as e:
                logger.error(f"Failed to send SMS to {user}: {e}")
                Notification.objects.create(
                    user=user,
                    type='sms',
                    notification_type=notification_type,
                    related_entity_type=related_entity_type,
                    related_entity_id=related_entity_id,
                    subject="SMS Notification",
                    message=message,
                    status='failed'
                )
        else:
            logger.warning(f"Skipping SMS notification for {user.username}: No phone number.")

    @staticmethod
    def _send_email(user, subject, message):
        if not user.email:
            logger.warning(f"User {user.username} has no email address.")
            return

        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=False,
        )
        logger.info(f"Email sent to {user.email}: {subject}")

    @staticmethod
    def _send_sms(user, message):
        """
        Mock SMS sender.
        """
        # In production, integrate with Twilio, Chikka, etc.
        # For now, just log it.
        phone = getattr(user, 'phone', 'N/A') # Assuming user profile might have phone
        logger.info(f"--------------------------------------------------")
        logger.info(f" [MOCK SMS GATEWAY] To: {user.username} ({phone})")
        logger.info(f" Message: {message}")
        logger.info(f"--------------------------------------------------")
