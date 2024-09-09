from django.urls import path
from .views import signup_view, profile_view, withdraw_xmr_view
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('signup/', signup_view, name='signup'),
    path('login/', auth_views.LoginView.as_view(template_name='accounts/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('profile/', profile_view, name='profile'),
    path('withdraw-xmr/', withdraw_xmr_view, name='withdraw_xmr'),
]
