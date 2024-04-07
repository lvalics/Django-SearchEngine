"""
This file contains the serializers for the API
"""
from rest_framework import serializers

class MessageSerializer(serializers.Serializer):
    message = serializers.CharField(max_length=200)
