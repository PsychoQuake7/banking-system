import os
import django
from django.conf import settings
from django.template.loader import render_to_string
from django.test import RequestFactory

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kayamanan.settings')
django.setup()

from clients.models import Client

def reproduce():
    factory = RequestFactory()
    request = factory.get('/clients/')
    request.user = type('User', (object,), {'is_authenticated': True, 'role': 'admin', 'username': 'admin'})()
    
    clients = Client.objects.all()
    context = {'clients': clients, 'request': request}
    
    try:
        render_to_string('clients/client_list.html', context)
        print("Template rendered successfully")
    except Exception as e:
        print(f"Caught exception: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    reproduce()
