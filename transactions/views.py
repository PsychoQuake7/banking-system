from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from .models import Transaction
from users.decorators import staff_required, require_role

# Create your views here.
@login_required
def transaction_list_view(request):
    # Base queryset
    if request.user.role in ['admin', 'staff']:
        # Staff/Admin see all transactions
        transactions = Transaction.objects.all()
        from accounts.models import Account
        accounts = Account.objects.all()
    elif hasattr(request.user, 'client'):
        # Borrowers see only their own transactions
        transactions = Transaction.objects.filter(account__client=request.user.client)
        accounts = request.user.client.accounts.all()
    else:
        transactions = Transaction.objects.none()
        accounts = []

    # Apply filters
    account_id = request.GET.get('account')
    if account_id:
        # If borrower, ensure the account belongs to them
        if request.user.role == 'borrower':
            if not accounts.filter(account_id=account_id).exists():
                raise PermissionDenied("You do not have permission to view transactions for this account.")
        transactions = transactions.filter(account_id=account_id)

    transaction_type = request.GET.get('transaction_type')
    if transaction_type:
        transactions = transactions.filter(transaction_type=transaction_type)

    start_date = request.GET.get('start_date')
    if start_date:
        transactions = transactions.filter(transaction_date__date__gte=start_date)

    end_date = request.GET.get('end_date')
    if end_date:
        transactions = transactions.filter(transaction_date__date__lte=end_date)

    # Order by date
    transactions = transactions.order_by('-transaction_date')

    context = {
        'transactions': transactions,
        'accounts': accounts,
    }
    return render(request, 'transactions/transaction_list.html', context)

@staff_required
def transaction_create_view(request):
    # This view handles deposits and withdrawals, which are staff operations
    return render(request, 'transactions/transaction_create.html')

@login_required
def transfer_create_view(request):
    # Borrowers can transfer, but logic (in form/post) must validate source account ownership
    return render(request, 'transactions/transfer_create.html')