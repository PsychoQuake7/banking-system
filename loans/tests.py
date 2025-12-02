from django.test import TestCase, Client as TestClient
from django.contrib.auth import get_user_model
from clients.models import Client
from accounts.models import Account
from loans.models import LoanApplication, Loan
from decimal import Decimal
from datetime import date, timedelta

User = get_user_model()

class EligibilityCalculationTests(TestCase):
    def setUp(self):
        # Create base user
        self.user = User.objects.create_user(username='testuser', email='test@example.com', password='password')
        self.client = Client.objects.create(
            user=self.user,
            first_name='Test',
            last_name='User',
            monthly_income=Decimal('50000.00'),
            credit_score=750,
            date_of_birth='1990-01-01',
            address='123 Test St'
        )
        self.savings_account = Account.objects.create(
            client=self.client,
            account_type='savings',
            account_number='SAV-0001',
            current_balance=Decimal('0.00')
        )
    
    def set_savings_balance(self, amount):
        self.savings_account.current_balance = amount
        self.savings_account.save()
        
    def create_active_loan(self, client, monthly_payment, balance):
        """Helper to create an active loan for testing"""
        app = LoanApplication.objects.create(
            client=client,
            loan_amount=balance, # Simplified
            purpose='Test',
            term_months=12,
            status='approved'
        )
        loan = Loan.objects.create(
            application=app,
            loan_amount=balance,
            interest_rate=Decimal('0.10'),
            term_months=12,
            start_date=date.today(),
            end_date=date.today() + timedelta(days=365),
            remaining_balance=balance,
            status='active'
        )
        # We need to mock get_monthly_payment since it's calculated
        # But for integration test, we rely on the actual calculation.
        # So we should set loan amount and terms such that it results in desired monthly payment.
        # Or we can just mock the return value if we were unit testing, but this is integration.
        # Let's just create multiple loans if needed to reach a DTI.
        return loan

    def test_high_eligibility_client(self):
        """
        Test Scenario 1: High Eligibility Client
        - Credit score: 850
        - Monthly income: 100,000
        - No existing loans
        - Savings: >= 12 months coverage
        """
        self.client.credit_score = 850
        self.client.monthly_income = Decimal('100000.00')
        self.client.save()
        self.set_savings_balance(Decimal('1200000.00'))
        
        from loans.utils import calculate_eligibility_score
        result = calculate_eligibility_score(self.client)
        
        # Expected: ~95-100 score
        # All factors maxed -> score 100
        self.assertEqual(result['eligibility_score'], 100)
        self.assertEqual(result['recommendation'], "Excellent - Highly Recommended")
        self.assertTrue(result['is_eligible'])
        self.assertEqual(len(result['warnings']), 0)

    def test_medium_eligibility_client(self):
        """
        Test Scenario 2: Medium Eligibility Client
        - Credit score: 650
        - Monthly income: 50,000
        - 1 active loan with ~10,000/month payment
        """
        self.client.credit_score = 650
        self.client.monthly_income = Decimal('50000.00')
        self.client.save()
        self.set_savings_balance(Decimal('150000.00'))
        
        # Create a loan that results in approx 10k monthly payment
        # 100k loan for 12 months at 10% is roughly 8.8k. Let's do 120k.
        app = LoanApplication.objects.create(
            client=self.client,
            loan_amount=Decimal('120000.00'),
            term_months=12,
            status='approved',
            purpose='Test'
        )
        loan = Loan.objects.create(
            application=app,
            loan_amount=Decimal('120000.00'),
            interest_rate=Decimal('0.10'),
            term_months=12,
            start_date=date.today(),
            end_date=date.today() + timedelta(days=365),
            remaining_balance=Decimal('100000.00'),
            status='active'
        )
        
        from loans.utils import calculate_eligibility_score
        result = calculate_eligibility_score(self.client)
        
        # Credit (650): 65 pts * 0.40 = 26
        # DTI (~20%): 100 pts * 0.35 = 35
        # Burden (1 loan, <1yr income): 85 pts * 0.25 = 21.25
        # Total: ~82.25
        
        self.assertGreater(result['eligibility_score'], 60)
        self.assertTrue(result['is_eligible'])

    def test_low_eligibility_client(self):
        """
        Test Scenario 3: Low Eligibility Client
        - Credit score: 450
        - Monthly income: 20,000
        - High DTI
        """
        self.client.credit_score = 450
        self.client.monthly_income = Decimal('20000.00')
        self.client.save()
        self.set_savings_balance(Decimal('0.00'))
        
        # Create loans to increase DTI
        # Need > 40% DTI. 40% of 20k is 8k.
        app = LoanApplication.objects.create(
            client=self.client,
            loan_amount=Decimal('100000.00'),
            term_months=12,
            status='approved',
            purpose='Test'
        )
        loan = Loan.objects.create(
            application=app,
            loan_amount=Decimal('100000.00'),
            interest_rate=Decimal('0.10'),
            term_months=12,
            start_date=date.today(),
            end_date=date.today() + timedelta(days=365),
            remaining_balance=Decimal('90000.00'),
            status='active'
        )
        
        from loans.utils import calculate_eligibility_score
        result = calculate_eligibility_score(self.client)
        
        # Credit (450): 25 pts * 0.40 = 10
        # DTI (>40%): 40 pts * 0.35 = 14
        # Burden (1 loan, >3yr income? No, 90k < 20k*12*3): 85 pts * 0.25 = 21.25
        # Total: ~45.25
        
        self.assertLess(result['eligibility_score'], 50)
        self.assertTrue(result['is_eligible']) # Still eligible but low score, unless DTI > 50%

    def test_automatic_rejection_credit_score(self):
        """Test rejection due to low credit score"""
        self.client.credit_score = 250
        self.client.save()
        self.set_savings_balance(Decimal('0.00'))
        
        from loans.utils import calculate_eligibility_score
        result = calculate_eligibility_score(self.client)
        
        self.assertFalse(result['is_eligible'])
        self.assertIn("Credit score below minimum threshold", result['warnings'][0])

    def test_automatic_rejection_dti(self):
        """Test rejection due to high DTI (>50%)"""
        self.client.monthly_income = Decimal('10000.00')
        self.client.save()
        self.set_savings_balance(Decimal('0.00'))
        
        # Create massive loan payment
        app = LoanApplication.objects.create(
            client=self.client,
            loan_amount=Decimal('100000.00'),
            term_months=12, # ~8.8k payment / 10k income = 88% DTI
            status='approved',
            purpose='Test'
        )
        loan = Loan.objects.create(
            application=app,
            loan_amount=Decimal('100000.00'),
            interest_rate=Decimal('0.10'),
            term_months=12,
            start_date=date.today(),
            end_date=date.today() + timedelta(days=365),
            remaining_balance=Decimal('100000.00'),
            status='active'
        )
        
        from loans.utils import calculate_eligibility_score
        result = calculate_eligibility_score(self.client)
        
        self.assertFalse(result['is_eligible'])
        self.assertTrue(any("Debt-to-Income ratio" in w for w in result['warnings']))

    def test_max_loan_amount_calculation(self):
        """Test maximum loan amount calculation logic"""
        self.client.monthly_income = Decimal('50000.00')
        self.client.credit_score = 800
        self.client.save()
        self.set_savings_balance(Decimal('600000.00'))
        
        from loans.utils import calculate_eligibility_score
        result = calculate_eligibility_score(self.client)
        
        # Base: 50k * 12 * 3 = 1.8M (score 100 so remains 1.8M)
        self.assertEqual(result['max_loan_amount'], Decimal('1800000.00'))
        
        # Add existing debt
        app = LoanApplication.objects.create(
            client=self.client,
            loan_amount=Decimal('500000.00'),
            term_months=60,
            status='approved',
            purpose='Test'
        )
        loan = Loan.objects.create(
            application=app,
            loan_amount=Decimal('500000.00'),
            interest_rate=Decimal('0.10'),
            term_months=60,
            start_date=date.today(),
            end_date=date.today() + timedelta(days=365),
            remaining_balance=Decimal('400000.00'),
            status='active'
        )
        
        result = calculate_eligibility_score(self.client)
        
        base_amount = self.client.monthly_income * 12 * 3
        score_multiplier = Decimal(str(result['eligibility_score'])) / Decimal('100')
        expected_max = (base_amount * score_multiplier) - Decimal('400000.00')
        self.assertAlmostEqual(result['max_loan_amount'], expected_max, delta=Decimal('1.00'))
