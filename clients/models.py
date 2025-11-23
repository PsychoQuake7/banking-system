from django.db import models
from django.conf import settings

class Client(models.Model):
    client_id = models.AutoField(primary_key=True)
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    date_of_birth = models.DateField()
    address = models.TextField()
    # prefer FileField for uploads rather than storing simple path
    id_document = models.FileField(upload_to='client_documents/', blank=True, null=True)
    credit_score = models.IntegerField(default=0)
    monthly_income = models.DecimalField(max_digits=15, decimal_places=2, default=0.00)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.user.username})"
