from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from .models import Transaction
from users.decorators import staff_required, require_role, borrower_or_staff_required

# Create your views here.
@login_required
def transaction_list_view(request):
    # Only borrowers can view transactions
    if request.user.role != 'borrower':
        raise PermissionDenied("Only borrowers can view transactions.")
    
    # Borrowers see only their own transactions
    if not hasattr(request.user, 'client'):
        # Borrower doesn't have a Client profile
        from django.contrib import messages
        messages.warning(request, "Your client profile is not set up. Please contact support.")
        transactions = Transaction.objects.none()
        accounts = []
    else:
        transactions = Transaction.objects.filter(account__client=request.user.client)
        accounts = request.user.client.accounts.all()

    # Apply filters
    account_id = request.GET.get('account')
    if account_id:
        # If borrower, ensure the account belongs to them
        if request.user.role == 'borrower' and hasattr(request.user, 'client'):
            if not accounts.filter(account_id=account_id).exists():
                raise PermissionDenied("You do not have permission to view transactions for this account.")
        transactions = transactions.filter(account_id=account_id)

    transaction_type = request.GET.get('transaction_type')
    if transaction_type:
        transactions = transactions.filter(transaction_type=transaction_type)

    start_date = request.GET.get('start_date')
    if start_date:
        transactions = transactions.filter(transaction_date__date__gte=start_date)

    end_date = request.GET.get('end_date')
    if end_date:
        transactions = transactions.filter(transaction_date__date__lte=end_date)

    # Order by date
    transactions = transactions.order_by('-transaction_date')

    context = {
        'transactions': transactions,
        'accounts': accounts,
    }
    return render(request, 'transactions/transaction_list.html', context)

@staff_required
def transaction_create_view(request):
    from .forms import TransactionForm
    from accounts.models import Account
    from django.db import transaction as db_transaction
    from django.contrib import messages
    from django.shortcuts import redirect

    if request.method == 'POST':
        form = TransactionForm(request.POST)
        if form.is_valid():
            account_number = form.cleaned_data['account_number']
            transaction_type = form.cleaned_data['transaction_type']
            amount = form.cleaned_data['amount']
            description = form.cleaned_data['description']

            try:
                account = Account.objects.get(account_number=account_number)
                
                if transaction_type == 'withdrawal':
                    account.withdraw(amount, description=description)
                    success_msg = f"Successfully withdrew ₱{amount} from account {account_number}."
                else:
                    account.deposit(amount, description=description)
                    success_msg = f"Successfully deposited ₱{amount} to account {account_number}."

                messages.success(request, success_msg)
                return redirect('transactions:transaction_list')

            except Account.DoesNotExist:
                messages.error(request, f"Account with number {account_number} not found.")
            except ValueError as e:
                # Catch insufficient funds error from withdraw method
                messages.error(request, str(e))
            except Exception as e:
                messages.error(request, f"Transaction failed: {str(e)}")
    else:
        form = TransactionForm()

    return render(request, 'transactions/transaction_create.html', {'form': form})

@login_required
def transfer_create_view(request):
    from .forms import TransferForm
    from accounts.models import Account
    from django.db import transaction as db_transaction
    from django.contrib import messages
    from django.shortcuts import redirect

    if request.method == 'POST':
        form = TransferForm(request.POST, user=request.user)
        if form.is_valid():
            source_account = form.cleaned_data['source_account']
            target_account_number = form.cleaned_data['target_account_number']
            amount = form.cleaned_data['amount']
            description = form.cleaned_data['description']

            if source_account.account_number == target_account_number:
                messages.error(request, "Cannot transfer to the same account.")
                return render(request, 'transactions/transfer_create.html', {'form': form})

            try:
                target_account = Account.objects.get(account_number=target_account_number)
                
                with db_transaction.atomic():
                    # Withdraw from source
                    source_account.withdraw(
                        amount, 
                        description=f"Transfer to {target_account_number}: {description}",
                        transaction_type='withdrawal' # Or 'transfer_out' if we add that type
                    )
                    
                    # Deposit to target
                    target_account.deposit(
                        amount, 
                        description=f"Transfer from {source_account.account_number}: {description}",
                        transaction_type='deposit' # Or 'transfer_in'
                    )
                    
                    messages.success(request, f"Successfully transferred ₱{amount} to {target_account_number}.")
                    return redirect('transactions:transaction_list')

            except Account.DoesNotExist:
                messages.error(request, f"Target account {target_account_number} not found.")
            except ValueError as e:
                messages.error(request, str(e))
            except Exception as e:
                messages.error(request, f"Transfer failed: {str(e)}")
    else:
        form = TransferForm(user=request.user)

    return render(request, 'transactions/transfer_create.html', {'form': form})

