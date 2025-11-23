from django.contrib import admin
from .models import LoanApplication, Loan, AmortizationSchedule

@admin.register(LoanApplication)
class LoanApplicationAdmin(admin.ModelAdmin):
    list_display = ('application_id','client','loan_officer','loan_amount','status','application_date','approval_date')
    list_filter = ('status',)
    search_fields = ('client__first_name','client__last_name','loan_officer__username')

@admin.register(Loan)
class LoanAdmin(admin.ModelAdmin):
    list_display = ('loan_id','application','loan_amount','interest_rate','term_months','start_date','end_date','remaining_balance','status')
    search_fields = ('application__client__first_name','application__client__last_name')

@admin.register(AmortizationSchedule)
class AmortizationScheduleAdmin(admin.ModelAdmin):
    list_display = ('schedule_id','loan','installment_number','due_date','total_payment','status')
    list_filter = ('status',)
    search_fields = ('loan__loan_id',)
