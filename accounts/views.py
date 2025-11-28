from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from .models import Account
from users.decorators import staff_required, require_role

# Create your views here.
@login_required
def account_list_view(request):
    # Staff/Admin can see all accounts, Borrowers only see their own
    if request.user.role in ['admin', 'staff']:
        accounts = Account.objects.all().select_related('client')
    elif hasattr(request.user, 'client'):
        accounts = Account.objects.filter(client=request.user.client).select_related('client')
    else:
        accounts = Account.objects.none()
        
    context = {
        'accounts': accounts,
    }
    return render(request, 'accounts/account_list.html', context)

@login_required
def account_detail_view(request, id):
    account = get_object_or_404(Account, account_id=id)
    
    # Check permission: Owner or Staff/Admin
    is_owner = hasattr(request.user, 'client') and account.client == request.user.client
    is_staff = request.user.role in ['admin', 'staff']
    
    if not (is_owner or is_staff):
        raise PermissionDenied("You do not have permission to view this account.")
        
    transactions = account.transactions.all().order_by('-transaction_date')
    context = {
        'account': account,
        'transactions': transactions,
    }
    return render(request, 'accounts/account_detail.html', context)

@staff_required
def account_create_view(request):
    return render(request, 'accounts/account_create.html')