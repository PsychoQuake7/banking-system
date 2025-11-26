from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView
from kayamanan.views import dashboard_view

urlpatterns = [
    # Redirect root URL to dashboard
    path('', RedirectView.as_view(url='/dashboard/', permanent=True)),
    
    path('admin/', admin.site.urls),

    # Main dashboard
    path('dashboard/', dashboard_view, name='dashboard'),

    # Your app URLs
    path('accounts/', include('accounts.urls')),
    path('auth/', include('authentication.urls')),
    path('clients/', include('clients.urls')),
    path('loans/', include('loans.urls')),
    path('notifications/', include('notifications.urls')),
    path('transactions/', include('transactions.urls')),
    path('audit/', include('audit.urls')),
]