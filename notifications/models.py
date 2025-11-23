from django.db import models
from django.conf import settings

class Notification(models.Model):
    TYPE = [('email','Email'),('sms','SMS')]
    NOTIF_TYPES = [
        ('payment_reminder','Payment Reminder'),
        ('loan_approved','Loan Approved'),
        ('due_date','Due Date'),
        ('system_alert','System Alert'),
    ]
    ENTITY_TYPE = [('loan','loan'),('account','account'),('system','system')]

    notification_id = models.AutoField(primary_key=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notifications')
    type = models.CharField(max_length=10, choices=TYPE)
    notification_type = models.CharField(max_length=50, choices=NOTIF_TYPES)
    related_entity_type = models.CharField(max_length=20, choices=ENTITY_TYPE)
    related_entity_id = models.IntegerField()  # polymorphic reference — keep numeric
    subject = models.CharField(max_length=255)
    message = models.TextField()
    sent_date = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=[('sent','Sent'),('pending','Pending'),('failed','Failed')], default='pending')

    def __str__(self):
        return f"{self.notification_type} to {self.user.username} - {self.status}"
