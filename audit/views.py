from django.shortcuts import render
from users.decorators import admin_required

# Create your views here.
@admin_required
def audit_logs_view(request):
    return render(request, 'audit/audit_logs.html')