@login_required
def deposit_view(request):
    from accounts.models import Account
    from django.contrib import messages
    from django.shortcuts import redirect, get_object_or_404
    from decimal import Decimal
    
    # Only borrowers can make deposits
    if request.user.role != 'borrower':
        raise PermissionDenied("Only borrowers can make deposits.")
    
    # Get user's accounts
    if hasattr(request.user, 'client'):
        accounts = request.user.client.accounts.filter(is_active=True)
    else:
        messages.error(request, "You don't have any accounts.")
        return redirect('dashboard')
    
    if request.method == 'POST':
        account_id = request.POST.get('account')
        amount = request.POST.get('amount')
        description = request.POST.get('description', '')
        
        try:
            amount = Decimal(amount)
            if amount <= 0:
                messages.error(request, "Amount must be greater than zero.")
                return render(request, 'transactions/deposit.html', {'accounts': accounts})
            
            account = get_object_or_404(Account, account_id=account_id)
            
            # Check permission
            if request.user.role == 'borrower':
                if not hasattr(request.user, 'client') or account.client != request.user.client:
                    raise PermissionDenied("You don't have permission to deposit to this account.")
            
            # Make deposit
            transaction = account.deposit(amount, description or f"Deposit of ₱{amount}")
            
            messages.success(request, f"Successfully deposited ₱{amount} to account {account.account_number}. New balance: ₱{account.current_balance}")
            return redirect('accounts:account_detail', id=account.account_id)
            
        except (ValueError, TypeError):
            messages.error(request, "Invalid amount.")
        except Exception as e:
            messages.error(request, f"Error: {str(e)}")
    
    context = {'accounts': accounts}
    return render(request, 'transactions/deposit.html', context)

@login_required
def withdrawal_view(request):
    from accounts.models import Account
    from django.contrib import messages
    from django.shortcuts import redirect, get_object_or_404
    from decimal import Decimal
    
    # Only borrowers can make withdrawals
    if request.user.role != 'borrower':
        raise PermissionDenied("Only borrowers can make withdrawals.")
    
    # Get user's accounts
    if hasattr(request.user, 'client'):
        accounts = request.user.client.accounts.filter(is_active=True)
    else:
        messages.error(request, "You don't have any accounts.")
        return redirect('dashboard')
    
    if request.method == 'POST':
        account_id = request.POST.get('account')
        amount = request.POST.get('amount')
        description = request.POST.get('description', '')
        
        try:
            amount = Decimal(amount)
            if amount <= 0:
                messages.error(request, "Amount must be greater than zero.")
                return render(request, 'transactions/withdrawal.html', {'accounts': accounts})
            
            account = get_object_or_404(Account, account_id=account_id)
            
            # Check permission
            if request.user.role == 'borrower':
                if not hasattr(request.user, 'client') or account.client != request.user.client:
                    raise PermissionDenied("You don't have permission to withdraw from this account.")
            
            # Make withdrawal
            transaction = account.withdraw(amount, description or f"Withdrawal of ₱{amount}")
            
            messages.success(request, f"Successfully withdrew ₱{amount} from account {account.account_number}. New balance: ₱{account.current_balance}")
            return redirect('accounts:account_detail', id=account.account_id)
            
        except ValueError as e:
            messages.error(request, str(e))
        except (TypeError,) as e:
            messages.error(request, "Invalid amount.")
        except Exception as e:
            messages.error(request, f"Error: {str(e)}")
    
    context = {'accounts': accounts}
    return render(request, 'transactions/withdrawal.html', context)