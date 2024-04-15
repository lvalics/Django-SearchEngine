"""
This function is responsible for rendering the main view of the application.
It fetches data from the database, processes it, and sends it to the
template for rendering.

Raises:
    DatabaseError: If there is an issue fetching data from the database.

Returns:
    HttpResponse: A HttpResponse object containing the rendered template.
"""

import os.path
import time
import logging
import json
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes, authentication_classes
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.permissions import IsAuthenticated
from django.views.decorators.csrf import csrf_exempt
from api.utils.qdrant_connection import QdrantConnection
from api.utils.neural_search import NeuralSearcher
from api.utils.text_search import TextSearcher
from api.serializers import MessageSerializer
from app.permissions import IsOwner


logger = logging.getLogger(__name__)


class HelloWorldApiView(APIView):
    """
    View to return "Hello World" response.
    """

    authentication_classes = (JWTAuthentication,)
    serializer_class = MessageSerializer
    permission_classes = [IsAuthenticated, IsOwner]

    @staticmethod
    def get(_):
        """DJ-SE"""
        return Response({"message": "DJ-SE"}, status=status.HTTP_200_OK)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def create_qdrant_collection_name(request):
    """
    Create a new collection in Qdrant. Will create IDUser +
    namespace to be sure is unique/user specific.
    {
        "namespace":  "SearchEngineGP"
    }
    """
    user = request.user
    # collection_name = f"{user.id}_{request.data.get('collection_name')}"
    raw_collection_name = request.data.get("collection_name")
    if not raw_collection_name:
        return Response(
            {"error": "collection_name is required"}, status=status.HTTP_400_BAD_REQUEST
        )
    collection_name = f"{user.id}_{raw_collection_name}"

    try:
        vector_size = int(os.getenv("VECTOR_SIZE", "1536"))
        qdrant = QdrantConnection()
        creation_result = qdrant.create_collection(collection_name, vector_size)
        if creation_result is not None:  # If creation_result contains an error message
            return Response(
                {"error": creation_result}, status=status.HTTP_400_BAD_REQUEST
            )

    except (ValueError, ConnectionError, KeyError, TypeError, IndexError) as error:
        return Response({"error": str(error)}, status=status.HTTP_400_BAD_REQUEST)

    return Response(
        {"collection_name": collection_name}, status=status.HTTP_201_CREATED
    )


def process_vector_data(data):
    """
    Process vector data by updating and inserting vectors into the Qdrant database...
    """
    qdrant = QdrantConnection()
    # Assuming filter_conditions is a dictionary like {"companyID": "1772", "type": "primarie"}
    filter_conditions = data.get("filter_conditions", {})
    collection_name = data.get("collection_name")
    document = data.get("document")
    payload = data.get("payload")

    # Convert filter_conditions into a format suitable for Qdrant update_vector method
    if filter_conditions:
        # Update vector if filter_conditions are provided
        data_deleted = qdrant.update_vector(
            collection_name=collection_name, filter_conditions=filter_conditions
        )
    else:
        data_deleted = False

    # Insert vector
    data_inserted = qdrant.insert_vector(collection_name, document, payload)

    return data_deleted, data_inserted


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def embed_data_into_vector_database(request):
    """
    This function handles the HTTP requests to a specific view in the Django application.
    It takes a request object and returns a response object.

    Args:
        request (HttpRequest): The request object that encapsulates all of the HTTP request data.
        This includes data like the method (GET, POST, etc.), headers, user information,
        and any data sent in the body of the request.

    Returns:
        HttpResponse: The response object that encapsulates all of the HTTP response data.
        This includes data like the status code, headers, and any data sent in the body
        of the response.
    """


