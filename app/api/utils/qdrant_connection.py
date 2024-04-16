"""
This function establishes a connection to the Qdrant server.
and do all the jobs with Qdrant Vector Search Engine.

Raises:
    ConnectionError: If the connection to the Qdrant server cannot be established.

Returns:
    Connection: A connection object to the Qdrant server.
"""

import os
import logging
import json
from qdrant_client import QdrantClient, models
from qdrant_client.models import Filter, FieldCondition, Range, MatchValue
from app.settings import EMBEDDINGS_MODEL, TEXT_FIELD_NAME

logger = logging.getLogger(__name__)


class QdrantConnection:
    """
    This function establishes a connection to the Qdrant server.
    It uses the provided server address and port number to establish a connection
    and returns a connection object that can be used for further interactions with the server.

    Raises:
        ConnectionError: If the connection to the Qdrant server cannot be established.
        This could be due to a number of reasons such as the server being down,
        incorrect address or port, or network issues.

    Returns:
        Connection: A connection object to the Qdrant server. This object can be
        used to perform further operations on the server such as creating
        collections, inserting points, and running queries.
    """

    def __init__(self):
        self.initialize_client()

    def initialize_client(self):
        self.client = QdrantClient(
            url=os.environ.get("QDRANT_URL"),
            port=os.environ.get("QDRANT_PORT"),
            prefer_grpc=True,  # Use gRPC for better performance
            # api_key=os.environ.get("QDRANT_API_KEY"),
        )
        embedding_model_name = EMBEDDINGS_MODEL
        if not self.client._FASTEMBED_INSTALLED:
            return "FastEmbed is not installed. Install fastembed to use this feature."
        if not hasattr(self.client, "model_set") or not self.client.model_set:
            self.client.set_model(embedding_model_name=embedding_model_name)
            self.client.model_set = True
            # Check if the model is initialized & cls.embeddings_models is set with expected values
            dim, _ = self.client._get_model_params(embedding_model_name)
            assert dim == 384

    def create_collection(self, collection_name: str, vector_size):
        """
        This function creates a new collection in the Qdrant server.

        Args:
            collection_name (str): The name of the collection to be created.
            This name should be unique across the server.
            vector_size (int): The size of the vectors that will be stored in the
            collection. All vectors in a collection must be of the same size.

        Raises:
            CollectionCreationError: If there is an issue creating the collection.
            This could be due to a collection with the same name already existing,
            server issues, or invalid parameters.
        """
        vector_size = int(vector_size)
        try:
            self.client.create_collection(
                collection_name=collection_name,
                vectors_config=self.client.get_fastembed_vector_params(on_disk=True),
                quantization_config=models.ScalarQuantization(
                    scalar=models.ScalarQuantizationConfig(
                        type=models.ScalarType.INT8, quantile=0.99, always_ram=True
                    )
                ),
            )
            self.client.create_payload_index(
                collection_name=collection_name,
                field_name=TEXT_FIELD_NAME,
                field_schema=models.TextIndexParams(
                    type=models.TextIndexType.TEXT,
                    tokenizer=models.TokenizerType.WORD,
                    min_token_len=2,
                    max_token_len=20,
                    lowercase=True,
                ),
            )
            logger.info("Collection %s created successfully.", collection_name)
        except Exception as error:
            error_message = str(error)
            formatted_error = (
                "Collection already exists."
                if "already exists" in error_message
                else "Failed to create collection due to server error."
            )
            logger.error(
                "Failed to create collection %s: %s", collection_name, formatted_error
            )
            return formatted_error  # Return the error message instead of raising an exception

    def insert_vector(self, collection_name, document: dict, payload: dict):
        """
        This function inserts documents into a specified collection in the Qdrant server.

        Args:
            collection_name (str): The name of the collection into which the
            documents need to be inserted.
            documents (List[dict]): A list of dictionaries where each dictionary
            represents a document to be inserted. Each dictionary must contain an
            'id' key and a 'vector' key.
            payload (dict, optional): A dictionary containing additional data to
            be associated with each document. This could include metadata like
            'title', 'description', etc. Defaults to None.

        Raises:
            InsertionError: If there is an issue inserting the documents into the
            collection. This could be due to issues with the collection, server
            issues, or invalid documents.

        Returns:
            bool: True if the insertion was successful, False otherwise.
        """
        try:
            document_str = json.dumps(
                document
            )  # Convert document dict to a JSON string
            self.client.add(
                collection_name=collection_name,
                documents=[document_str],
                metadata=payload,
                parallel=0,
            )
            return True
        except Exception as error:
            logger.error(
                "Failed to insert vector into collection %s: %s",
                collection_name,
                str(error),
            )
            return False

    def update_vector(self, collection_name: str, filter_conditions: dict):
        """
        This function deletes a specific record from a collection in the Qdrant server.

        Args:
            collection_name (str): The name of the collection from which the record
            needs to be deleted.
            filter_conditions (dict): A dictionary representing the conditions to filter
            the vectors that need to be updated or deleted.

        Raises:
            DeletionError: If there is an issue deleting the record from the collection.
            This could be due to the record not existing, issues with the collection,
            or server issues.

        Returns:
            bool: True if the deletion was successful, False otherwise.
        """

        must_conditions = [
            models.FieldCondition(key=key, match=models.MatchValue(value=value))
            for key, value in filter_conditions.items()
        ]
        scroll_filter = models.Filter(must=must_conditions)

        try:
            scroll_response = self.client.scroll(
                collection_name=collection_name,
                scroll_filter=scroll_filter,
                limit=100,
                offset=0,
                with_payload=True,
            )

            logger.debug(f"scroll_response: {scroll_response}")

            if not scroll_response[0]:  # Check if the scroll_response list is empty
                logger.info("No records found matching the conditions.")
                return False

            point_ids = [record.id for record in scroll_response[0]]
            if point_ids:
                self.client.delete(
                    collection_name=collection_name,
                    points_selector=models.PointIdsList(points=point_ids),
                )
                deleted_ids = [str(point_id) for point_id in point_ids]
                logger.info(f"Successfully deleted records with IDs: {deleted_ids}")
                return deleted_ids
            else:
                logger.info("No records found matching the conditions.")
                return False

        except Exception as e:
            logger.error(f"Error updating data in vector database: {str(e)}")
            raise Exception(
                f"Error deleting records from collection {collection_name}: {str(e)}"
            )
