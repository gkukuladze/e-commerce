from django.contrib.auth import get_user_model
from rest_framework import serializers
from typing import Any
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer


class UserSerializer(serializers.ModelSerializer):
    """Serializer for the user object."""

    class Meta:
        model = get_user_model()
        fields = ['email', 'password', 'name']
        extra_kwargs = {'password': {'write_only': True, 'min_length': 5}}

    def create(self, validated_data):
        """Create and return a user with encrypted password."""
        user = get_user_model().objects.create_user(**validated_data)
        return user

    def update(self, instance, validated_data):
        """Update and return the user."""
        password = validated_data.pop(
            'password', None)
        user = super().update(instance, validated_data)

        if password:
            if len(password) < 5:
                raise serializers.ValidationError(
                    {"password": "Password must be at least 5 characters long."})
            user.set_password(password)
            user.save()

        return user


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):

    def validate(self, attrs: dict[str, Any]) -> dict[str, str]:
        data = super().validate(attrs)

        token = super().get_token(self.user)

        access_token = token.access_token

        access_token['email'] = self.user.email
        access_token['is_staff'] = self.user.is_staff
        access_token['is_superuser'] = self.user.is_superuser
        access_token['permissions'] = list(self.user.get_all_permissions())

        data['access'] = str(access_token)

        return data
