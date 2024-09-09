from django import forms
from .models import Transaction

class BuyTransactionForm(forms.ModelForm):
    class Meta:
        model = Transaction
        fields = ['transaction_amount']

    def __init__(self, *args, **kwargs):
        self.ad = kwargs.pop('ad', None)
        super(BuyTransactionForm, self).__init__(*args, **kwargs)

    def clean_transaction_amount(self):
        transaction_amount = self.cleaned_data.get('transaction_amount')

        if not self.ad:
            raise forms.ValidationError("Annonce introuvable.")

        # Validation du montant par rapport à l'annonce
        if transaction_amount < self.ad.min_amount or transaction_amount > self.ad.max_amount:
            raise forms.ValidationError(f"Le montant doit être compris entre {self.ad.min_amount} et {self.ad.max_amount} XMR.")

        return transaction_amount
