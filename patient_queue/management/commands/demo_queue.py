from django.core.management.base import BaseCommand
from django.utils.timezone import now
from patient_queue.models import QueueItem, QueueLog
from patient_queue.services import send_registration_email


class Command(BaseCommand):
    help = "Load demo OB-GYNE patients into today's queue"

    def add_arguments(self, parser):
        parser.add_argument("--reset", action="store_true")

    def handle(self, *args, **options):
        today = now().date()

        if options["reset"]:
            QueueItem.objects.filter(queue_date=today).delete()
            QueueLog.objects.filter(timestamp__date=today).delete()
            self.stdout.write(self.style.WARNING("Today's queue cleared"))

        patients = ["lala", "lele", "lili", "lolo", "lulu"]

        last = QueueItem.objects.filter(queue_date=today).order_by("-queue_number").first()
        next_number = 1 if not last else last.queue_number + 1

        for name in patients:
            item = QueueItem.objects.create(
                queue_number=next_number,
                queue_date=today,
                patient_name=name,
                email=f"{name}2026@yopmail.com",
            )

            send_registration_email(item.queue_number, item.email)

            QueueLog.objects.create(
                event="DEMO",
                message=f"Patient #{item.queue_number} loaded ({name})"
            )

            self.stdout.write(
                self.style.SUCCESS(
                    f"Added Patient #{item.queue_number} — {name}2026@yopmail.com"
                )
            )

            next_number += 1

        self.stdout.write(self.style.SUCCESS("Demo queue loaded successfully"))
