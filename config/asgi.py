import os

from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter
from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.production")

django_asgi_app = get_asgi_application()

from apps.chat.routing import websocket_urlpatterns as chat_ws_urlpatterns  # noqa: E402
from apps.notifications.routing import websocket_urlpatterns as notifications_ws_urlpatterns  # noqa: E402
from common.ws_auth import JWTAuthMiddlewareStack  # noqa: E402

application = ProtocolTypeRouter(
    {
        "http": django_asgi_app,
        "websocket": JWTAuthMiddlewareStack(
            AuthMiddlewareStack(
                URLRouter(chat_ws_urlpatterns + notifications_ws_urlpatterns)
            )
        ),
    }
)
