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
from rest_framework.decorators import (
    api_view,
    permission_classes,
)
from rest_framework.permissions import IsAuthenticated
from django.views.decorators.csrf import csrf_exempt
from api.utils.qdrant_connection import QdrantConnection
from api.utils.neural_search import NeuralSearcher
from api.utils.text_search import TextSearcher
from api.serializers import MessageSerializer


logger = logging.getLogger(__name__)


class HelloWorldApiView(APIView):
    """
    View to return "Hello World" response.
    """

    serializer_class = MessageSerializer

    @staticmethod
    def get(_):
        """DJ-SE"""
        return Response({"message": "DJ-SE"}, status=status.HTTP_200_OK)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
@csrf_exempt
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


@api_view(["POST"])
@permission_classes([IsAuthenticated])
@csrf_exempt
def embed_data_into_vector_database(request):
    """
    This endpoint expects a JSON payload with the following structure:
    {
        "collection_name": "COLLECTION_NAME",
        "payload": [{
            "companyID": 1772,
            "name": "NameHere",
            "address": "SomeAddress",
            "url": "something.com",
            "description": "a short description",
            "publicContactPhone": "0257-557555555",
            "category": "store",
            "type": "business"
        }],
        "data":  "Any other document-specific information which will be searchable"
    }

    Where:
    - "collection_name" is the name of the Qdrant collection to insert the vector into.
    - "payload" is a dictionary containing any additional data to be associated with the vector.
    - "data" is the actual document data including the vector and its ID.
    """
    try:
        collection_name = request.data.get("collection_name")
        payload = request.data.get("payload")
        if not isinstance(payload, list):
            payload = [payload]
        document_data = request.data.get("data")

        qdrant = QdrantConnection()
        qdrant.insert_vector(collection_name, document_data, payload)
        response_data = {"SUCCESS": payload}
        return Response(response_data, status=status.HTTP_201_CREATED)

    except Exception as error:
        logger.exception("Unhandled exception during data insertion: %s", str(error))
        return Response(
            {"error": f"Failed to insert data due to an internal error. {str(error)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(["POST"])
@permission_classes([IsAuthenticated])
@csrf_exempt
def update_data_into_vector_database(request):
    """
    This function handles the HTTP requests to a specific view in the Django application.
    It takes a request object and returns a response object.

    This endpoint expects a JSON payload with the following structure:
    {
        "filter_conditions": {
            "companyID": "1772",
            "type": "business"
        },
        "collection_name": "COLLECTION_NAME",
        "payload": [{
            "companyID": 1772,
            "name": "NameHere",
            "address": "SomeAddress",
            "url": "something.com",
            "description": "a short description",
            "publicContactPhone": "0257-557555555",
            "category": "store",
            "type": "business"
        }],
        "data":  "Any other document-specific information which will be searchable"
    }

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
        collection_name = request.data.get("collection_name")
        payload = request.data.get("payload")
        if not isinstance(payload, list):
            payload = [payload]
        document_data = request.data.get("data")

        if not filter_conditions or not collection_name:
            return Response(
                {"error": "filter_conditions and collection_name are required fields."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        qdrant = QdrantConnection()
        data_deleted = qdrant.update_vector(
            collection_name=collection_name, filter_conditions=filter_conditions
        )
        if data_deleted:
            data_inserted = qdrant.insert_vector(
                collection_name, document_data, payload
            )
            if data_inserted:
                response_data = {
                    "DELETED_IDS": data_deleted,
                    "SUCCESS": payload,
                }
            else:
                response_data = {
                    "DELETED_IDS": data_deleted,
                    "ERROR": "Failed to insert data",
                }
            return Response(response_data, status=status.HTTP_200_OK)
        else:
            return Response(
                {"error": f"No records found for: {filter_conditions}"},
                status=status.HTTP_404_NOT_FOUND,
            )
    except Exception as error:
        logger.error(f"Error updating data in vector database: {str(error)}")
        return Response(
            {"error": "Internal server error."},
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
        logging.info("Neural search")

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
