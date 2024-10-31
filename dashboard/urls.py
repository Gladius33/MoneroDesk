from django.urls import path
from .views import (
    user_dashboard_view, 
    admin_dashboard_view, 
    admin_settings_view, 
    manage_support_group,
    withdraw_xmr_view,
    search_ads_view,
)

app_name = 'dashboard'

urlpatterns = [
    path('user/', user_dashboard_view, name='user_dashboard'),
    path('admin/', admin_dashboard_view, name='admin_dashboard'),
    path('admin/settings/', admin_settings_view, name='admin_settings'),
    path('admin/manage_support/', manage_support_group, name='manage_support_group'),
    path('withdraw-xmr/', withdraw_xmr_view, name='withdraw_xmr'),
    path('search-ads/', search_ads_view, name='search_ads'),
]
