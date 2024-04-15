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
from typing import List
from qdrant_client import QdrantClient, models
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

        if not hasattr(self.client, "model_set") or not self.client.model_set:
            self.client.set_model(EMBEDDINGS_MODEL)
            self.client.model_set = True

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
                # vectors_config=models.VectorParams(
                #     size=vector_size,
                #     distance=models.Distance.Metric.COSINE,
                #     on_disk=True,
                # ),
                # Quantization is optional, but it can significantly reduce the memory usage
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
            if "already exists" in error_message:
                return {
                    "error": f"Collection {collection_name} already exists. Proceeding without creating a new one."
                }
        else:
            logger.info("Collection %s created successfully.", collection_name)
            return {"message": f"Collection {collection_name} created successfully."}

    # def insert_vector(self, collection_name, document, payload, ids):
    def insert_vector(self, collection_name, document, payload):
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
        self.client.add(
            collection_name=collection_name,
            documents=[
                f"{document}",
            ],
            metadata=payload,
            # ids="bf4d7b0e-b34d-2fd8-d292-6049c4f7efc7",
            parallel=0,
        )
        logger.info(
            "Inserted %d vectors into collection %s", len(document), collection_name
        )
        return True

    def update_vector(self, collection_name, id_value, id_key, id_value2, id_key2):
        """
        This function deletes a specific record from a collection in the Qdrant server.

        Args:
            collection_name (str): The name of the collection from which the record
            needs to be deleted.
            id (int): The unique identifier of the record that needs to be deleted.
            id_key (str): The key used for the unique identifier in the collection.
            id_value2 (str, optional): The second unique identifier of the
            record that needs to be matched.
            id_key2 (str, optional): The key used for the second unique identifier
            in the collection.

        Raises:
            DeletionError: If there is an issue deleting the record from the collection.
            This could be due to the record not existing, issues with the collection,
            or server issues.

        Returns:
            bool: True if the deletion was successful, False otherwise.
        """

        filter_conditions = [
            models.FieldCondition(key=id_key, match=models.MatchValue(value=id_value)),
        ]
        if id_key2 and id_value2:
            filter_conditions.append(
                models.FieldCondition(
                    key=id_key2, match=models.MatchValue(value=id_value2)
                )
            )

        records, point_ids = self.client.scroll(
            collection_name=collection_name,
            scroll_filter=models.Filter(must=filter_conditions),
            limit=int(100),
            offset=int(0),
            with_payload=True,
            with_vectors=False,
        )

        if records:
            point_ids = [record.id for record in records]
            self.client.delete(
                collection_name=collection_name,
                points_selector=models.PointIdsList(
                    points=point_ids,
                ),
            )
            deleted_ids = [str(point_id) for point_id in point_ids]
            return deleted_ids