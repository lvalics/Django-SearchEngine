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
    logger.info(f"Received request data: {request.data}")
    if not request.data:
        return Response(
            {"error": "No data provided"}, status=status.HTTP_400_BAD_REQUEST
        )

    qdrant = QdrantConnection()
    qdrant.set_model(EMBEDDINGS_MODEL)

    documents = []
    payload = []

    # Ensure request.data is correctly interpreted as a list of dictionaries
    # Ensure request.data is correctly interpreted as a list of dictionaries
    data = request.data if isinstance(request.data, list) else [request.data]  # Wrap single dict in a list

    for item in data:  # Process each item in the JSON array received in the request body
        # Ensure each item is a dictionary
        if not isinstance(item, dict):
            continue  # Skip items that are not dictionaries
        # Assuming each item in the request data is a dictionary like the ones in startups_demo.json
        if "description" in item:
            documents.append({"vector": item.pop("description")})  # Adjusted to match expected document structure
        if "images" in item:
            item["logo_url"] = item.pop("images")
        if "link" in item:
            item["homepage_url"] = item.pop("link")
        payload.append(item)

    logger.debug(f"Prepared documents for insertion: {documents}")
    logger.debug(f"Prepared payload for insertion: {payload}")

    # Here you should insert the documents and payload into the vector database
    # This is a placeholder for the actual insertion logic
    collection_name="1_SearchEngineGP"
    logger.info(f"Inserting data into collection {collection_name} with documents: {documents} and payload: {payload}")
    qdrant.insert_vector(collection_name, documents, payload)

    return Response(
        {"message": "Data successfully inserted into vector database"},
        status=status.HTTP_201_CREATED
    )
