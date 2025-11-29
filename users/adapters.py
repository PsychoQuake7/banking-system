from allauth.account.adapter import DefaultAccountAdapter
from django.db import transaction
from clients.models import Client
from datetime import date


class CustomAccountAdapter(DefaultAccountAdapter):
    """
    Custom account adapter that extends allauth's DefaultAccountAdapter
    to automatically create a Client profile when a new user registers.
    """
    
    def save_user(self, request, user, form, commit=True):
        """
        Save the user and create an associated Client profile.
        Uses database transactions to ensure atomicity.
        """
        # Call parent method to save the user
        user = super().save_user(request, user, form, commit=False)
        
        # Set default role for new users
        user.role = 'borrower'
        
        if commit:
            with transaction.atomic():
                # Save the user first
                user.save()
                
                # Retrieve Client profile data from session
                client_data = request.session.get('client_profile_data', {})
                
                # Convert date string back to date object
                dob_str = client_data.get('date_of_birth')
                if dob_str:
                    dob = date.fromisoformat(dob_str)
                else:
                    # Fallback to a default date if not provided (should not happen with validation)
                    dob = date.today()
                
                # Create the Client profile
                client = Client.objects.create(
                    user=user,
                    first_name=client_data.get('first_name', ''),
                    last_name=client_data.get('last_name', ''),
                    date_of_birth=dob,
                    address=client_data.get('address', ''),
                    monthly_income=client_data.get('monthly_income', '0.00'),
                    credit_score=0  # Default credit score for new users
                )
                
                # Update user's phone number if provided
                phone = client_data.get('phone', '')
                if phone:
                    user.phone = phone
                    user.save(update_fields=['phone'])
                
                # Handle ID document upload if present
                if 'id_document' in form.cleaned_data and form.cleaned_data['id_document']:
                    client.id_document = form.cleaned_data['id_document']
                    client.save(update_fields=['id_document'])
                
                # Clean up session data
                if 'client_profile_data' in request.session:
                    del request.session['client_profile_data']
                if 'has_id_document' in request.session:
                    del request.session['has_id_document']
        
        return user
    
    def get_login_redirect_url(self, request):
        """
        Redirect to dashboard after successful login.
        """
        return '/dashboard/'
    
    def get_signup_redirect_url(self, request):
        """
        Redirect to dashboard after successful signup.
        """
        return '/dashboard/'
