from rest_framework.routers import DefaultRouter
from .views import QueueViewSet
from .log_views import LogViewSet   # ← THIS WAS MISSING

router = DefaultRouter()
router.register("queue", QueueViewSet, basename="queue")
router.register("logs", LogViewSet, basename="logs")

urlpatterns = router.urls
