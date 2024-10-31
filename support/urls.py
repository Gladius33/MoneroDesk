from django.urls import path
from . import views

urlpatterns = [
    path('', views.support_dashboard, name='support_dashboard'),  # Dashboard view
    path('join/<int:support_id>/', views.join_chat, name='join_chat'),  # Joining a chat
    path('leave/<int:support_id>/', views.leave_chat, name='leave_chat'),  # Leaving a chat
    path('archive/<int:support_id>/', views.archive_chat, name='archive_chat'),  # Archiving a chat
    path('cancel/<int:support_id>/', views.cancel_transaction, name='cancel_transaction'),  # Support canceling a transaction
    path('validate/<int:support_id>/', views.validate_transaction, name='validate_transaction'),  # Support validating a transaction
]
