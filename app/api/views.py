# todo/todo_api/views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from .serializers import MessageSerializer
from rest_framework import status
from rest_framework import permissions
from rest_framework_simplejwt.authentication import JWTAuthentication
from app.permissions import IsOwner
from rest_framework.permissions import IsAuthenticated


class HelloWorldApiView(APIView):
    """
    View to return "Hello World" response.
    """

    authentication_classes = (JWTAuthentication,)
    serializer_class = MessageSerializer
    permission_classes = [IsAuthenticated, IsOwner]

    def get(self, request, format=None):
        return Response({"message": "Hello World"}, status=status.HTTP_200_OK)
