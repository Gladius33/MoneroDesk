from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .forms import UserProfileForm, EmailChangeForm, PasswordChangeForm, XMRWithdrawForm, SignupForm
from django.contrib.auth import update_session_auth_hash
from monero_app.services import MoneroService
from decimal import Decimal
from django.contrib import messages
from django.conf import settings
from .models import User, Profile


@login_required
def profile_view(request):
    profile = request.user.profile
    monero_service = MoneroService()

    # Fetch real-time Monero balance and transactions
    try:
        monero_data = monero_service.get_subaddress_balance_and_transactions(profile.user_subaddress)
        xmr_balance = monero_data['balance']
        transactions = monero_data['transactions']
    except Exception as e:
        messages.error(request, "Could not retrieve Monero data. Please try again later.")
        xmr_balance = profile.xmr_balance
        transactions = []

    if request.method == 'POST':
        profile_form = UserProfileForm(request.POST, request.FILES, instance=profile)
        email_form = EmailChangeForm(request.POST, instance=request.user)
        password_form = PasswordChangeForm(request.user, request.POST)
        if profile_form.is_valid() and email_form.is_valid() and password_form.is_valid():
            profile_form.save()
            email_form.save()
            password_form.save()
            update_session_auth_hash(request, password_form.user)
            messages.success(request, "Profile updated successfully!")
            return redirect('profile')
    else:
        profile_form = UserProfileForm(instance=profile)
        email_form = EmailChangeForm(instance=request.user)
        password_form = PasswordChangeForm(request.user)

    return render(request, 'accounts/profile.html', {
        'profile_form': profile_form,
        'email_form': email_form,
        'password_form': password_form,
        'xmr_balance': xmr_balance,
        'xmr_wallet_address': profile.user_subaddress,
        'transactions': transactions
    })


@login_required
def withdraw_xmr_view(request):
    profile = request.user.profile

    if request.method == 'POST':
        form = XMRWithdrawForm(request.POST)
        if form.is_valid():
            withdraw_address = form.cleaned_data['withdraw_address']
            amount = form.cleaned_data['amount']
            fee_percentage = get_withdraw_fee_percentage()

            try:
                # Process withdrawal via MoneroService
                profile.withdraw_monero(amount, withdraw_address, fee_percentage)
                messages.success(request, "Withdrawal is being processed. You will receive a confirmation once the transaction is complete.")
            except ValueError as e:
                messages.error(request, str(e))
            except Exception as e:
                messages.error(request, "An unexpected error occurred. Please try again later.")
            return redirect('profile')
    else:
        form = XMRWithdrawForm()
    
    return render(request, 'accounts/withdraw_xmr.html', {'form': form, 'xmr_balance': profile.xmr_balance})


def signup_view(request):
    if request.method == 'POST':
        form = SignupForm(request.POST)
        if form.is_valid():
            user = form.save()
            referral_code = form.cleaned_data.get('referral_code')
            if referral_code:
                referrer = User.objects.filter(profile__referral_code=referral_code).first()
                if referrer:
                    referrer.profile.referred_users.add(user)
                    referrer.profile.save()

            # Create a Monero subaddress for the new user
            monero_service = MoneroService()
            try:
                subaddress = monero_service.create_user_subaddress(label=user.username)
                if not subaddress:
                    raise ValueError("Failed to create Monero subaddress.")
            except Exception as e:
                messages.error(request, f"Error creating Monero subaddress: {e}")
                return redirect('accounts:signup')

            # Create a profile and store the subaddress
            Profile.objects.create(user=user, user_subaddress=subaddress['address'])
            messages.success(request, "Account created successfully with Monero subaddress!")
            return redirect('login')
    else:
        form = SignupForm()
    
    return render(request, 'accounts/signup.html', {'form': form})


# Function to get the withdrawal fee percentage
def get_withdraw_fee_percentage():
    return settings.WITHDRAW_FEE_PERCENTAGE if hasattr(settings, 'WITHDRAW_FEE_PERCENTAGE') else Decimal('0.01')
