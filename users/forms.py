from django import forms
from allauth.account.forms import SignupForm, LoginForm
from datetime import date
from dateutil.relativedelta import relativedelta


class CustomSignupForm(SignupForm):
    """
    Custom signup form that extends allauth's SignupForm to collect
    additional Client profile information during user registration.
    """
    
    # Client profile fields
    first_name = forms.CharField(
        max_length=50,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your first name'
        }),
        label='First Name',
        help_text='Your legal first name'
    )
    
    last_name = forms.CharField(
        max_length=50,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your last name'
        }),
        label='Last Name',
        help_text='Your legal last name'
    )
    
    dob_year = forms.ChoiceField(
        choices=[('', 'Year')] + [(str(y), str(y)) for y in range(date.today().year, 1900, -1)],
        required=True,
        widget=forms.Select(attrs={'class': 'form-select'}),
        label='Year'
    )
    
    dob_month = forms.ChoiceField(
        choices=[('', 'Month')] + [(str(m), date(2000, m, 1).strftime('%B')) for m in range(1, 13)],
        required=True,
        widget=forms.Select(attrs={'class': 'form-select'}),
        label='Month'
    )
    
    dob_day = forms.ChoiceField(
        choices=[('', 'Day')] + [(str(d), str(d)) for d in range(1, 32)],
        required=True,
        widget=forms.Select(attrs={'class': 'form-select'}),
        label='Day'
    )
    
    address = forms.CharField(
        required=True,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Enter your complete address'
        }),
        label='Address',
        help_text='Your complete residential address (minimum 10 characters)'
    )
    
    phone = forms.CharField(
        max_length=20,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '+63 XXX XXX XXXX'
        }),
        label='Phone Number',
        help_text='Optional: Your contact phone number'
    )
    
    monthly_income = forms.DecimalField(
        max_digits=15,
        decimal_places=2,
        required=False,
        initial=0.00,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': '0.00',
            'step': '0.01',
            'min': '0'
        }),
        label='Monthly Income',
        help_text='Optional: Your monthly income in PHP'
    )
    
    id_document = forms.FileField(
        required=False,
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': 'image/*,.pdf'
        }),
        label='ID Document',
        help_text='Optional: Upload a valid government-issued ID (image or PDF)'
    )
    
    def clean(self):
        """
        Combine year, month, day into date_of_birth and validate age.
        """
        cleaned_data = super().clean()
        year = cleaned_data.get('dob_year')
        month = cleaned_data.get('dob_month')
        day = cleaned_data.get('dob_day')
        
        if year and month and day:
            try:
                dob = date(int(year), int(month), int(day))
                cleaned_data['date_of_birth'] = dob
                
                today = date.today()
                age = relativedelta(today, dob).years
                
                if age < 18:
                    raise forms.ValidationError(
                        'You must be at least 18 years old to register. '
                        f'You are currently {age} years old.'
                    )
            except ValueError:
                raise forms.ValidationError('Invalid date of birth.')
        
        return cleaned_data
    
    def clean_address(self):
        """
        Validate that the address is at least 10 characters long.
        """
        address = self.cleaned_data.get('address')
        if address and len(address.strip()) < 10:
            raise forms.ValidationError(
                'Please provide a complete address (minimum 10 characters). '
                f'Current length: {len(address.strip())} characters.'
            )
        
        return address.strip() if address else address
    
    def clean_phone(self):
        """
        Clean and validate phone number format.
        """
        phone = self.cleaned_data.get('phone')
        if phone:
            # Remove common separators for validation
            cleaned_phone = phone.replace(' ', '').replace('-', '').replace('(', '').replace(')', '')
            
            # Basic validation: should contain only digits and + sign
            if not all(c.isdigit() or c == '+' for c in cleaned_phone):
                raise forms.ValidationError(
                    'Phone number should only contain digits, spaces, hyphens, and + sign.'
                )
        
        return phone
    
    def clean_monthly_income(self):
        """
        Validate monthly income is non-negative.
        """
        income = self.cleaned_data.get('monthly_income')
        if income is not None and income < 0:
            raise forms.ValidationError('Monthly income cannot be negative.')
        
        return income if income is not None else 0.00
    
    def save(self, request):
        """
        Save the user and store Client profile data in the request session
        for the adapter to use when creating the Client profile.
        """
        # Store Client profile data in session for the adapter
        request.session['client_profile_data'] = {
            'first_name': self.cleaned_data.get('first_name'),
            'last_name': self.cleaned_data.get('last_name'),
            'date_of_birth': self.cleaned_data.get('date_of_birth').isoformat(),
            'address': self.cleaned_data.get('address'),
            'phone': self.cleaned_data.get('phone', ''),
            'monthly_income': str(self.cleaned_data.get('monthly_income', '0.00')),
        }
        
        # Handle file upload separately (can't store in session)
        if 'id_document' in self.cleaned_data and self.cleaned_data['id_document']:
            request.session['has_id_document'] = True
        
        # Call parent's save method to create the user
        return super().save(request)


class CustomLoginForm(LoginForm):
    """
    Custom login form to change the label of the login field.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['login'].label = 'Username'


from django.contrib.auth.forms import UserCreationForm
from .models import CustomUser

class AdminUserCreationForm(UserCreationForm):
    """
    Form for admins to create new users with specific roles.
    """
    class Meta:
        model = CustomUser
        fields = ('username', 'email', 'role', 'first_name', 'last_name')
        
    def save(self, commit=True):
        user = super().save(commit=False)
        if commit:
            user.save()
        return user
