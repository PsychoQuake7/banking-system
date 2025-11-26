from django.shortcuts import render

# Create your views here.
def audit_logs_view(request):
    return render(request, 'audit/audit_logs.html')