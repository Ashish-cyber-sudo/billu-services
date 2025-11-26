# job_portal/asgi.py
import os
import django
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from django.core.asgi import get_asgi_application
import job_app.routing

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "job_portal.settings")
django.setup()

application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": AuthMiddlewareStack(
        URLRouter(
            job_app.routing.websocket_urlpatterns
        )
    ),
})
