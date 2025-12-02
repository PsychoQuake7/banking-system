from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from .models import Account
from users.decorators import staff_required, require_role, borrower_or_staff_required

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

@borrower_or_staff_required
def account_create_view(request):
    from django.shortcuts import redirect
    from django.contrib import messages
    from decimal import Decimal
    import random
    import string
    
    if request.method == 'POST':
        account_type = request.POST.get('account_type')
        initial_deposit = request.POST.get('initial_deposit')
        terms = request.POST.get('terms')
        
        # Validate inputs
        if not terms:
            messages.error(request, "You must agree to the terms and conditions.")
            return render(request, 'accounts/account_create.html')
        
        try:
            initial_deposit = Decimal(initial_deposit)
            if initial_deposit < 500:
                messages.error(request, "Minimum initial deposit is ₱500.")
                return render(request, 'accounts/account_create.html')
        except (ValueError, TypeError):
            messages.error(request, "Invalid deposit amount.")
            return render(request, 'accounts/account_create.html')
        
        # Check if user has a client profile
        if not hasattr(request.user, 'client'):
            messages.error(request, "You must have a client profile to open an account. Please contact support.")
            return redirect('accounts:account_list')
        
        # Generate unique account number
        while True:
            account_number = ''.join(random.choices(string.digits, k=10))
            if not Account.objects.filter(account_number=account_number).exists():
                break
        
        # Set interest rate based on account type
        interest_rate = Decimal('2.5') if account_type == 'savings' else Decimal('0.0')
        
        # Create the account
        account = Account.objects.create(
            client=request.user.client,
            account_number=account_number,
            account_type=account_type,
            current_balance=initial_deposit,
            interest_rate=interest_rate,
            is_active=True
        )
        
        messages.success(request, f"Account {account_number} created successfully with initial deposit of ₱{initial_deposit}!")
        return redirect('accounts:account_detail', id=account.account_id)
    
    return render(request, 'accounts/account_create.html')