import os
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from django.core.asgi import get_asgi_application
import job_app.routing

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'job_portal.settings')

django_app = get_asgi_application()

application = ProtocolTypeRouter({
    "http": django_app,
    "websocket": AuthMiddlewareStack(
        URLRouter(job_app.routing.websocket_urlpatterns)
    ),
})
