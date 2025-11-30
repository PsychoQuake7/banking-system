from django.core.management.base import BaseCommand
from django.db import transaction
from ledger.models import GLAccount, LedgerEntry
from transactions.models import Transaction
from decimal import Decimal

class Command(BaseCommand):
    help = 'Initialize GL Accounts and backfill ledger entries from existing transactions'

    def handle(self, *args, **options):
        self.stdout.write('Initializing Ledger System...')

        # 1. Create GL Accounts
        GL_ACCOUNTS = [
            {
                'name': 'Cash Vault',
                'code': '1001',
                'account_type': 'asset',
                'description': 'Physical cash and bank reserves'
            },
            {
                'name': 'Loan Receivable',
                'code': '1002',
                'account_type': 'asset',
                'description': 'Principal amount owed by borrowers'
            },
            {
                'name': 'Client Deposits',
                'code': '2001',
                'account_type': 'liability',
                'description': 'Total funds held in client accounts'
            },
            {
                'name': 'Interest Income',
                'code': '4001',
                'account_type': 'revenue',
                'description': 'Income generated from loan interest'
            },
        ]

        for acc_data in GL_ACCOUNTS:
            obj, created = GLAccount.objects.get_or_create(
                code=acc_data['code'],
                defaults=acc_data
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f"Created GL Account: {obj}"))
            else:
                self.stdout.write(f"GL Account already exists: {obj}")

        # 2. Backfill Transactions
        self.stdout.write('Backfilling ledger entries...')
        
        transactions = Transaction.objects.filter(ledger_entries__isnull=True)
        count = 0
        
        # Get GL Account instances
        cash_vault = GLAccount.objects.get(code='1001')
        loan_receivable = GLAccount.objects.get(code='1002')
        client_deposits = GLAccount.objects.get(code='2001')
        
        with transaction.atomic():
            for trans in transactions:
                if trans.transaction_type == 'deposit':
                    # Debit Cash Vault, Credit Client Deposits
                    LedgerEntry.objects.create(
                        transaction_ref=trans,
                        gl_account=cash_vault,
                        amount=trans.amount,
                        debit_credit='debit',
                        description=f"Backfill: Deposit to {trans.account.account_number}",
                        created_at=trans.transaction_date
                    )
                    LedgerEntry.objects.create(
                        transaction_ref=trans,
                        gl_account=client_deposits,
                        client_account=trans.account,
                        amount=trans.amount,
                        debit_credit='credit',
                        description=f"Backfill: Deposit from Client",
                        created_at=trans.transaction_date
                    )
                    
                elif trans.transaction_type == 'withdrawal':
                    # Debit Client Deposits, Credit Cash Vault
                    LedgerEntry.objects.create(
                        transaction_ref=trans,
                        gl_account=client_deposits,
                        client_account=trans.account,
                        amount=trans.amount,
                        debit_credit='debit',
                        description=f"Backfill: Withdrawal from {trans.account.account_number}",
                        created_at=trans.transaction_date
                    )
                    LedgerEntry.objects.create(
                        transaction_ref=trans,
                        gl_account=cash_vault,
                        amount=trans.amount,
                        debit_credit='credit',
                        description=f"Backfill: Withdrawal by Client",
                        created_at=trans.transaction_date
                    )
                    
                elif trans.transaction_type == 'disbursement':
                    # Debit Loan Receivable, Credit Client Deposits
                    LedgerEntry.objects.create(
                        transaction_ref=trans,
                        gl_account=loan_receivable,
                        amount=trans.amount,
                        debit_credit='debit',
                        description=f"Backfill: Loan Disbursement",
                        created_at=trans.transaction_date
                    )
                    LedgerEntry.objects.create(
                        transaction_ref=trans,
                        gl_account=client_deposits,
                        client_account=trans.account,
                        amount=trans.amount,
                        debit_credit='credit',
                        description=f"Backfill: Loan Proceeds",
                        created_at=trans.transaction_date
                    )
                    
                elif trans.transaction_type == 'payment':
                    # Debit Client Deposits, Credit Loan Receivable
                    LedgerEntry.objects.create(
                        transaction_ref=trans,
                        gl_account=client_deposits,
                        client_account=trans.account,
                        amount=trans.amount,
                        debit_credit='debit',
                        description=f"Backfill: Loan Payment",
                        created_at=trans.transaction_date
                    )
                    LedgerEntry.objects.create(
                        transaction_ref=trans,
                        gl_account=loan_receivable,
                        amount=trans.amount,
                        debit_credit='credit',
                        description=f"Backfill: Loan Repayment",
                        created_at=trans.transaction_date
                    )
                
                count += 1
                
        self.stdout.write(self.style.SUCCESS(f'Successfully backfilled {count} transactions.'))
