# app/api/views.py
import json
import os.path
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework import permissions
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import api_view, permission_classes
from api.utils.qdrant_connection import QdrantConnection
from api.serializers import MessageSerializer
from app.settings import EMBEDDINGS_MODEL
from app.permissions import IsOwner

class HelloWorldApiView(APIView):
    """
    View to return "Hello World" response.
    """

    authentication_classes = (JWTAuthentication,)
    serializer_class = MessageSerializer
    permission_classes = [IsAuthenticated, IsOwner]

    def get(self, request, format=None):
        return Response({"message": "Hello World"}, status=status.HTTP_200_OK)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def create_qdrant_collection_name(request):
    """
    Create a new collection in Qdrant. Will create IDUser + namespace to be sure is unique/user specific.
    {
        "namespace": "SearchEngineGP",
        "vector_size": "1536"
    }
    """
    user = request.user
    collection_name = f"{user.id}_{request.data.get('collection_name')}"
    if not collection_name:
        return Response(
            {"error": "collection_name is required"}, status=status.HTTP_400_BAD_REQUEST
        )
    vector_size = request.data.get("vector_size", 1536)  # Default vector size

    try:
        qdrant = QdrantConnection()
        qdrant.create_collection(collection_name, vector_size)

    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    return Response(
        {"collection_name": collection_name}, status=status.HTTP_201_CREATED
    )


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def embed_data_into_vector_database(request):
    """
    Embed data into the vector database
    {
        "namespace": "SearchEngineGP",
        "vector_size": "1536"
    }
    """
    qdrant = QdrantConnection()
    qdrant.set_model(EMBEDDINGS_MODEL)

    payload_path = os.path.join("../../startups_demo.json")
    payload = []
    documents = []

    #     {
    #    "name":"Hyde Park Angels",
    #    "images":"https:\/\/d1qb2nb5cznatu.cloudfront.net\/startups\/i\/61114-35cd9d9689b70b4dc1d0b3c5f11c26e7-thumb_jpg.jpg?buster=1427395222",
    #    "alt":"Hyde Park Angels - ",
    #    "description":"Hyde Park Angels is the largest and most active angel group in the Midwest. With a membership of over 100 successful entrepreneurs, executives, and venture capitalists, the organization prides itself on providing critical strategic expertise to entrepreneurs and ...",
    #    "link":"http:\/\/hydeparkangels.com",
    #    "city":"Chicago"
    #     }

    with open(payload_path) as fd:
        for line in fd:
            obj = json.loads(line)
            # Rename fields to unified schema
            documents.append(obj.pop("description"))
            obj["logo_url"] = obj.pop("images")
            obj["homepage_url"] = obj.pop("link")
            payload.append(obj)
