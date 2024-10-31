from decimal import Decimal
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.models import User, Group
from django.contrib import messages
from ads.models import Ad
from .models import AdminSettings
from .forms import AdminSettingsForm
from accounts.models import Profile  # Profiles are managed in the accounts app
from transactions.models import Transaction  # Assurez-vous que Transaction est correctement importé ici
from django.core.paginator import Paginator
from django.db.models import Q
from monero_app.services import MoneroService


@login_required
def user_dashboard_view(request):
    """
    User-specific dashboard displaying their ads and transactions.
    """
    ads = Ad.objects.filter(user=request.user)
    transactions = Transaction.objects.filter(buyer=request.user) | Transaction.objects.filter(seller=request.user)

    # Adding pagination for ads and transactions
    ads_paginator = Paginator(ads, 10)  # Show 10 ads per page
    transactions_paginator = Paginator(transactions, 10)  # Show 10 transactions per page
    
    page_number_ads = request.GET.get('ads_page')
    page_number_transactions = request.GET.get('transactions_page')

    ads_page_obj = ads_paginator.get_page(page_number_ads)
    transactions_page_obj = transactions_paginator.get_page(page_number_transactions)

    return render(request, 'dashboard/user_dashboard.html', {
        'ads': ads_page_obj,
        'transactions': transactions_page_obj
    })


@staff_member_required
def admin_dashboard_view(request):
    """
    Admin-specific dashboard that gives an overview of all ads, transactions, and users.
    """
    ads = Ad.objects.all()
    transactions = Transaction.objects.all()
    users = User.objects.all()

    # Pagination for admin overview
    ads_paginator = Paginator(ads, 10)
    transactions_paginator = Paginator(transactions, 10)
    users_paginator = Paginator(users, 10)

    page_number_ads = request.GET.get('ads_page')
    page_number_transactions = request.GET.get('transactions_page')
    page_number_users = request.GET.get('users_page')

    ads_page_obj = ads_paginator.get_page(page_number_ads)
    transactions_page_obj = transactions_paginator.get_page(page_number_transactions)
    users_page_obj = users_paginator.get_page(page_number_users)

    return render(request, 'dashboard/admin_dashboard.html', {
        'ads': ads_page_obj,
        'transactions': transactions_page_obj,
        'users': users_page_obj
    })


@staff_member_required
def manage_support_group(request):
    """
    View for managing the Support Group.
    """
    support_group = Group.objects.get(name='Support')
    if request.method == 'POST':
        selected_users = request.POST.getlist('support_group')
        for user in User.objects.all():
            if str(user.id) in selected_users:
                support_group.user_set.add(user)
            else:
                support_group.user_set.remove(user)
        messages.success(request, "Support group updated successfully.")
        return redirect('admin_dashboard')
    
    return render(request, 'dashboard/manage_support_group.html', {
        'users': User.objects.all(),
        'support_group': support_group.user_set.all()
    })


@staff_member_required
def admin_settings_view(request):
    """
    View to manage admin settings for fees and other configurations.
    """
    settings, created = AdminSettings.objects.get_or_create(id=1)
    if request.method == 'POST':
        form = AdminSettingsForm(request.POST, instance=settings)
        if form.is_valid():
            form.save()
            messages.success(request, "Settings updated successfully.")
            return redirect('admin_dashboard')
    else:
        form = AdminSettingsForm(instance=settings)
    
    return render(request, 'dashboard/admin_settings.html', {'form': form})


@staff_member_required
def manage_referral_fees_view(request):
    """
    View to manage referral fees in the admin dashboard.
    """
    if request.method == 'POST':
        referral_percentage = request.POST.get('referral_percentage')
        AdminSettings.set_referral_percentage(referral_percentage)
        messages.success(request, 'Referral percentage updated successfully.')
        return redirect('admin_dashboard')

    current_referral_percentage = AdminSettings.get_referral_percentage()
    return render(request, 'dashboard/manage_referral_fees.html', {
        'current_referral_percentage': current_referral_percentage,
    })


