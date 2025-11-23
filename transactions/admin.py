from django.contrib import admin
from .models import Transaction

@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ('transaction_id','account','transaction_type','amount','transaction_date','loan')
    search_fields = ('account__account_number','loan__loan_id')
    list_filter = ('transaction_type','transaction_date')
