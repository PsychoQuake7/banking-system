from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from .models import Client
from users.decorators import staff_required, admin_required

# Create your views here.
# @staff_required
def client_list_view(request):
    clients = Client.objects.all().order_by('-created_at')
    
    # Search filter
    search_query = request.GET.get('search')
    if search_query:
        from django.db.models import Q
        clients = clients.filter(
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query) |
            Q(user__email__icontains=search_query)
        )
    
    # Status filter
    status = request.GET.get('status')
    if status:
        if status == 'active':
            clients = clients.filter(user__is_active=True)
        elif status == 'inactive':
            clients = clients.filter(user__is_active=False)
            
    # Credit score filter
    credit_score = request.GET.get('credit_score')
    if credit_score:
        if credit_score == 'excellent':
            clients = clients.filter(credit_score__gte=800)
        elif credit_score == 'good':
            clients = clients.filter(credit_score__range=(700, 799))
        elif credit_score == 'fair':
            clients = clients.filter(credit_score__range=(600, 699))
        elif credit_score == 'poor':
            clients = clients.filter(credit_score__lt=600)

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

@admin_required
def client_edit_view(request, id):
    client = get_object_or_404(Client, client_id=id)
    
    if request.method == 'POST':
        # Update Client fields
        client.first_name = request.POST.get('first_name')
        client.last_name = request.POST.get('last_name')
        client.date_of_birth = request.POST.get('date_of_birth')
        client.address = request.POST.get('address')
        client.monthly_income = request.POST.get('monthly_income')
        client.credit_score = request.POST.get('credit_score')
        
        if 'id_document' in request.FILES:
            client.id_document = request.FILES['id_document']
            
        client.save()
        
        # Update User fields
        user = client.user
        user.email = request.POST.get('email')
        user.phone = request.POST.get('phone')
        
        # Handle checkbox for is_active
        user.is_active = request.POST.get('is_active') == 'on'
        user.save()
        
        messages.success(request, f'Client {client.first_name} {client.last_name} updated successfully.')
        return redirect('clients:client_detail', id=client.client_id)

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