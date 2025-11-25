from django.shortcuts import render

# Create your views here.
def client_list_view(request):
    return render(request, 'clients/client_list.html')

def client_detail_view(request):
    return render(request, 'clients/client_detail.html')

def client_edit_view(request):
    return render(request, 'clients/client_edit.html')