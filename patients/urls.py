from django.urls import path
from .views import (
    send_otp,
    verify_otp,
    patient_login,
    google_login,
    patient_dashboard,
)

urlpatterns = [
    path("send-otp/", send_otp),
    path("verify-otp/", verify_otp),
    path("login/", patient_login),
     path("google-login/", google_login),
    path("dashboard/", patient_dashboard),
]
