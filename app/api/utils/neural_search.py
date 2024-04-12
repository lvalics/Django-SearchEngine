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
        query_filter = (
            Filter(
                must=[
                    FieldCondition(
                        key=TEXT_FIELD_NAME,
                        match=MatchText(text=text),
                    )
                ]
            )
            if filter_ is None
            else Filter(**filter_)
        )

        logger.info(f"query_filter {query_filter} for {text}.")
        start_time = time.time()
        query_response = self.client.query(
            collection_name=self.collection_name,
            query_text=text,
            query_filter=query_filter,
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
