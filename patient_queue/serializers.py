from rest_framework import serializers
from .models import QueueItem

class QueueItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = QueueItem
        fields = '__all__'
