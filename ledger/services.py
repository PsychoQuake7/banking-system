from django.db.models import Sum
from django.utils import timezone
from decimal import Decimal
from .models import GLAccount, LedgerEntry

class FinancialReportService:
    @staticmethod
    def get_income_statement(start_date=None, end_date=None):
        """
        Generate Income Statement data.
        
        Args:
            start_date: Optional start date filter
            end_date: Optional end date filter
            
        Returns:
            dict containing revenues, expenses, totals, and net income
        """
        # Default to all time if no dates provided
        entries_query = LedgerEntry.objects.all()
        
        if start_date:
            entries_query = entries_query.filter(created_at__date__gte=start_date)
        if end_date:
            entries_query = entries_query.filter(created_at__date__lte=end_date)
            
        # Get Revenue Accounts (Type: revenue)
        # For Revenue: Credit increases balance (positive), Debit decreases (negative)
        revenue_accounts = GLAccount.objects.filter(account_type='revenue')
        revenue_data = []
        total_revenue = Decimal('0.00')
        
        for account in revenue_accounts:
            credits = entries_query.filter(gl_account=account, debit_credit='credit').aggregate(Sum('amount'))['amount__sum'] or Decimal('0.00')
            debits = entries_query.filter(gl_account=account, debit_credit='debit').aggregate(Sum('amount'))['amount__sum'] or Decimal('0.00')
            balance = credits - debits
            
            if balance != 0:
                revenue_data.append({
                    'code': account.code,
                    'name': account.name,
                    'balance': balance
                })
                total_revenue += balance
                
        # Get Expense Accounts (Type: expense)
        # For Expense: Debit increases balance (positive), Credit decreases (negative)
        expense_accounts = GLAccount.objects.filter(account_type='expense')
        expense_data = []
        total_expenses = Decimal('0.00')
        
        for account in expense_accounts:
            debits = entries_query.filter(gl_account=account, debit_credit='debit').aggregate(Sum('amount'))['amount__sum'] or Decimal('0.00')
            credits = entries_query.filter(gl_account=account, debit_credit='credit').aggregate(Sum('amount'))['amount__sum'] or Decimal('0.00')
            balance = debits - credits
            
            if balance != 0:
                expense_data.append({
                    'code': account.code,
                    'name': account.name,
                    'balance': balance
                })
                total_expenses += balance
                
        net_income = total_revenue - total_expenses
        
        return {
            'revenues': revenue_data,
            'expenses': expense_data,
            'total_revenue': total_revenue,
            'total_expenses': total_expenses,
            'net_income': net_income,
            'generated_at': timezone.now()
        }

    @staticmethod
    def get_balance_sheet(as_of_date=None):
        """
        Generate Balance Sheet data.
        Assets = Liabilities + Equity
        """
        if as_of_date is None:
            as_of_date = timezone.now().date()
            
        # Helper to get account balances
        def get_accounts(account_type):
            accounts = GLAccount.objects.filter(account_type=account_type)
            data = []
            total = Decimal('0.00')
            
            for acc in accounts:
                # Calculate balance up to date
                # For Assets/Expenses: Debit increases, Credit decreases
                # For Liab/Equity/Revenue: Credit increases, Debit decreases
                
                debits = LedgerEntry.objects.filter(
                    gl_account=acc,
                    created_at__date__lte=as_of_date,
                    debit_credit='debit'
                ).aggregate(Sum('amount'))['amount__sum'] or Decimal('0.00')
                
                credits = LedgerEntry.objects.filter(
                    gl_account=acc,
                    created_at__date__lte=as_of_date,
                    debit_credit='credit'
                ).aggregate(Sum('amount'))['amount__sum'] or Decimal('0.00')
                
                if account_type in ['asset', 'expense']:
                    balance = debits - credits
                else:
                    balance = credits - debits
                    
                if balance != 0:
                    data.append({
                        'name': acc.name,
                        'code': acc.code,
                        'balance': balance
                    })
                    total += balance
            
            return data, total

        assets, total_assets = get_accounts('asset')
        liabilities, total_liabilities = get_accounts('liability')
        equity, total_equity = get_accounts('equity')
        
        # Calculate Current Year Earnings (Revenue - Expenses) to balance the sheet
        # This is effectively "Retained Earnings" for the period
        revenue_data, total_revenue = get_accounts('revenue')
        expense_data, total_expenses = get_accounts('expense')
        current_earnings = total_revenue - total_expenses
        
        if current_earnings != 0:
            equity.append({
                'name': 'Current Year Earnings',
                'code': 'RE-CY',
                'balance': current_earnings
            })
            total_equity += current_earnings
            
        return {
            'assets': assets,
            'total_assets': total_assets,
            'liabilities': liabilities,
            'total_liabilities': total_liabilities,
            'equity': equity,
            'total_equity': total_equity,
            'total_liabilities_equity': total_liabilities + total_equity,
            'as_of_date': as_of_date
        }
