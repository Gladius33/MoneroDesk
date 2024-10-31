from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(r'ws/transaction/(?P<transaction_id>\w+)/$', consumers.TransactionConsumer.as_asgi()),
]
