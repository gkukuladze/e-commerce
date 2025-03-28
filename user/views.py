"""
Views for the user API.
"""
from rest_framework import generics
from user.serializers import UserSerializer
from .serializers import CustomTokenObtainPairSerializer
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework.permissions import AllowAny


class CreateUserView(generics.CreateAPIView):
    """Create a new user in the system."""
    serializer_class = UserSerializer
    permission_classes = [AllowAny]


class ManageUserView(generics.RetrieveAPIView):
    """Manage the authenticated user."""
    serializer_class = UserSerializer

    def get_object(self):
        """Retrieve and return the authenticated user."""
        return self.request.user


class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer
