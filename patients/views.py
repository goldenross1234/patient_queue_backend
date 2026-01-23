import random

from django.core.mail import send_mail
from rest_framework.response import Response
from rest_framework.decorators import (
    api_view,
    authentication_classes,
    permission_classes,
)

from .models import Patient, EmailOTP
from .tokens import get_patient_token
from .auth import PatientJWTAuthentication, IsPatient
from google.oauth2 import id_token
from google.auth.transport import requests
from django.conf import settings


@api_view(["POST"])
def send_otp(request):
    email = request.data.get("email")

    if not email:
        return Response({"error": "Email is required"}, status=400)

    code = f"{random.randint(100000, 999999)}"

    EmailOTP.objects.create(email=email, code=code)

    send_mail(
        "Your OTP Code",
        f"Your verification code is {code}",
        None,
        [email],
    )

    return Response({"message": "OTP sent"})


@api_view(["POST"])
def verify_otp(request):
    email = request.data.get("email")
    code = request.data.get("code")
    full_name = request.data.get("full_name")
    password = request.data.get("password")

    if not all([email, code, full_name, password]):
        return Response({"error": "Missing fields"}, status=400)

    otp = EmailOTP.objects.filter(
        email=email,
        code=code,
        used=False
    ).last()

    if not otp or otp.is_expired():
        return Response({"error": "Invalid or expired OTP"}, status=400)

    patient, created = Patient.objects.get_or_create(
        email=email,
        defaults={"full_name": full_name}
    )

    if created or not patient.password:
        patient.set_password(password)

    patient.is_verified = True
    patient.save()

    otp.used = True
    otp.save()

    return Response({"message": "Account verified"})


@api_view(["POST"])
def patient_login(request):
    email = request.data.get("email")
    password = request.data.get("password")

    if not email or not password:
        return Response({"error": "Missing credentials"}, status=400)

    try:
        patient = Patient.objects.get(email=email)
    except Patient.DoesNotExist:
        return Response({"error": "Invalid credentials"}, status=401)

    if not patient.is_verified:
        return Response({"error": "Email not verified"}, status=403)

    if not patient.check_password(password):
        return Response({"error": "Invalid credentials"}, status=401)

    token = get_patient_token(patient)

    return Response({
        "refresh": str(token),
        "access": str(token.access_token),
    })


@api_view(["GET"])
@authentication_classes([PatientJWTAuthentication])
@permission_classes([IsPatient])
def patient_dashboard(request):
    return Response({
        "message": "Welcome patient",
        "patient_id": request.auth["patient_id"],
        "email": request.auth["email"],
    })

@api_view(["POST"])
def google_login(request):
    token = request.data.get("token")

    if not token:
        return Response({"error": "Token missing"}, status=400)

    try:
        idinfo = id_token.verify_oauth2_token(
            token,
            requests.Request(),
            settings.GOOGLE_CLIENT_ID
        )
    except ValueError:
        return Response({"error": "Invalid Google token"}, status=400)

    email = idinfo.get("email")
    full_name = idinfo.get("name", "")

    patient, _ = Patient.objects.get_or_create(
        email=email,
        defaults={
            "full_name": full_name,
            "is_verified": True,
        }
    )

    patient.is_verified = True
    patient.save()

    jwt = get_patient_token(patient)

    return Response({
        "refresh": str(jwt),
        "access": str(jwt.access_token),
    })
