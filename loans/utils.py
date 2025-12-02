"""
Loan eligibility calculation utilities.

This module provides functions to calculate loan eligibility scores based on:
- Client credit score
- Debt-to-income ratio (income)
- Existing loan burden
- Savings reserves

The eligibility score is a weighted combination of these factors.
"""

from decimal import Decimal
from typing import Dict, List, Optional
from django.db.models import Sum, Q
from datetime import date


def calculate_credit_score_factor(credit_score: int) -> int:
    """
    Calculate credit score factor (0-100 points).
    
    Args:
        credit_score: Client's credit score (0-1000)
        
    Returns:
        Factor points (0-100)
    """
    if credit_score >= 800:
        return 100
    elif credit_score >= 700:
        return 85
    elif credit_score >= 600:
        return 65
    elif credit_score >= 500:
        return 45
    elif credit_score >= 300:
        return 25
    else:
        return 0  # Below 300 is ineligible


def calculate_debt_to_income_ratio(client) -> Dict[str, any]:
    """
    Calculate debt-to-income ratio for a client.
    
    Args:
        client: Client model instance
        
    Returns:
        Dictionary with:
            - dti_ratio: DTI percentage (0-100+)
            - monthly_debt: Total monthly debt payments
            - monthly_income: Client's monthly income
            - factor_points: Factor points (0-100)
    """
    from loans.models import Loan
    
    monthly_income = client.monthly_income
    
    # If no income, DTI is infinite (return 0 factor)
    if monthly_income <= 0:
        return {
            'dti_ratio': 100.0,
            'monthly_debt': Decimal('0.00'),
            'monthly_income': monthly_income,
            'factor_points': 0
        }
    
    # Get all active loans for this client
    active_loans = Loan.objects.filter(
        application__client=client,
        status='active'
    )
    
    # Calculate total monthly debt payments
    total_monthly_debt = Decimal('0.00')
    for loan in active_loans:
        monthly_payment = loan.get_monthly_payment()
        total_monthly_debt += monthly_payment
    
    # Calculate DTI ratio as percentage
    dti_ratio = float((total_monthly_debt / monthly_income) * 100)
    
    # Determine factor points based on DTI ratio
    if dti_ratio <= 20:
        factor_points = 100
    elif dti_ratio <= 30:
        factor_points = 85
    elif dti_ratio <= 40:
        factor_points = 65
    elif dti_ratio <= 50:
        factor_points = 40
    else:
        factor_points = 0  # Above 50% DTI is ineligible
    
    return {
        'dti_ratio': round(dti_ratio, 2),
        'monthly_debt': total_monthly_debt,
        'monthly_income': monthly_income,
        'factor_points': factor_points
    }


def calculate_existing_loan_burden(client) -> Dict[str, any]:
    """
    Calculate existing loan burden factor.
    
    Args:
        client: Client model instance
        
    Returns:
        Dictionary with:
            - active_loan_count: Number of active loans
            - total_balance: Total remaining balance
            - annual_income: Client's annual income
            - balance_to_income_ratio: Balance as multiple of annual income
            - factor_points: Factor points (0-100)
    """
    from loans.models import Loan
    
    # Get all active loans
    active_loans = Loan.objects.filter(
        application__client=client,
        status='active'
    )
    
    active_loan_count = active_loans.count()
    total_balance = active_loans.aggregate(
        total=Sum('remaining_balance')
    )['total'] or Decimal('0.00')
    
    annual_income = client.monthly_income * 12
    
    # Calculate balance as multiple of annual income
    if annual_income > 0:
        balance_to_income_ratio = float(total_balance / annual_income)
    else:
        balance_to_income_ratio = 0.0
    
    # Determine factor points based on loan count and balance
    if active_loan_count == 0:
        factor_points = 100
    elif active_loan_count <= 2 and balance_to_income_ratio < 1:
        factor_points = 85
    elif active_loan_count <= 2 and balance_to_income_ratio < 2:
        factor_points = 70
    elif active_loan_count <= 4 and balance_to_income_ratio < 2:
        factor_points = 50
    elif active_loan_count >= 5:
        factor_points = 25
    elif balance_to_income_ratio >= 3:
        factor_points = 10
    else:
        factor_points = 40
    
    return {
        'active_loan_count': active_loan_count,
        'total_balance': total_balance,
        'annual_income': annual_income,
        'balance_to_income_ratio': round(balance_to_income_ratio, 2),
        'factor_points': factor_points
    }


