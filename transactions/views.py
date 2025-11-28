from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .models import Transaction

# Create your views here.
@login_required
def transaction_list_view(request):
    # Base queryset
    if hasattr(request.user, 'client'):
        transactions = Transaction.objects.filter(account__client=request.user.client)
        accounts = request.user.client.accounts.all()
    elif request.user.is_superuser:
        transactions = Transaction.objects.all()
        from accounts.models import Account
        accounts = Account.objects.all()
    else:
        transactions = Transaction.objects.none()
        accounts = []

    # Apply filters
    account_id = request.GET.get('account')
    if account_id:
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

def transaction_create_view(request):
    return render(request, 'transactions/transaction_create.html')

def transfer_create_view(request):
    return render(request, 'transactions/transfer_create.html')