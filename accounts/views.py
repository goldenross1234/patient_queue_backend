from rest_framework_simplejwt.views import TokenObtainPairView
from .serializers import CustomTokenObtainPairSerializer

class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer

# @permission_classes([IsAuthenticated])
# def staff_only_view(request):
#     assert request.user.is_staff
