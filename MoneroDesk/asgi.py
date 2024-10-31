import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from chat.routing import websocket_urlpatterns as chat_websocket_urlpatterns
from transactions.routing import websocket_urlpatterns as transaction_websocket_urlpatterns

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'MoneroDesk.settings')

application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": AuthMiddlewareStack(
        URLRouter(
            chat_websocket_urlpatterns + transaction_websocket_urlpatterns
        )
    ),
})
