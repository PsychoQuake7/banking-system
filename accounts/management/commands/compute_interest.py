from django.core.management.base import BaseCommand
from accounts.models import Account
from django.utils import timezone

class Command(BaseCommand):
    help = 'Computes daily interest for all active savings accounts'

    def add_arguments(self, parser):
        parser.add_argument(
            '--capitalize',
            action='store_true',
            help='Also capitalize (pay out) accrued interest',
        )

    def handle(self, *args, **options):
        today = timezone.now().date()
        self.stdout.write(f'Running interest computation for {today}...')
        
        savings_accounts = Account.objects.filter(
            account_type='savings', 
            is_active=True,
            current_balance__gt=0
        )
        
        count = 0
        total_accrued = 0
        
        for account in savings_accounts:
            try:
                accrual = account.compute_daily_interest(date=today)
                if accrual:
                    count += 1
                    total_accrued += accrual.interest_earned
                    self.stdout.write(f'  Accrued ₱{accrual.interest_earned} for Account {account.account_number}')
                
                if options['capitalize']:
                    capitalized = account.capitalize_interest()
                    if capitalized > 0:
                        self.stdout.write(self.style.SUCCESS(f'  Capitalized ₱{capitalized} for Account {account.account_number}'))
                        
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'  Error processing account {account.account_number}: {str(e)}'))
        
        self.stdout.write(self.style.SUCCESS(f'Successfully processed {count} accounts. Total accrued: ₱{total_accrued}'))
