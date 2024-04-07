# app/api/views.py
import json
import os.path
import logging
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

logger = logging.getLogger(__name__)

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
    try:
        qdrant = QdrantConnection()
        qdrant.set_model(EMBEDDINGS_MODEL)
        
        # Assuming the data is sent in the format as the 'startups_demo.json' file's lines.
        obj = request.data
        description = obj.pop('description')
        obj["logo_url"] = obj.pop("images")
        obj["homepage_url"] = obj.pop("link")

        # Prepare the documents and payload for insertion
        documents = [description]
        payload = [obj]
        
        collection_name="1_SearchEngineGP"
        qdrant.insert_vector(collection_name, documents, payload)
        logger.info(f"Inserting into collection {collection_name} with documents: {documents} and payload: {payload}")
        return Response(
            {"message": "Data successfully inserted into vector database"},
            status=status.HTTP_201_CREATED
        )

    except Exception as e:
        return Response(
            {"error": f"Failed to insert data due to an internal error. {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
