from rest_framework.permissions import BasePermission
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.exceptions import AuthenticationFailed


class PatientJWTAuthentication(JWTAuthentication):
    def get_user(self, validated_token):
        if validated_token.get("type") != "patient":
            raise AuthenticationFailed("Invalid token type")
        return validated_token


class IsPatient(BasePermission):
    def has_permission(self, request, view):
        return bool(request.auth and request.auth.get("type") == "patient")
