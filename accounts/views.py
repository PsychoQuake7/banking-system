from django.shortcuts import render

# Create your views here.
def account_list_view(request):
    return render(request, 'accounts/account_list.html')

def account_detail_view(request):
    return render(request, 'accounts/account_detail.html')

def account_create_view(request):
    return render(request, 'accounts/account_create.html')