"""
This module provides neural search functionality using the Qdrant server.
"""

import logging
import time
from typing import List
from qdrant_client import models
from .qdrant_connection import QdrantConnection
from qdrant_client.models import Filter, FieldCondition, MatchText
from app.settings import TEXT_FIELD_NAME

logger = logging.getLogger(__name__)


class NeuralSearcher:
    def __init__(self, collection_name: str):
        self.collection_name = collection_name
        qdrant_connection = QdrantConnection()
        qdrant_connection.initialize_client()
        self.client = qdrant_connection.client

    def search(
        self, text: str, filter_: dict = None, search_limit: int = 10
    ) -> List[dict]:
        if filter_ is None:
            query_filter = models.Filter(
                must=[
                    models.FieldCondition(
                        key=TEXT_FIELD_NAME,
                        condition=models.Condition(match=models.MatchValue(value=text)),
                    )
                ]
            )
        else:
            query_filter = models.Filter(**filter_)

        logger.info(f"query_filter {query_filter} for {text}.")
        start_time = time.time()
        # query_response = self.client.search(
        #     collection_name=self.collection_name,
        #     query_filter=query_filter,
        #     limit=self.search_limit,
        #     query_vector=query_vector.tolist(),
        # )
        query_response = self.client.query(
            collection_name=self.collection_name,
            query_text=text,
            query_filter=Filter(**filter_) if filter_ else None,
            limit=search_limit,
        )
        if query_response is None:
            logger.info(
                "Query response is None for query: %s with filter: %s", text, filter_
            )
            return [], start_time
        else:
            hits = [
                {k: v for k, v in hit.metadata.items() if k != "document"}
                for hit in query_response
            ]
            if not hits:
                logger.info(
                    "No hits found for query: %s with filter: %s", text, filter_
                )
            return hits, start_time
