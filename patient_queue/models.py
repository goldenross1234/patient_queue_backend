from django.db import models

class QueueItem(models.Model):
    STATUS_CHOICES = (
        ('waiting', 'Waiting'),
        ('serving', 'Serving'),
        ('done', 'Done'),
        ('skipped', 'Skipped'),
    )

    queue_number = models.PositiveIntegerField()
    queue_date = models.DateField(auto_now_add=True)

    patient_name = models.CharField(max_length=100)
    email = models.EmailField()

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='waiting')

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['queue_number']
        unique_together = ('queue_number', 'queue_date')

    def __str__(self):
        return f"{self.queue_date} - {self.queue_number} - {self.patient_name}"

class QueueLog(models.Model):
    timestamp = models.DateTimeField(auto_now_add=True)
    event = models.CharField(max_length=50)
    message = models.TextField()

    def __str__(self):
        return f"{self.timestamp} - {self.event}"
