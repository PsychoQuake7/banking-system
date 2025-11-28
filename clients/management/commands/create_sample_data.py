from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from decimal import Decimal
from datetime import datetime, timedelta
import random

from clients.models import Client
from accounts.models import Account, InterestAccrual
from loans.models import LoanApplication, Loan, AmortizationSchedule
from transactions.models import Transaction

User = get_user_model()


class Command(BaseCommand):
    help = 'Generate sample data for testing the banking system'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing data before generating new data',
        )

    def handle(self, *args, **options):
        if options['clear']:
            self.stdout.write('Clearing existing data...')
            Transaction.objects.all().delete()
            AmortizationSchedule.objects.all().delete()
            Loan.objects.all().delete()
            LoanApplication.objects.all().delete()
            InterestAccrual.objects.all().delete()
            Account.objects.all().delete()
            Client.objects.all().delete()
            # Don't delete the admin user
            User.objects.exclude(username='admin').delete()
            self.stdout.write(self.style.SUCCESS('Existing data cleared!'))

        self.stdout.write('Generating sample data...')

        # Generate users and clients
        clients = self.create_clients()
        self.stdout.write(self.style.SUCCESS(f'Created {len(clients)} clients'))

        # Generate accounts
        accounts = self.create_accounts(clients)
        self.stdout.write(self.style.SUCCESS(f'Created {len(accounts)} accounts'))

        # Generate transactions
        transactions = self.create_transactions(accounts)
        self.stdout.write(self.style.SUCCESS(f'Created {len(transactions)} transactions'))

        # Generate loan applications
        loan_apps = self.create_loan_applications(clients)
        self.stdout.write(self.style.SUCCESS(f'Created {len(loan_apps)} loan applications'))

        # Generate loans
        loans = self.create_loans(loan_apps)
        self.stdout.write(self.style.SUCCESS(f'Created {len(loans)} loans'))

        # Generate loan payments
        loan_payments = self.create_loan_payments(loans, accounts)
        self.stdout.write(self.style.SUCCESS(f'Created {len(loan_payments)} loan payments'))

        self.stdout.write(self.style.SUCCESS('Sample data generation complete!'))

    def create_clients(self):
        """Create sample clients with diverse profiles"""
        clients_data = [
            {
                'username': 'juan.delacruz',
                'email': 'juan.delacruz@example.com',
                'first_name': 'Juan',
                'last_name': 'Dela Cruz',
                'dob': '1985-03-15',
                'address': '123 Rizal Street, Makati City, Metro Manila',
                'credit_score': 750,
                'monthly_income': Decimal('45000.00'),
            },
            {
                'username': 'maria.santos',
                'email': 'maria.santos@example.com',
                'first_name': 'Maria',
                'last_name': 'Santos',
                'dob': '1990-07-22',
                'address': '456 Bonifacio Avenue, Quezon City, Metro Manila',
                'credit_score': 820,
                'monthly_income': Decimal('65000.00'),
            },
            {
                'username': 'pedro.reyes',
                'email': 'pedro.reyes@example.com',
                'first_name': 'Pedro',
                'last_name': 'Reyes',
                'dob': '1978-11-08',
                'address': '789 Mabini Street, Pasig City, Metro Manila',
                'credit_score': 680,
                'monthly_income': Decimal('38000.00'),
            },
            {
                'username': 'ana.garcia',
                'email': 'ana.garcia@example.com',
                'first_name': 'Ana',
                'last_name': 'Garcia',
                'dob': '1995-02-14',
                'address': '321 Luna Street, Taguig City, Metro Manila',
                'credit_score': 710,
                'monthly_income': Decimal('52000.00'),
            },
            {
                'username': 'jose.mendoza',
                'email': 'jose.mendoza@example.com',
                'first_name': 'Jose',
                'last_name': 'Mendoza',
                'dob': '1982-09-30',
                'address': '654 Del Pilar Street, Manila City, Metro Manila',
                'credit_score': 640,
                'monthly_income': Decimal('35000.00'),
            },
            {
                'username': 'rosa.flores',
                'email': 'rosa.flores@example.com',
                'first_name': 'Rosa',
                'last_name': 'Flores',
                'dob': '1988-05-18',
                'address': '987 Aguinaldo Highway, Cavite',
                'credit_score': 780,
                'monthly_income': Decimal('58000.00'),
            },
            {
                'username': 'carlos.ramos',
                'email': 'carlos.ramos@example.com',
                'first_name': 'Carlos',
                'last_name': 'Ramos',
                'dob': '1992-12-25',
                'address': '147 Roxas Boulevard, Pasay City, Metro Manila',
                'credit_score': 690,
                'monthly_income': Decimal('42000.00'),
            },
            {
                'username': 'elena.cruz',
                'email': 'elena.cruz@example.com',
                'first_name': 'Elena',
                'last_name': 'Cruz',
                'dob': '1987-04-10',
                'address': '258 Quezon Avenue, Quezon City, Metro Manila',
                'credit_score': 800,
                'monthly_income': Decimal('72000.00'),
            },
        ]

        clients = []
        for data in clients_data:
            user = User.objects.create_user(
                username=data['username'],
                email=data['email'],
                password='password123',
                first_name=data['first_name'],
                last_name=data['last_name'],
            )
            client = Client.objects.create(
                user=user,
                first_name=data['first_name'],
                last_name=data['last_name'],
                date_of_birth=datetime.strptime(data['dob'], '%Y-%m-%d').date(),
                address=data['address'],
                credit_score=data['credit_score'],
                monthly_income=data['monthly_income'],
            )
            clients.append(client)

        return clients

    def create_accounts(self, clients):
        """Create multiple accounts for clients"""
        accounts = []
        account_types = ['savings', 'checking']
        
        for client in clients:
            # Each client gets 1-3 accounts
            num_accounts = random.randint(1, 3)
            for i in range(num_accounts):
                account_type = random.choice(account_types)
                account_number = f"{random.randint(1000000000, 9999999999)}"
                
                # Savings accounts have higher interest rates
                interest_rate = Decimal('0.0250') if account_type == 'savings' else Decimal('0.0050')
                
                # Random initial balance
                initial_balance = Decimal(random.randint(5000, 100000))
                
                account = Account.objects.create(
                    client=client,
                    account_type=account_type,
                    account_number=account_number,
                    current_balance=initial_balance,
                    interest_rate=interest_rate,
                    is_active=True,
                )
                accounts.append(account)

        return accounts

    def create_transactions(self, accounts):
        """Create various transactions for accounts"""
        transactions = []
        transaction_types = ['deposit', 'withdrawal']
        
        for account in accounts:
            # Each account gets 3-8 transactions
            num_transactions = random.randint(3, 8)
            
            for i in range(num_transactions):
                trans_type = random.choice(transaction_types)
                
                # Deposits are generally larger than withdrawals
                if trans_type == 'deposit':
                    amount = Decimal(random.randint(1000, 50000))
                    description = random.choice([
                        'Salary deposit',
                        'Business income',
                        'Freelance payment',
                        'Investment return',
                        'Cash deposit',
                    ])
                else:
                    amount = Decimal(random.randint(500, 20000))
                    description = random.choice([
                        'ATM withdrawal',
                        'Bill payment',
                        'Online purchase',
                        'Cash withdrawal',
                        'Utility payment',
                    ])
                
                # Create transaction with date in the past
                days_ago = random.randint(1, 90)
                trans_date = timezone.now() - timedelta(days=days_ago)
                
                transaction = Transaction.objects.create(
                    account=account,
                    transaction_type=trans_type,
                    amount=amount,
                    description=description,
                )
                # Manually set the date
                transaction.transaction_date = trans_date
                transaction.save()
                
                # Update account balance
                if trans_type == 'deposit':
                    account.current_balance += amount
                else:
                    account.current_balance -= amount
                account.save()
                
                transactions.append(transaction)

        return transactions

    def create_loan_applications(self, clients):
        """Create loan applications with various statuses"""
        loan_apps = []
        statuses = ['pending', 'approved', 'rejected']
        purposes = [
            'Home renovation',
            'Business expansion',
            'Education',
            'Medical expenses',
            'Debt consolidation',
            'Vehicle purchase',
            'Wedding expenses',
        ]
        
        # Get admin user as loan officer
        admin_user = User.objects.get(username='admin')
        
        for client in clients:
            # Each client has 0-2 loan applications
            num_apps = random.randint(0, 2)
            
            for i in range(num_apps):
                status = random.choice(statuses)
                loan_amount = Decimal(random.randint(50000, 500000))
                purpose = random.choice(purposes)
                
                # Calculate eligibility score based on credit score
                base_score = (client.credit_score - 600) / 4  # Scale 600-1000 to 0-100
                eligibility_score = max(0, min(100, base_score + random.randint(-10, 10)))
                
                days_ago = random.randint(5, 60)
                app_date = timezone.now() - timedelta(days=days_ago)
                
                loan_app = LoanApplication.objects.create(
                    client=client,
                    loan_officer=admin_user,
                    loan_amount=loan_amount,
                    purpose=purpose,
                    status=status,
                    eligibility_score=Decimal(str(eligibility_score)),
                )
                loan_app.application_date = app_date
                
                if status == 'approved':
                    loan_app.approval_date = app_date + timedelta(days=random.randint(1, 7))
                elif status == 'rejected':
                    loan_app.rejection_reason = random.choice([
                        'Insufficient credit score',
                        'High debt-to-income ratio',
                        'Incomplete documentation',
                        'Unstable employment history',
                    ])
                
                loan_app.save()
                loan_apps.append(loan_app)

        return loan_apps

    def create_loans(self, loan_applications):
        """Create loans for approved applications"""
        loans = []
        
        approved_apps = [app for app in loan_applications if app.status == 'approved']
        
        for app in approved_apps:
            # Randomly decide if approved app has been disbursed (80% chance)
            if random.random() < 0.8:
                interest_rate = Decimal('0.0850')  # 8.5% annual interest
                term_months = random.choice([12, 24, 36, 48, 60])
                
                start_date = app.approval_date.date() if app.approval_date else timezone.now().date()
                end_date = start_date + timedelta(days=term_months * 30)
                
                # Calculate monthly payment
                monthly_rate = interest_rate / 12
                num_payments = term_months
                monthly_payment = app.loan_amount * (monthly_rate * (1 + monthly_rate) ** num_payments) / ((1 + monthly_rate) ** num_payments - 1)
                
                # Random number of payments made (0 to half of term)
                payments_made = random.randint(0, term_months // 2)
                remaining_balance = app.loan_amount - (Decimal(str(monthly_payment)) * payments_made * Decimal('0.6'))  # Approximate
                
                status = 'active' if remaining_balance > 0 else 'paid'
                
                loan = Loan.objects.create(
                    application=app,
                    loan_amount=app.loan_amount,
                    interest_rate=interest_rate,
                    term_months=term_months,
                    start_date=start_date,
                    end_date=end_date,
                    remaining_balance=max(Decimal('0'), remaining_balance),
                    status=status,
                )
                
                # Create amortization schedule
                self.create_amortization_schedule(loan, monthly_payment, payments_made)
                
                loans.append(loan)

        return loans

    def create_amortization_schedule(self, loan, monthly_payment, payments_made):
        """Create amortization schedule for a loan"""
        current_date = loan.start_date
        remaining_principal = loan.loan_amount
        monthly_rate = loan.interest_rate / 12
        
        for i in range(1, loan.term_months + 1):
            due_date = current_date + timedelta(days=30 * i)
            
            interest_amount = remaining_principal * monthly_rate
            principal_amount = monthly_payment - interest_amount
            
            # Determine status
            if i <= payments_made:
                status = 'paid'
            elif due_date < timezone.now().date():
                status = 'overdue'
            else:
                status = 'pending'
            
            AmortizationSchedule.objects.create(
                loan=loan,
                installment_number=i,
                due_date=due_date,
                principal_amount=principal_amount,
                interest_amount=interest_amount,
                total_payment=monthly_payment,
                status=status,
            )
            
            remaining_principal -= principal_amount

    def create_loan_payments(self, loans, accounts):
        """Create loan payment transactions"""
        payments = []
        
        for loan in loans:
            # Get paid installments
            paid_schedules = loan.schedules.filter(status='paid')
            
            # Get a random account from the loan's client
            client_accounts = [acc for acc in accounts if acc.client == loan.application.client]
            if not client_accounts:
                continue
                
            account = random.choice(client_accounts)
            
            for schedule in paid_schedules:
                payment = Transaction.objects.create(
                    account=account,
                    loan=loan,
                    transaction_type='payment',
                    amount=schedule.total_payment,
                    description=f'Loan payment - Installment {schedule.installment_number}',
                )
                # Set date to match schedule due date
                payment.transaction_date = timezone.make_aware(
                    datetime.combine(schedule.due_date, datetime.min.time())
                )
                payment.save()
                
                # Deduct from account balance
                account.current_balance -= schedule.total_payment
                account.save()
                
                payments.append(payment)

        return payments
