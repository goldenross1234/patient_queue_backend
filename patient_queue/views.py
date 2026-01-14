from rest_framework import viewsets, status
from rest_framework.response import Response
from django.utils.timezone import now
from .models import QueueItem, QueueLog
from .serializers import QueueItemSerializer
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from django.core.mail import send_mail
import time


class QueueViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = QueueItemSerializer

    def get_queryset(self):
        today = now().date()
        return QueueItem.objects.filter(queue_date=today).order_by("queue_number")

    def create(self, request):
        today = now().date()

        last = QueueItem.objects.filter(queue_date=today).order_by("-queue_number").first()
        next_number = 1 if not last else last.queue_number + 1

        item = QueueItem.objects.create(
            queue_number=next_number,
            queue_date=today,
            patient_name=request.data["patient_name"],
            email=request.data["email"],
        )

        return Response(QueueItemSerializer(item).data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=["post"])
    def serve_next(self, request):
        today = now().date()

        QueueLog.objects.create(event="CALL", message="Staff clicked Serve Next")

        QueueItem.objects.filter(queue_date=today, status="serving").update(status="done")

        next_patient = QueueItem.objects.filter(
            queue_date=today, status="waiting"
        ).order_by("queue_number").first()

        if not next_patient:
            return Response({"message": "No more patients in queue"})

        channel_layer = get_channel_layer()

        QueueLog.objects.create(event="CALLING", message="Broadcasting calling message")

        async_to_sync(channel_layer.group_send)(
            "queue",
            {"type": "queue_update", "data": {"state": "calling"}},
        )

        time.sleep(2)

        next_patient.status = "serving"
        next_patient.save()

        send_mail(
            "You are now being served",
            f"Hello {next_patient.patient_name}, your number {next_patient.queue_number} is now being served.",
            None,
            [next_patient.email],
            fail_silently=True,
        )

        for p in QueueItem.objects.filter(queue_date=today, status="waiting"):
            send_mail(
                f"Now Serving #{next_patient.queue_number}",
                f"The clinic is now serving {next_patient.patient_name}. Please prepare.",
                None,
                [p.email],
                fail_silently=True,
            )

        QueueLog.objects.create(event="EMAIL", message="Email broadcast completed")

        async_to_sync(channel_layer.group_send)(
            "queue",
            {
                "type": "queue_update",
                "data": {
                    "state": "serving",
                    "queue_number": next_patient.queue_number,
                    "patient_name": next_patient.patient_name,
                },
            },
        )

        QueueLog.objects.create(
            event="SERVING", message=f"Now serving {next_patient.patient_name}"
        )

        return Response(
            {
                "queue_number": next_patient.queue_number,
                "patient_name": next_patient.patient_name,
            }
        )

    @action(detail=False, methods=["get"])
    def current(self, request):
        today = now().date()
        current = QueueItem.objects.filter(queue_date=today, status="serving").first()

        if not current:
            return Response({"queue_number": None, "patient_name": None})

        return Response(
            {"queue_number": current.queue_number, "patient_name": current.patient_name}
        )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def me(request):
    user = request.user
    role = user.groups.first().name if user.groups.exists() else "Staff"

    return Response({"username": user.username, "role": role})
