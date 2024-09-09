from django import forms
from .models import AdminSettings

class AdminSettingsForm(forms.ModelForm):
    class Meta:
        model = AdminSettings
        fields = ['fee_percentage', 'btc_wallet_address', 'xmr_wallet_address']
from django import forms
from .models import AdminSettings

class AdminSettingsForm(forms.ModelForm):
    class Meta:
        model = AdminSettings
        fields = ['fee_percentage', 'withdraw_fee_percentage', 'xmr_wallet_address']

    # Ajout des labels personnalisés si nécessaire
    def __init__(self, *args, **kwargs):
        super(AdminSettingsForm, self).__init__(*args, **kwargs)
        self.fields['fee_percentage'].label = 'Transaction Fee (%)'
        self.fields['withdraw_fee_percentage'].label = 'Withdrawal Fee (%)'
        self.fields['xmr_wallet_address'].label = 'Monero Wallet Address for Fees'
