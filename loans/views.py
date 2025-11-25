from django.shortcuts import render

# Create your views here.
def loan_list_view(request):
    return render(request, 'loans/loan_list.html')

def loan_detail_view(request):
    return render(request, 'loans/loan_detail.html')

def loan_application_view(request):
    return render(request, 'loans/loan_application.html')

def loan_application_list_view(request):
    return render(request, 'loans/loan_application_list.html')

def make_payment_view(request):
    return render(request, 'loans/make_payment.html')

def amortization_schedule_view(request):
    return render(request, 'loans/amortization_schedule.html')