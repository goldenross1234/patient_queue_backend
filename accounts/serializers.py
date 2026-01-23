from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)

        # roles array
        roles = []

        if user.is_superuser:
            roles.append("admin")
        elif user.is_staff:
            roles.append("staff")

        # example: doctor via group
        if user.groups.filter(name="Doctor").exists():
            roles.append("doctor")

        token["roles"] = roles
        token["username"] = user.username

        return token