def calculate_savings_factor(client) -> Dict[str, any]:
    """
    Calculate savings strength factor based on active savings accounts.
    
    Args:
        client: Client model instance
        
    Returns:
        Dictionary with:
            - total_savings: Combined savings balance
            - coverage_months: Months of income covered by savings
            - factor_points: Factor points (0-100)
    """
    from accounts.models import Account
    
    savings_accounts = Account.objects.filter(
        client=client,
        account_type='savings',
        is_active=True
    )
    
    total_savings = savings_accounts.aggregate(
        total=Sum('current_balance')
    )['total'] or Decimal('0.00')
    
    monthly_income = client.monthly_income
    
    if monthly_income > 0:
        coverage_months = float(total_savings / monthly_income) if monthly_income else 0.0
        coverage_months = round(coverage_months, 2)
        
        if coverage_months >= 12:
            factor_points = 100
        elif coverage_months >= 6:
            factor_points = 85
        elif coverage_months >= 3:
            factor_points = 65
        elif coverage_months >= 1:
            factor_points = 40
        elif total_savings > 0:
            factor_points = 20
        else:
            factor_points = 0
    else:
        coverage_months = None
        if total_savings >= Decimal('1000000.00'):
            factor_points = 90
        elif total_savings >= Decimal('500000.00'):
            factor_points = 75
        elif total_savings >= Decimal('100000.00'):
            factor_points = 50
        elif total_savings > 0:
            factor_points = 25
        else:
            factor_points = 0
    
    return {
        'total_savings': total_savings,
        'coverage_months': coverage_months,
        'factor_points': factor_points,
        'monthly_income': monthly_income
    }


def calculate_eligibility_score(client, requested_amount: Optional[Decimal] = None) -> Dict[str, any]:
    """
    Calculate comprehensive loan eligibility score.
    
    This is the main function that combines all factors with weights:
    - Credit Score: 35% weight
    - Debt-to-Income Ratio: 35% weight
    - Existing Loan Burden: 15% weight
    - Savings Strength: 15% weight
    
    Args:
        client: Client model instance
        requested_amount: Optional requested loan amount for specific checks
        
    Returns:
        Dictionary with:
            - eligibility_score: Overall score (0-100)
            - max_loan_amount: Maximum eligible loan amount
            - recommendation: Text recommendation
            - factors: Detailed breakdown of all factors
            - warnings: List of warning messages
            - is_eligible: Boolean indicating if client is eligible
    """
    # Calculate individual factors
    credit_factor = calculate_credit_score_factor(client.credit_score)
    dti_data = calculate_debt_to_income_ratio(client)
    loan_burden_data = calculate_existing_loan_burden(client)
    savings_data = calculate_savings_factor(client)
    
    # Apply weights to get weighted scores
    credit_weighted = credit_factor * 0.35
    dti_weighted = dti_data['factor_points'] * 0.35
    burden_weighted = loan_burden_data['factor_points'] * 0.15
    savings_weighted = savings_data['factor_points'] * 0.15
    
    # Calculate overall eligibility score
    eligibility_score = credit_weighted + dti_weighted + burden_weighted + savings_weighted
    
    # Calculate maximum loan amount
    # Base: 3 years of annual income
    base_amount = client.monthly_income * 12 * 3
    
    # Adjust by eligibility score
    eligibility_multiplier = Decimal(str(eligibility_score / 100))
    
    # Reduce by existing debt
    max_loan_amount = (base_amount * eligibility_multiplier) - loan_burden_data['total_balance']
    
    # Ensure non-negative
    if max_loan_amount < 0:
        max_loan_amount = Decimal('0.00')
    
    # Get recommendation
    recommendation = get_eligibility_recommendation(eligibility_score)
    
    # Collect warnings
    warnings = []
    
    # Check for automatic rejection criteria
    is_eligible = True
    
    if client.credit_score < 300:
        warnings.append("Credit score below minimum threshold (300)")
        is_eligible = False
    
    if dti_data['dti_ratio'] > 50:
        warnings.append(f"Debt-to-Income ratio ({dti_data['dti_ratio']:.1f}%) exceeds maximum threshold (50%)")
        is_eligible = False
    
    if client.monthly_income <= 0:
        warnings.append("No monthly income reported")
        is_eligible = False
    
    # Additional warnings for concerning factors
    if client.credit_score < 600:
        warnings.append(f"Low credit score ({client.credit_score}). Consider improving credit history.")
    
    if dti_data['dti_ratio'] > 40:
        warnings.append(f"High debt-to-income ratio ({dti_data['dti_ratio']:.1f}%). Consider reducing existing debt.")
    
    if loan_burden_data['active_loan_count'] >= 3:
        warnings.append(f"Multiple active loans ({loan_burden_data['active_loan_count']}). Consider consolidating.")
    
    low_savings = False
    if savings_data['coverage_months'] is not None:
        low_savings = savings_data['coverage_months'] < 1
    else:
        low_savings = savings_data['total_savings'] < Decimal('100000.00')
    if low_savings:
        warnings.append("Low savings reserves. Build additional savings to strengthen eligibility.")
    
    # Check if requested amount exceeds maximum
    if requested_amount and requested_amount > max_loan_amount:
        warnings.append(f"Requested amount (₱{requested_amount:,.2f}) exceeds maximum eligible amount (₱{max_loan_amount:,.2f})")
    
    return {
        'eligibility_score': round(eligibility_score, 2),
        'max_loan_amount': max_loan_amount,
        'recommendation': recommendation,
        'is_eligible': is_eligible,
        'factors': {
            'credit_score': {
                'value': client.credit_score,
                'factor_points': credit_factor,
                'weighted_score': round(credit_weighted, 2),
                'weight_percentage': 35
            },
            'dti_ratio': {
                'value': dti_data['dti_ratio'],
                'monthly_debt': dti_data['monthly_debt'],
                'monthly_income': dti_data['monthly_income'],
                'factor_points': dti_data['factor_points'],
                'weighted_score': round(dti_weighted, 2),
                'weight_percentage': 35
            },
            'loan_burden': {
                'active_loan_count': loan_burden_data['active_loan_count'],
                'total_balance': loan_burden_data['total_balance'],
                'balance_to_income_ratio': loan_burden_data['balance_to_income_ratio'],
                'factor_points': loan_burden_data['factor_points'],
                'weighted_score': round(burden_weighted, 2),
                'weight_percentage': 15
            },
            'savings': {
                'total_savings': savings_data['total_savings'],
                'coverage_months': savings_data['coverage_months'],
                'monthly_income': savings_data['monthly_income'],
                'factor_points': savings_data['factor_points'],
                'weighted_score': round(savings_weighted, 2),
                'weight_percentage': 15
            }
        },
        'warnings': warnings,
        'requested_amount': requested_amount
    }


