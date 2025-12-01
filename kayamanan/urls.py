from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView, TemplateView
from . import views
from .views import dashboard_view, dashboard_data_api
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # Redirect root URL to dashboard
    path('', RedirectView.as_view(url='/dashboard/', permanent=True)),
    
    path('admin/', admin.site.urls),

    # Main dashboard
    path('dashboard/', dashboard_view, name='dashboard'),
    path('api/dashboard-data/', dashboard_data_api, name='dashboard_data_api'),
    path('profile/', TemplateView.as_view(template_name='profile.html'), name='profile'),

    # Your app URLs
    path('accounts/', include('accounts.urls')),
    path('accounts/', include('allauth.urls')),
    # path('auth/', include('authentication.urls')), # Deprecated in favor of allauth
    path('clients/', include('clients.urls')),
    path('ledger/', include('ledger.urls')),
    path('loans/', include('loans.urls')),
    path('notifications/', include('notifications.urls')),
    path('transactions/', include('transactions.urls')),
    path('audit/', include('audit.urls')),
    path('users/', include('users.urls')),
]

# Serve media files during development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)