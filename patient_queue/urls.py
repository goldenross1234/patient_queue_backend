from rest_framework.routers import DefaultRouter
from .views import QueueViewSet

router = DefaultRouter()
router.register("queue", QueueViewSet, basename="queue")

urlpatterns = router.urls
