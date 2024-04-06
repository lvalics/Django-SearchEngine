from django.urls import path, include
from . import views

urlpatterns = [
    path("", views.HelloWorldApiView.as_view(), name="hello_world"),
]
