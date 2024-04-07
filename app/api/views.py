# app/api/views.py
import json
import uuid
import os.path
import logging
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework import permissions
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import api_view, permission_classes
from django.http import JsonResponse
from api.utils.qdrant_connection import NeuralSearcher
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
        "namespace": "SearchEngineGP"
    }
    """
    user = request.user
    collection_name = f"{user.id}_{request.data.get('collection_name')}"
    if not collection_name:
        return Response(
            {"error": "collection_name is required"}, status=status.HTTP_400_BAD_REQUEST
        )
    
    if not collection_name:
       return Response(
           {"error": "Query parameter 'collection_name' is required."},
           status=status.HTTP_400_BAD_REQUEST
       )

    try:
        vector_size = int(os.getenv("VECTOR_SIZE", "1536"))
        qdrant = QdrantConnection()
        qdrant.create_collection(collection_name,vector_size)

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
        # Extracting payload and document from the request data
        ids = request.data.get("id")
        payload = request.data.get("payload")
        document = request.data.get("data")
        collection_name = request.data.get("collection_name")
        print (ids)
        # Attempt to transform non-UUID ids into UUIDs
        try:
            # Check if ids is already a valid UUID
            generated_uuid = uuid.UUID(ids)
            # Re-validate the generated UUID string to ensure it's in a proper format
            ids = str(generated_uuid)
        except ValueError:
            # If not, generate a UUID based on the id string
            ids = str(uuid.uuid5(uuid.NAMESPACE_DNS, ids))
        except TypeError:
            # If ids is None, generate a new UUID
            ids = str(uuid.uuid4())
        print (ids)

        if not collection_name:
            return Response(
                {"error": "Query parameter 'collection_name' is required."},
                status=status.HTTP_400_BAD_REQUEST
            )

        if payload is None or document is None:
            return Response(
                {"error": "Payload and document must not be None."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # qdrant.insert_vector(collection_name, document, [payload], ids)
        qdrant.insert_vector(collection_name, document, [payload])

        message = f"Inserted into collection {collection_name} and payload: {json.dumps(payload, indent=2)}"
        return Response({"message": message}, status=status.HTTP_201_CREATED)

    except Exception as e:
        logger.error(f"Exception during data insertion: {str(e)}")
        return Response(
            {"error": f"Failed to insert data due to an internal error. {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def update_data(request):
    """
    Update data by deleting the existing point based on the provided id and category, and recreate it with new data.
    """
    try:
        id = request.data.get("id")
        id_key= request.data.get("id_key")
        # TODO: Implement category based deletion as second choice.
        #category = request.data.get("category")
        collection_name = request.data.get("collection_name")

        if not id or not collection_name:
            return Response(
                {"error": "id, and collection_name are required fields."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Initialize Qdrant connection
        qdrant = QdrantConnection()
        qdrant.update_vector(collection_name, id, id_key)
        embed_data_into_vector_database(request)
        
        
        return Response(
            {"message": "Data points deleted successfully."},
            status=status.HTTP_200_OK,
        )
    except Exception as e:
        return Response(
            {"error": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(["GET"])
def search_in_vector_database(request):
    q = request.query_params.get("q")
    collection_name = request.query_params.get("collection_name")
    if not q:
        return Response(
            {"error": "Query parameter 'q' is required."},
            status=status.HTTP_400_BAD_REQUEST
        )

    if not collection_name:
       return Response(
           {"error": "Query parameter 'collection_name' is required."},
           status=status.HTTP_400_BAD_REQUEST
       )

    try:
        searcher = NeuralSearcher(collection_name=collection_name)
        search_results = searcher.search(text=q)
        return Response(search_results, status=status.HTTP_200_OK)
    except Exception as e:
        return Response(
            {"error": f"Failed to perform search due to an internal error. {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
