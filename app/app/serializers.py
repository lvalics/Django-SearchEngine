"""
This file contains the serializers for the API
"""
from djoser.serializers import (
    UserCreateSerializer as BaseUserSerializer,
)


class UserCreateSerializer(BaseUserSerializer):
    """
    UserCreateSerializer
    """
    class Meta(BaseUserSerializer.Meta):
        """
        Meta(BaseUserSerializer.Meta)
        """
        fields = ["id", "email", "username", "password"]
