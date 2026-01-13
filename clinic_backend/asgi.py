import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
import patient_queue.routing

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'clinic_backend.settings')

application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": AuthMiddlewareStack(
        URLRouter(
            patient_queue.routing.websocket_urlpatterns
        )
    ),
})
