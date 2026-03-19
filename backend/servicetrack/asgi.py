"""
ASGI config for department project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/4.2/howto/deployment/asgi/
"""

import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'servicetrack.settings')

django_asgi_app = get_asgi_application()

from servicedesk.routing import websocket_urlpatterns as servicedesk_ws
from notifications.routing import websocket_urlpatterns as notifications_ws

application = ProtocolTypeRouter({
    'http': django_asgi_app,
    'websocket': AuthMiddlewareStack(
        URLRouter(
            servicedesk_ws + notifications_ws
        )
    ),
})
