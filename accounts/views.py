from django.shortcuts import render, get_object_or_404
from .models import Account

# Create your views here.
def account_list_view(request):
    accounts = Account.objects.all().select_related('client')
    context = {
        'accounts': accounts,
    }
    return render(request, 'accounts/account_list.html', context)

def account_detail_view(request, id):
    account = get_object_or_404(Account, account_id=id)
    transactions = account.transactions.all().order_by('-transaction_date')
    context = {
        'account': account,
        'transactions': transactions,
    }
    return render(request, 'accounts/account_detail.html', context)

def account_create_view(request):
    return render(request, 'accounts/account_create.html')