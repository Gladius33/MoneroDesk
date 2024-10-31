from django import forms
from .models import AdminSettings

class AdminSettingsForm(forms.ModelForm):
    class Meta:
        model = AdminSettings
        fields = ['fee_percentage', 'withdraw_fee_percentage', 'xmr_wallet_address']

    def __init__(self, *args, **kwargs):
        super(AdminSettingsForm, self).__init__(*args, **kwargs)
        
        # Custom labels
        self.fields['fee_percentage'].label = 'Transaction Fee (%)'
        self.fields['withdraw_fee_percentage'].label = 'Withdrawal Fee (%)'
        self.fields['xmr_wallet_address'].label = 'Monero Wallet Address for Fees'
        
        # Adding placeholder text for user guidance
        self.fields['fee_percentage'].widget.attrs.update({'placeholder': 'Enter the transaction fee as a percentage'})
        self.fields['withdraw_fee_percentage'].widget.attrs.update({'placeholder': 'Enter the withdrawal fee as a percentage'})
        self.fields['xmr_wallet_address'].widget.attrs.update({'placeholder': 'Enter the XMR wallet address for fee collection'})

    # Optional: Add form-level validation if needed
    def clean_fee_percentage(self):
        fee_percentage = self.cleaned_data.get('fee_percentage')
        if fee_percentage < 0 or fee_percentage > 100:
            raise forms.ValidationError('The transaction fee must be between 0% and 100%.')
        return fee_percentage

    def clean_withdraw_fee_percentage(self):
        withdraw_fee_percentage = self.cleaned_data.get('withdraw_fee_percentage')
        if withdraw_fee_percentage < 0 or withdraw_fee_percentage > 100:
            raise forms.ValidationError('The withdrawal fee must be between 0% and 100%.')
        return withdraw_fee_percentage
