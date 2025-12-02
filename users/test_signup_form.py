from django.test import TestCase
from users.forms import CustomSignupForm
from datetime import date

class CustomSignupFormTest(TestCase):
    def test_signup_form_valid_date(self):
        form_data = {
            'first_name': 'John',
            'last_name': 'Doe',
            'dob_year': '2000',
            'dob_month': '1',
            'dob_day': '1',
            'address': '123 Main St, City',
            'phone': '+1234567890',
            'monthly_income': '1000.00',
            # Required fields from SignupForm (allauth) usually include email/username/password
            # but CustomSignupForm inherits from it. 
            # We might need to provide them if validation runs on parent fields too.
            'username': 'johndoe',
            'email': 'john@example.com',
        }
        form = CustomSignupForm(data=form_data)
        # We might need to mock request or ignore other errors if we just want to check date_of_birth
        # But let's see if is_valid() passes or if we can check cleaned_data after full_clean()
        
        # Since SignupForm might require more data (passwords), let's focus on the date part
        # by inspecting the errors or cleaned_data manually if is_valid fails on other fields.
        
        form.is_valid() # Trigger validation
        
        # Check if date_of_birth is in cleaned_data and correct
        if 'date_of_birth' in form.cleaned_data:
            self.assertEqual(form.cleaned_data['date_of_birth'], date(2000, 1, 1))
        else:
            # If it failed, check errors
            print(form.errors)
            self.fail("date_of_birth not in cleaned_data")

    def test_signup_form_underage(self):
        today = date.today()
        # 17 years ago
        dob = today.replace(year=today.year - 17)
        
        form_data = {
            'first_name': 'Kid',
            'last_name': 'Doe',
            'dob_year': str(dob.year),
            'dob_month': str(dob.month),
            'dob_day': str(dob.day),
            'address': '123 Main St',
        }
        form = CustomSignupForm(data=form_data)
        form.is_valid()
        
        # Check that the error message appears in non_field_errors
        found_error = False
        for error in form.non_field_errors():
            if "at least 18 years old" in error:
                found_error = True
                break
        self.assertTrue(found_error, f"Underage error not found in {form.non_field_errors()}")

    def test_signup_form_invalid_date(self):
        form_data = {
            'dob_year': '2000',
            'dob_month': '2',
            'dob_day': '30', # Feb 30 is invalid
        }
        form = CustomSignupForm(data=form_data)
        form.is_valid()
        
        found_error = False
        for error in form.non_field_errors():
            if "Invalid date of birth" in error:
                found_error = True
                break
        self.assertTrue(found_error, "Invalid date error not found")
