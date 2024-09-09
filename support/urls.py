from django.urls import path
from . import views

urlpatterns = [
    path('', views.support_dashboard, name='support_dashboard'),
    path('join/<int:support_id>/', views.join_chat, name='join_chat'),
    path('leave/<int:support_id>/', views.leave_chat, name='leave_chat'),
    path('archive/<int:support_id>/', views.archive_chat, name='archive_chat'),
]
