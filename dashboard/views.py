from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.models import User, Group
from .models import AdminSettings
from .forms import AdminSettingsForm
from ads.models import Ad
from transactions.models import Transaction

@login_required
def user_dashboard_view(request):
    ads = Ad.objects.filter(user=request.user)
    transactions = Transaction.objects.filter(buyer=request.user) | Transaction.objects.filter(seller=request.user)
    return render(request, 'dashboard/user_dashboard.html', {'ads': ads, 'transactions': transactions})

@staff_member_required
def admin_dashboard_view(request):
    ads = Ad.objects.all()
    transactions = Transaction.objects.all()
    users = User.objects.all()
    return render(request, 'dashboard/admin_dashboard.html', {
        'ads': ads,
        'transactions': transactions,
        'users': users
    })

@staff_member_required
def manage_support_group(request):
    if request.method == 'POST':
        support_group = Group.objects.get(name='Support')
        for user in User.objects.all():
            if str(user.id) in request.POST.getlist('support_group'):
                support_group.user_set.add(user)
            else:
                support_group.user_set.remove(user)
        return redirect('admin_dashboard')

@staff_member_required
def admin_settings_view(request):
    settings, created = AdminSettings.objects.get_or_create(id=1)
    if request.method == 'POST':
        form = AdminSettingsForm(request.POST, instance=settings)
        if form.is_valid():
            form.save()
            return redirect('admin_dashboard')
    else:
        form = AdminSettingsForm(instance=settings)
    return render(request, 'dashboard/admin_settings.html', {'form': form})

from django.contrib.admin.views.decorators import staff_member_required

@login_required
@staff_member_required
def manage_referral_fees_view(request):
    if request.method == 'POST':
        referral_percentage = request.POST.get('referral_percentage')
        # Update the referral percentage setting
        set_referral_percentage(referral_percentage)
        messages.success(request, 'Referral percentage updated successfully.')
        return redirect('admin_dashboard')

    current_referral_percentage = get_referral_percentage()
    return render(request, 'dashboard/manage_referral_fees.html', {
        'current_referral_percentage': current_referral_percentage,
    })

@login_required
@staff_member_required
def manage_fee_exemptions_view(request):
    if request.method == 'POST':
        user_id = request.POST.get('user_id')
        user = User.objects.get(id=user_id)
        # Toggle the user's fee exemption status
        user.profile.is_first_100 = not user.profile.is_first_100
        user.profile.save()
        messages.success(request, f'User {user.username} fee exemption updated.')
        return redirect('admin_dashboard')

    exempted_users = Profile.objects.filter(is_first_100=True)
    return render(request, 'dashboard/manage_fee_exemptions.html', {'exempted_users': exempted_users})
