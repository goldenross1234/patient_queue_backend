from django.urls import path
from rest_framework.routers import DefaultRouter
from .views import QueueViewSet, me
from .log_views import LogViewSet
from accounts.views import CustomTokenObtainPairView

router = DefaultRouter()
router.register("queue", QueueViewSet, basename="queue")
router.register("logs", LogViewSet, basename="logs")

urlpatterns = router.urls + [
    path("me/", me),
    path("api/token/", CustomTokenObtainPairView.as_view(), name="token"),
]
