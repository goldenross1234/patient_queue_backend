from rest_framework.viewsets import ReadOnlyModelViewSet
from .models import QueueLog
from rest_framework.serializers import ModelSerializer

class LogSerializer(ModelSerializer):
    class Meta:
        model = QueueLog
        fields = "__all__"

class LogViewSet(ReadOnlyModelViewSet):
    queryset = QueueLog.objects.order_by("-timestamp")[:100]
    serializer_class = LogSerializer