@staff_member_required
def manage_fee_exemptions_view(request):
    """
    View to manage fee exemptions for certain users (e.g., first 100 users).
    """
    if request.method == 'POST':
        user_id = request.POST.get('user_id')
        user = User.objects.get(id=user_id)
        user.profile.is_first_100 = not user.profile.is_first_100
        user.profile.save()
        messages.success(request, f'User {user.username} fee exemption updated.')
        return redirect('admin_dashboard')

    exempted_users = Profile.objects.filter(is_first_100=True)
    return render(request, 'dashboard/manage_fee_exemptions.html', {'exempted_users': exempted_users})


@login_required
def search_ads_view(request):
    """
    View to search for ads based on filters (e.g., buy/sell, amount, user).
    """
    query = request.GET.get('q', '')
    ad_type = request.GET.get('type', '')
    min_amount = request.GET.get('min_amount')
    max_amount = request.GET.get('max_amount')
    user_id = request.GET.get('user')
    created_after = request.GET.get('created_after')
    created_before = request.GET.get('created_before')
    fiat_currency = request.GET.get('fiat_currency', '')
    payment_method = request.GET.get('payment_method', '')

    ads = Ad.objects.all()

    # Search by title or description
    if query:
        ads = ads.filter(Q(title__icontains=query) | Q(description__icontains=query))

    # Filter by type (buy/sell)
    if ad_type:
        ads = ads.filter(type=ad_type)

    # Filter by amount range
    if min_amount:
        ads = ads.filter(amount__gte=min_amount)
    if max_amount:
        ads = ads.filter(amount__lte=max_amount)

    # Filter by user (seller/buyer)
    if user_id:
        ads = ads.filter(user__id=user_id)

    # Filter by creation date range
    if created_after:
        ads = ads.filter(created_at__gte=created_after)
    if created_before:
        ads = ads.filter(created_at__lte=created_before)

    # Filter by fiat currency
    if fiat_currency:
        ads = ads.filter(fiat_currency__icontains=fiat_currency)

    # Filter by payment method
    if payment_method:
        ads = ads.filter(payment_method__icontains=payment_method)

    # Pagination for filtered results
    paginator = Paginator(ads, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # For users list in filter dropdown (optional)
    users = User.objects.all()

    return render(request, 'dashboard/search_ads.html', {
        'ads': page_obj,
        'query': query,
        'ad_type': ad_type,
        'min_amount': min_amount,
        'max_amount': max_amount,
        'user_id': user_id,
        'created_after': created_after,
        'created_before': created_before,
        'fiat_currency': fiat_currency,
        'payment_method': payment_method,
        'users': users,  # For user filtering dropdown
    })


@login_required
def withdraw_xmr_view(request):
    """
    Handles Monero (XMR) withdrawal from the user's wallet to an external address.
    """
    if request.method == 'POST':
        xmr_withdraw_address = request.POST.get('xmr_withdraw_address')
        xmr_amount = request.POST.get('xmr_amount')

        if not xmr_withdraw_address or not xmr_amount:
            messages.error(request, "Please provide a valid withdrawal address and amount.")
            return redirect('user_dashboard')

        try:
            xmr_amount = Decimal(xmr_amount)
            if xmr_amount <= 0:
                raise ValueError("Invalid amount")

            monero_service = MoneroService()
            user_balance = monero_service.get_subaddress_balance_and_transactions(
                request.user.profile.subaddress_index
            )['unlocked_balance']

            if xmr_amount > user_balance:
                messages.error(request, "Insufficient balance.")
                return redirect('user_dashboard')

            # Process the withdrawal to an external address
            tx_hash = monero_service.send_xmr(
                to_address=xmr_withdraw_address, 
                amount=xmr_amount,
                internal=False
            )

            if tx_hash:
                messages.success(
                    request, f"Withdrawal of {xmr_amount} XMR to {xmr_withdraw_address} was successful. Transaction hash: {tx_hash}"
                )
            else:
                messages.error(request, "An error occurred during the withdrawal process.")
                
            return redirect('user_dashboard')

        except Exception as e:
            messages.error(request, f"Error processing withdrawal: {str(e)}")
            return redirect('user_dashboard')

    return render(request, 'dashboard/withdraw_xmr.html')
