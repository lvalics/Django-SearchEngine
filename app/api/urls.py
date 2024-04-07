"""
URL structure for the API/REST endpoints
"""
from django.urls import path
from . import views

urlpatterns = [
    path("", views.HelloWorldApiView.as_view(), name="hello_world"),
    path(
        "create-namespace/",
        views.create_qdrant_collection_name,
        name="create_namespace",
    ),
    path(
        "insert-data/",
        views.embed_data_into_vector_database,
        name="insert_data",
    ),
    path(
        "update-data/",
        views.update_data_into_vector_database,
        name="insert_data",
    ),
    path("search/", views.search_in_vector_database, name="search"),
]
