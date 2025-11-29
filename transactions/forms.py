from django import forms

class TransactionForm(forms.Form):
    account_number = forms.CharField(
        label='Account Number',
        max_length=20,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter account number'})
    )
    transaction_type = forms.ChoiceField(
        choices=[('deposit', 'Deposit'), ('withdrawal', 'Withdrawal')],
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    amount = forms.DecimalField(
        min_value=0.01,
        max_digits=15,
        decimal_places=2,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'})
    )
    description = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Optional description'})
    )

class TransferForm(forms.Form):
    source_account = forms.ModelChoiceField(
        queryset=None,
        label='From Account',
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    target_account_number = forms.CharField(
        label='To Account Number',
        max_length=20,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter destination account number'})
    )
    amount = forms.DecimalField(
        min_value=0.01,
        max_digits=15,
        decimal_places=2,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'})
    )
    description = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Optional description'})
    )

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if user and hasattr(user, 'client'):
            self.fields['source_account'].queryset = user.client.accounts.all()