def get_eligibility_recommendation(eligibility_score: float) -> str:
    """
    Get text recommendation based on eligibility score.
    
    Args:
        eligibility_score: Overall eligibility score (0-100)
        
    Returns:
        Recommendation text
    """
    if eligibility_score >= 80:
        return "Excellent - Highly Recommended"
    elif eligibility_score >= 65:
        return "Good - Recommended"
    elif eligibility_score >= 50:
        return "Fair - Conditional Approval"
    elif eligibility_score >= 30:
        return "Poor - High Risk"
    else:
        return "Very Poor - Not Recommended"


def get_improvement_suggestions(eligibility_result: Dict[str, any]) -> List[str]:
    """
    Generate suggestions for improving eligibility score.
    
    Args:
        eligibility_result: Result from calculate_eligibility_score()
        
    Returns:
        List of suggestion strings
    """
    suggestions = []
    factors = eligibility_result['factors']
    
    # Credit score suggestions
    if factors['credit_score']['value'] < 700:
        suggestions.append("Improve credit score by paying bills on time and reducing credit utilization")
    
    # DTI suggestions
    if factors['dti_ratio']['value'] > 30:
        suggestions.append("Reduce debt-to-income ratio by paying down existing loans or increasing income")
    
    # Loan burden suggestions
    if factors['loan_burden']['active_loan_count'] >= 3:
        suggestions.append("Consider consolidating multiple loans into a single loan")
    
    if factors['loan_burden']['balance_to_income_ratio'] > 1.5:
        suggestions.append("Work on reducing total loan balance relative to annual income")
    
    # Savings suggestions
    coverage_months = factors['savings']['coverage_months']
    if coverage_months is not None:
        if coverage_months < 3:
            suggestions.append("Build savings to cover at least 3 months of income")
    else:
        if factors['savings']['total_savings'] < Decimal('300000.00'):
            suggestions.append("Increase savings balances to strengthen eligibility")
    
    # Income suggestions
    if factors['dti_ratio']['monthly_income'] < 30000:
        suggestions.append("Increasing monthly income would improve maximum eligible loan amount")
    
    return suggestions
