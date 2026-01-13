from rest_framework import viewsets, status
from rest_framework.response import Response
from django.utils.timezone import now
from .models import QueueItem
from .serializers import QueueItemSerializer
from rest_framework.decorators import action
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from django.core.mail import send_mail

class QueueViewSet(viewsets.ModelViewSet):
    serializer_class = QueueItemSerializer

    def get_queryset(self):
        today = now().date()
        return QueueItem.objects.filter(queue_date=today).order_by("queue_number")

    def create(self, request):
        today = now().date()

        last = QueueItem.objects.filter(queue_date=today).order_by('-queue_number').first()
        next_number = 1 if not last else last.queue_number + 1

        item = QueueItem.objects.create(
            queue_number=next_number,
            queue_date=today,
            patient_name=request.data["patient_name"],
            email=request.data["email"]
        )

        serializer = QueueItemSerializer(item)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=["post"])
    def serve_next(self, request):
        today = now().date()

        # Mark current serving as done
        QueueItem.objects.filter(queue_date=today, status="serving").update(status="done")

        # Get next waiting patient
        next_patient = QueueItem.objects.filter(
            queue_date=today,
            status="waiting"
        ).order_by("queue_number").first()

        if not next_patient:
            return Response({"message": "No more patients in queue"})

        next_patient.status = "serving"
        next_patient.save()
        
        # send_mail(
        #     subject="You are now being served",
        #     message=f"Hello {next_patient.patient_name},\n\nYour queue number {next_patient.queue_number} is now being served. Please proceed to the doctor's room.\n\nOB-GYNE Clinic",
        #     from_email=None,
        #     recipient_list=[next_patient.email],
        #     fail_silently=True,
        # )
        

        # Email to the patient being served
        send_mail(
            subject="You are now being served",
            message=f"""
        Hello {next_patient.patient_name},

        Your queue number {next_patient.queue_number} is now being served.
        Please proceed to the doctor's room.

        OB-GYNE Clinic
        """,
            from_email=None,
            recipient_list=[next_patient.email],
            fail_silently=True,
        )

        # Notify all waiting patients
        waiting_patients = QueueItem.objects.filter(
            queue_date=today,
            status="waiting"
        )

        for patient in waiting_patients:
            send_mail(
                subject=f"Now Serving: #{next_patient.queue_number}",
                message=f"""
        Hello {patient.patient_name},

        The clinic is now serving queue number {next_patient.queue_number}
        ({next_patient.patient_name}).

        Please be ready. Your turn is approaching.

        OB-GYNE Clinic
        """,
                from_email=None,
                recipient_list=[patient.email],
                fail_silently=True,
            )



        # 🔥 Broadcast to WebSocket
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            "queue",
            {
                "type": "queue_update",
                "data": {
                    "queue_number": next_patient.queue_number,
                    "patient_name": next_patient.patient_name,
                },
            }
        )

        return Response({
            "queue_number": next_patient.queue_number,
            "patient_name": next_patient.patient_name
        })

@action(detail=False, methods=["get"])
def current(self, request):
    today = now().date()

    current = QueueItem.objects.filter(
        queue_date=today,
        status="serving"
    ).first()

    if not current:
        return Response({"queue_number": None, "patient_name": None})

    return Response({
        "queue_number": current.queue_number,
        "patient_name": current.patient_name
    })
