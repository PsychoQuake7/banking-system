from django.db.models.signals import post_save
from django.dispatch import receiver
from django.db import transaction
from transactions.models import Transaction
from .models import LedgerEntry, GLAccount

@receiver(post_save, sender=Transaction)
def create_ledger_entries(sender, instance, created, **kwargs):
    """
    Automatically create ledger entries when a Transaction is created.
    """
    if not created:
        return

    # Define GL Account Codes (ensure these exist via init_ledger command)
    GL_CODES = {
        'CASH_VAULT': '1001',      # Asset
        'LOAN_RECEIVABLE': '1002', # Asset
        'CLIENT_DEPOSITS': '2001', # Liability
        'INTEREST_INCOME': '4001', # Revenue
    }

    try:
        # Get GL Accounts
        cash_vault = GLAccount.objects.get(code=GL_CODES['CASH_VAULT'])
        client_deposits = GLAccount.objects.get(code=GL_CODES['CLIENT_DEPOSITS'])
        loan_receivable = GLAccount.objects.get(code=GL_CODES['LOAN_RECEIVABLE'])
        # interest_income = GLAccount.objects.get(code=GL_CODES['INTEREST_INCOME']) # For future use

        description = instance.description or f"{instance.get_transaction_type_display()} - {instance.transaction_id}"

        with transaction.atomic():
            if instance.transaction_type == 'deposit':
                # Debit Cash Vault (Asset Increase)
                LedgerEntry.objects.create(
                    transaction_ref=instance,
                    gl_account=cash_vault,
                    amount=instance.amount,
                    debit_credit='debit',
                    description=f"Deposit to {instance.account.account_number}"
                )
                # Credit Client Deposits (Liability Increase)
                LedgerEntry.objects.create(
                    transaction_ref=instance,
                    gl_account=client_deposits,
                    client_account=instance.account,
                    amount=instance.amount,
                    debit_credit='credit',
                    description=f"Deposit from Client"
                )

            elif instance.transaction_type == 'withdrawal':
                # Debit Client Deposits (Liability Decrease)
                LedgerEntry.objects.create(
                    transaction_ref=instance,
                    gl_account=client_deposits,
                    client_account=instance.account,
                    amount=instance.amount,
                    debit_credit='debit',
                    description=f"Withdrawal from {instance.account.account_number}"
                )
                # Credit Cash Vault (Asset Decrease)
                LedgerEntry.objects.create(
                    transaction_ref=instance,
                    gl_account=cash_vault,
                    amount=instance.amount,
                    debit_credit='credit',
                    description=f"Withdrawal by Client"
                )

            elif instance.transaction_type == 'disbursement':
                # Debit Loan Receivable (Asset Increase)
                LedgerEntry.objects.create(
                    transaction_ref=instance,
                    gl_account=loan_receivable,
                    amount=instance.amount,
                    debit_credit='debit',
                    description=f"Loan Disbursement for Loan #{instance.loan.loan_id if instance.loan else 'N/A'}"
                )
                # Credit Client Deposits (Liability Increase - money goes to client account)
                LedgerEntry.objects.create(
                    transaction_ref=instance,
                    gl_account=client_deposits,
                    client_account=instance.account,
                    amount=instance.amount,
                    debit_credit='credit',
                    description=f"Loan Proceeds to {instance.account.account_number}"
                )

            elif instance.transaction_type == 'payment':
                # Debit Client Deposits (Liability Decrease - money taken from client account)
                LedgerEntry.objects.create(
                    transaction_ref=instance,
                    gl_account=client_deposits,
                    client_account=instance.account,
                    amount=instance.amount,
                    debit_credit='debit',
                    description=f"Loan Payment from {instance.account.account_number}"
                )
                # Credit Loan Receivable (Asset Decrease)
                LedgerEntry.objects.create(
                    transaction_ref=instance,
                    gl_account=loan_receivable,
                    amount=instance.amount,
                    debit_credit='credit',
                    description=f"Loan Repayment for Loan #{instance.loan.loan_id if instance.loan else 'N/A'}"
                )
                
                # Note: Interest split logic would go here if we separated principal/interest in Transaction model

    except GLAccount.DoesNotExist:
        # Log error or handle gracefully if GL accounts aren't initialized
        print("Error: GL Accounts not initialized. Cannot create ledger entries.")
