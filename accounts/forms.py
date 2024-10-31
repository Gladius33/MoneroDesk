from django import forms
from django.contrib.auth.forms import PasswordChangeForm as DjangoPasswordChangeForm
from django.contrib.auth.forms import UserCreationForm
from .models import Profile, User

class UserProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['bio', 'profile_picture']
        labels = {
            'bio': 'Bio',
            'profile_picture': 'Profile Picture'
        }
        help_texts = {
            'bio': 'Tell us something about yourself.',
            'profile_picture': 'Upload a profile picture (optional).'
        }
        widgets = {
            'bio': forms.Textarea(attrs={'placeholder': 'Write a short bio...', 'rows': 3}),
        }

class EmailChangeForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['email']
        labels = {
            'email': 'Email Address'
        }
        help_texts = {
            'email': 'Enter a valid email address.'
        }

class PasswordChangeForm(DjangoPasswordChangeForm):
    class Meta:
        model = User
        fields = ['password']
        labels = {
            'password': 'New Password'
        }
        help_texts = {
            'password': 'Ensure your password is at least 8 characters long.'
        }

class SignupForm(UserCreationForm):
    referral_code = forms.CharField(
        max_length=20, 
        required=False, 
        help_text="Enter a referral code if you have one.",
        widget=forms.TextInput(attrs={'placeholder': 'Referral code (optional)'})
    )

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2', 'referral_code']
        labels = {
            'username': 'Username',
            'email': 'Email Address',
            'password1': 'Password',
            'password2': 'Confirm Password',
            'referral_code': 'Referral Code'
        }
        help_texts = {
            'username': 'Choose a unique username.',
            'email': 'Enter your email address.',
            'password1': 'Must be at least 8 characters.',
            'password2': 'Enter the same password as before, for verification.'
        }

class XMRWithdrawForm(forms.Form):
    withdraw_address = forms.CharField(
        max_length=128, 
        label='Monero Address', 
        help_text='Enter a valid Monero wallet address.',
        widget=forms.TextInput(attrs={'placeholder': 'Paste your Monero wallet address here'})
    )
    amount = forms.DecimalField(
        max_digits=16, 
        decimal_places=8, 
        label='Amount', 
        help_text='Enter the amount of XMR you wish to withdraw.',
        widget=forms.NumberInput(attrs={'placeholder': 'e.g., 1.23456789'})
    )
    
    def clean_withdraw_address(self):
        address = self.cleaned_data['withdraw_address']
        if not self.is_valid_monero_address(address):
            raise forms.ValidationError('Invalid Monero address format.')
        return address

    def is_valid_monero_address(self, address):
        """
        Validates the Monero address format (this is a simple check and could be expanded).
        """
        return address.startswith('4') and len(address) in [95, 106]
