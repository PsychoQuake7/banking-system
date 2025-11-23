from django.contrib import admin
from .models import Account, InterestAccrual

@admin.register(Account)
class AccountAdmin(admin.ModelAdmin):
    list_display = ('account_id','account_number','client','account_type','current_balance','is_active','created_at')
    search_fields = ('account_number','client__first_name','client__last_name','client__user__username')
    list_filter = ('account_type','is_active')

@admin.register(InterestAccrual)
class InterestAccrualAdmin(admin.ModelAdmin):
    list_display = ('accrual_id','account','accrual_date','interest_earned','is_compounded')
    list_filter = ('is_compounded',)
    search_fields = ('account__account_number',)
