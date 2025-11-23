from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Transaction
from accounts.models import Account

@receiver(post_save, sender=Transaction)
def update_account_balance(sender, instance, created, **kwargs):
    if not created:
        return
    account = instance.account
    if instance.transaction_type == 'deposit' or instance.transaction_type == 'payment' or instance.transaction_type == 'disbursement':
        # NOTE: disbursement logic depends (disbursement may subtract or add depending on flow)
        account.current_balance = account.current_balance + instance.amount
    elif instance.transaction_type == 'withdrawal':
        account.current_balance = account.current_balance - instance.amount
    account.save()
