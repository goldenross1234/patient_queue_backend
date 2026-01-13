from django.contrib import admin
from .models import QueueItem

@admin.register(QueueItem)
class QueueItemAdmin(admin.ModelAdmin):
    list_display = ('queue_number', 'patient_name', 'status', 'queue_date', 'created_at')
    list_filter = ('status', 'queue_date')
    ordering = ('queue_date', 'queue_number')
