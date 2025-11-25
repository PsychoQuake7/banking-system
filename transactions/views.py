from django.shortcuts import render

# Create your views here.
def transaction_list_view(request):
    return render(request, 'transactions/transaction_list.html')

def transaction_create_view(request):
    return render(request, 'transactions/transaction_create.html')

def transfer_create_view(request):
    return render(request, 'transactions/transfer_create.html')