# todo/todo_api/views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework import permissions
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework import permissions
from rest_framework_simplejwt.authentication import JWTAuthentication

class HelloWorldApiView(APIView):
    """
    View to return "Hello World" response.
    """
    def get(self, request, format=None):
        return Response({"message": "Hello World"}, status=status.HTTP_200_OK)
