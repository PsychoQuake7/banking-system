from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView, TemplateView
from kayamanan.views import dashboard_view

urlpatterns = [
    # Redirect root URL to dashboard
    path('', RedirectView.as_view(url='/dashboard/', permanent=True)),
    
    path('admin/', admin.site.urls),

    # Main dashboard
    path('dashboard/', dashboard_view, name='dashboard'),
    path('profile/', TemplateView.as_view(template_name='profile.html'), name='profile'),

    # Your app URLs
    path('accounts/', include('accounts.urls')),
    path('accounts/', include('allauth.urls')),
    # path('auth/', include('authentication.urls')), # Deprecated in favor of allauth
    path('clients/', include('clients.urls')),
    path('loans/', include('loans.urls')),
    path('notifications/', include('notifications.urls')),
    path('transactions/', include('transactions.urls')),
    path('audit/', include('audit.urls')),
]