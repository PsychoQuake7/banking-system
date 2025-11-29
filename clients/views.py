from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from .models import Client
from users.decorators import staff_required, admin_required

# Create your views here.
# @staff_required
def client_list_view(request):
    clients = Client.objects.all().order_by('-created_at')
    context = {
        'clients': clients,
    }
    return render(request, 'clients/client_list.html', context)

@staff_required
def client_detail_view(request, id):
    client = get_object_or_404(Client, client_id=id)
    accounts = client.accounts.all()
    loans = client.loan_applications.filter(loan__isnull=False).select_related('loan')
    from loans.utils import calculate_eligibility_score
    eligibility_data = calculate_eligibility_score(client)
    
    context = {
        'client': client,
        'accounts': accounts,
        'loans': [app.loan for app in loans],
        'eligibility_data': eligibility_data,
    }
    return render(request, 'clients/client_detail.html', context)

@staff_required
def client_edit_view(request, id):
    client = get_object_or_404(Client, client_id=id)
    context = {
        'client': client,
    }
    return render(request, 'clients/client_edit.html', context)

@admin_required
def toggle_user_status(request, id):
    """View to toggle user active status (Deactivate/Activate)"""
    client = get_object_or_404(Client, client_id=id)
    user = client.user
    
    # Toggle status
    user.is_active = not user.is_active
    user.save()
    
    status_msg = "activated" if user.is_active else "deactivated"
    messages.success(request, f"User {user.username} has been {status_msg}.")
    
    return redirect('clients:client_list')