from django import forms
from .models import Ad
from django.core.exceptions import ValidationError

class AdForm(forms.ModelForm):
    class Meta:
        model = Ad
        fields = [
            'title', 'description', 'type', 'crypto_currency', 'price', 'fiat_currency', 
            'min_amount', 'max_amount', 'payment_methods', 'location', 'payment_details',
            'dynamic_price', 'dynamic_price_value'
        ]
        labels = {
            'description': 'Description (optional but recommended: details about the payment method and contact information)',
            'title': 'Ad Title',
            'crypto_currency': 'Cryptocurrency (e.g., XMR)',
            'price': 'Price per unit (in fiat)',
            'fiat_currency': 'Fiat Currency (e.g., USD, EUR)',
            'min_amount': 'Minimum transaction amount',
            'max_amount': 'Maximum transaction amount',
            'payment_methods': 'Payment Methods (e.g., PayPal, SEPA, etc.)',
            'location': 'Location (optional)',
            'payment_details': 'Additional payment details (required if "Goods" or "Other" is selected)',
            'dynamic_price': 'Sell/Buy at Market Price',
            'dynamic_price_value': 'Dynamic Price Adjustment (%)'
        }

    def clean(self):
        cleaned_data = super().clean()
        ad_type = cleaned_data.get('type')
        min_amount = cleaned_data.get('min_amount')
        max_amount = cleaned_data.get('max_amount')
        price = cleaned_data.get('price')
        dynamic_price = cleaned_data.get('dynamic_price')
        dynamic_price_value = cleaned_data.get('dynamic_price_value')
        payment_method = cleaned_data.get('payment_methods')
        payment_details = cleaned_data.get('payment_details')

        # Ensure minimum amount is less than maximum amount
        if min_amount >= max_amount:
            raise ValidationError('The minimum amount must be less than the maximum amount.')

        # Validate 'sell' type: Check user's XMR balance
        if ad_type == 'sell':
            user = self.instance.user
            if user.profile.xmr_balance < max_amount:
                raise ValidationError('Insufficient XMR balance to cover the maximum amount for this ad.')

        # Ensure 'Goods' or 'Other' payment methods have additional details
        if payment_method in ['GOODS', 'OTHER'] and not payment_details:
            raise ValidationError(f'Please provide additional details for the payment method "{payment_method}".')

        # Ensure either fixed or dynamic price is set, not both
        if dynamic_price and price:
            raise ValidationError('You cannot set both a fixed price and a dynamic price.')

        # Ensure the dynamic price adjustment is within -15% to +15%
        if dynamic_price and not (-15 <= dynamic_price_value <= 15):
            raise ValidationError('Dynamic price adjustment must be between -15% and +15%.')

        return cleaned_data
