from django.contrib import admin
from .models import Client

@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = ('client_id', 'first_name', 'last_name', 'user', 'credit_score', 'monthly_income', 'created_at')
    search_fields = ('first_name', 'last_name', 'user__username', 'user__email')
    list_filter = ('credit_score',)
    readonly_fields = ('created_at',)
