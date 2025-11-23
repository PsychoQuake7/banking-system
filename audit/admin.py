from django.contrib import admin
from .models import AuditLog

@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ('log_id','user','action','timestamp','ip_address')
    search_fields = ('user__username','action','ip_address')
    readonly_fields = ('timestamp',)
