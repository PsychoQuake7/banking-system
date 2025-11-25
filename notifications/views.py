from django.shortcuts import render

# Create your views here.
def notification_list_view(request):
    return render(request, 'notifications/notification_list.html')

def notification_settings_view(request):
    return render(request, 'notifications/notification_settings.html')