from django.urls import path
from .views import chat_room_view, request_support, leave_support

urlpatterns = [
    path('room/<int:transaction_pk>/', chat_room_view, name='chat_room'),
    path('room/<int:transaction_pk>/request_support/', request_support, name='request_support'),
    path('room/<int:transaction_pk>/leave_support/', leave_support, name='leave_support'),
]
