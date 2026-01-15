from rest_framework import viewsets, status
from rest_framework.response import Response
from django.utils.timezone import now
from .models import QueueItem, QueueLog
from .serializers import QueueItemSerializer
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
import time
from django.core.mail import send_mail

from .services import send_registration_email


class QueueViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = QueueItemSerializer

    def get_queryset(self):
        today = now().date()
        return QueueItem.objects.filter(queue_date=today).order_by("queue_number")

    # -------------------------------
    # ADD PATIENT
    # -------------------------------
    def create(self, request):
        today = now().date()

        last = QueueItem.objects.filter(queue_date=today).order_by("-queue_number").first()
        next_number = 1 if not last else last.queue_number + 1

        item = QueueItem.objects.create(
            queue_number=next_number,
            queue_date=today,
            patient_name=request.data.get("patient_name", ""),
            email=request.data["email"],
        )

        # Shared registration email
        send_registration_email(item.queue_number, item.email)

        QueueLog.objects.create(
            event="ADD",
            message=f"Patient #{item.queue_number} added to queue"
        )

        return Response(QueueItemSerializer(item).data, status=status.HTTP_201_CREATED)

    # -------------------------------
    # SERVE NEXT
    # -------------------------------
    @action(detail=False, methods=["post"])
    def serve_next(self, request):
        today = now().date()

        QueueLog.objects.create(event="CALL", message="Staff clicked Serve Next")

        # Finish current
        QueueItem.objects.filter(queue_date=today, status="serving").update(status="done")

        # Get next
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

        # Email the current patient
        send_mail(
            subject="You are now being served",
            message=f"""
Hello Patient #{next_patient.queue_number},

You are now being served.
Please proceed to the doctor's room.

OB-GYNE Clinic
""",
            from_email=None,
            recipient_list=[next_patient.email],
            fail_silently=True,
        )

        # All waiting patients
        waiting = QueueItem.objects.filter(queue_date=today, status="waiting")

        # Pre-alert the next
        next_in_line = waiting.order_by("queue_number").first()

        if next_in_line:
            send_mail(
                subject="You are next in line",
                message=f"""
Hello Patient #{next_in_line.queue_number},

You are next after Patient #{next_patient.queue_number}.

Please be ready and stay near the clinic.

OB-GYNE Clinic
""",
                from_email=None,
                recipient_list=[next_in_line.email],
                fail_silently=True,
            )

        # Broadcast to all other waiting patients
        others = waiting.exclude(id=next_in_line.id) if next_in_line else waiting

        for p in others:
            send_mail(
                subject=f"Now Serving Patient #{next_patient.queue_number}",
                message=f"""
Hello Patient #{p.queue_number},

The clinic is now serving Patient #{next_patient.queue_number}.

Please stay alert for your turn.

OB-GYNE Clinic
""",
                from_email=None,
                recipient_list=[p.email],
                fail_silently=True,
            )

        QueueLog.objects.create(
            event="EMAIL",
            message=f"Current, next, and waiting patients notified for Patient #{next_patient.queue_number}"
        )

        # WebSocket broadcast
        async_to_sync(channel_layer.group_send)(
            "queue",
            {
                "type": "queue_update",
                "data": {
                    "state": "serving",
                    "queue_number": next_patient.queue_number,
                    "patient_name": f"Patient #{next_patient.queue_number}",
                },
            },
        )

        QueueLog.objects.create(
            event="SERVING",
            message=f"Now serving Patient #{next_patient.queue_number}"
        )

        return Response(
            {
                "queue_number": next_patient.queue_number,
                "patient_name": f"Patient #{next_patient.queue_number}",
            }
        )

    # -------------------------------
    # CURRENT
    # -------------------------------
    @action(detail=False, methods=["get"])
    def current(self, request):
        today = now().date()
        current = QueueItem.objects.filter(queue_date=today, status="serving").first()

        if not current:
            return Response({"queue_number": None, "patient_name": None})

        return Response(
            {
                "queue_number": current.queue_number,
                "patient_name": f"Patient #{current.queue_number}",
            }
        )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def me(request):
    user = request.user
    role = user.groups.first().name if user.groups.exists() else "Staff"
    return Response({"username": user.username, "role": role})
