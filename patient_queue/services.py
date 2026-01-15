from django.core.mail import send_mail

def send_registration_email(queue_number, email):
    send_mail(
        subject="You are in the OB-GYNE Clinic Queue",
        message=f"""
Hello Patient #{queue_number},

You have been successfully added to today's queue.

You will receive another email when your number is being served.

OB-GYNE Clinic
""",
        from_email=None,
        recipient_list=[email],
        fail_silently=True,
    )
