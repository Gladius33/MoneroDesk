from django import forms
from django.contrib.auth.forms import PasswordChangeForm as DjangoPasswordChangeForm
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Profile
from .models import User

class UserProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['bio', 'profile_picture']

class EmailChangeForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['email']

class PasswordChangeForm(DjangoPasswordChangeForm):
    class Meta:
        model = User
        fields = ['password']

class SignupForm(UserCreationForm):
    referral_code = forms.CharField(max_length=20, required=False, help_text="Enter referral code (if any).")

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2', 'referral_code']


class XMRWithdrawForm(forms.Form):
    withdraw_address = forms.CharField(max_length=128, label='Monero Address')
    amount = forms.DecimalField(max_digits=16, decimal_places=8, label='Amount')
