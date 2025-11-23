from django.contrib import admin
from .models import Notification

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('notification_id','user','notification_type','type','sent_date','status')
    list_filter = ('notification_type','type','status')
    search_fields = ('user__username','subject')
