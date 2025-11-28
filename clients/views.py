from django.shortcuts import render, get_object_or_404
from .models import Client

# Create your views here.
def client_list_view(request):
    clients = Client.objects.all().order_by('-created_at')
    context = {
        'clients': clients,
    }
    return render(request, 'clients/client_list.html', context)

def client_detail_view(request, id):
    client = get_object_or_404(Client, client_id=id)
    accounts = client.accounts.all()
    loans = client.loan_applications.filter(loan__isnull=False).select_related('loan')
    context = {
        'client': client,
        'accounts': accounts,
        'loans': [app.loan for app in loans],
    }
    return render(request, 'clients/client_detail.html', context)

def client_edit_view(request, id):
    client = get_object_or_404(Client, client_id=id)
    context = {
        'client': client,
    }
    return render(request, 'clients/client_edit.html', context)