@api_view(["POST"])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
@csrf_exempt
def embed_data_into_vector_database(request):
    try:
        collection_name = request.data.get("collection_name")
        payload = request.data.get("payload")
        document_data = request.data.get("data")
        # Ensure document is properly formatted as a dictionary
        # Ensure document is properly formatted as a dictionary
        if document_data and isinstance(document_data, str):
            document = json.loads(document_data)
        else:
            document = document_data

        if not collection_name or not payload or document is None:
            return Response(
                {"error": "Missing required fields."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        qdrant = QdrantConnection()
        success = qdrant.insert_vector(
            collection_name=collection_name, document=document, payload=payload
        )

        if success:
            return Response(
                {"success": "Data successfully inserted into vector database."},
                status=status.HTTP_201_CREATED,
            )
        else:
            return Response(
                {"error": "Failed to insert data into vector database."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
    except Exception as error:
        return Response(
            {"error": f"Failed to insert data due to an internal error. {str(error)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def update_data_into_vector_database(request):
    """
    This function handles the HTTP requests to a specific view in the Django application.
    It takes a request object and returns a response object.

    Args:
        request (HttpRequest): The request object that encapsulates all of the
        HTTP request data. This includes data like the method (GET, POST, etc.),
        headers, user information, and any data sent in the body of the request.

    Returns:
        HttpResponse: The response object that encapsulates all of the HTTP
        response data. This includes data like the status code, headers, and
        any data sent in the body of the response.
    """
    try:
        filter_conditions = request.data.get("filter_conditions", {})
        payload = request.data.get("payload")
        document = request.data.get("data")
        collection_name = request.data.get("collection_name")

        if not filter_conditions or not collection_name:
            return Response(
                {"error": "filter_conditions and collection_name are required fields."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        data = {
            "collection_name": collection_name,
            "document": document,
            "payload": payload,
            "filter_conditions": filter_conditions,
        }
        data_deleted, data_inserted = process_vector_data(data)

        response_data = {}
        if data_deleted:
            response_data["DELETED_IDS"] = data_deleted
        if data_inserted:
            response_data["SUCCESS"] = payload
        if response_data:
            return Response(
                response_data,
                status=status.HTTP_200_OK if data_deleted else status.HTTP_201_CREATED,
            )

    except (ValueError, ConnectionError, KeyError, TypeError, IndexError) as error:
        return Response(
            {"error": str(error)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(["GET"])
def search_in_vector_database(request):
    """
    This function handles the HTTP requests to a specific view in the Django application.
    It takes a request object and returns a response object.

    Args:
        request (HttpRequest): The request object that encapsulates all of the HTTP request data.
        This includes data like the method (GET, POST, etc.), headers, user information,
        and any data sent in the body of the request.
        Limit was moved to parameter.

    params:
        q=QUERY (mandatory)
        collection_name=COLLECTION_NAME (mandatory)
        limit=1 (optional, default 10)
        type=neural (or text by default)

    Returns:
        HttpResponse: The response object that encapsulates all of the HTTP response data.
        This includes data like the status code, headers, and any data sent in the body of
        the response.
    """
    collection_name = request.GET.get("collection_name")
    q = request.GET.get("q")
    search_type = request.GET.get("type")
    search_limit = int(request.GET.get("limit", 10))
    if not q:
        return Response(
            {"error": "Query parameter 'q' is required."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    if not collection_name:
        return Response(
            {"error": "Query parameter 'collection_name' is required."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    text_searcher = TextSearcher(collection_name=collection_name)
    neural_searcher = NeuralSearcher(collection_name=collection_name)

    if search_type == "text" or not search_type:
        do_search = text_searcher.search(text=q, search_limit=search_limit)
        logging.info("Text search")
    else:
        do_search = neural_searcher.search(text=q, search_limit=search_limit)
        logging.info("Neural  search")

    try:
        search_results, start_time = do_search
        search_time_seconds = time.time() - start_time
        response_data = {
            "results": search_results,
            "search_time_seconds": round(search_time_seconds, 2),
        }
        return Response(response_data, status=status.HTTP_200_OK)
    except (ValueError, ConnectionError, KeyError, TypeError, IndexError) as error:
        logger.exception("Unhandled exception during search: %s", str(error))
        return Response(
            {
                "error": f"Failed to perform search due to an internal error. {str(error)}"
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
