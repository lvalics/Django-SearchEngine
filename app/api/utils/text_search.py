"""
This module provides text search functionality using the Qdrant server.
"""

import re
import time
import logging
from typing import List
from qdrant_client.models import Filter, FieldCondition, MatchText
from .qdrant_connection import QdrantConnection
from app.settings import TEXT_FIELD_NAME

logger = logging.getLogger(__name__)


class TextSearcher:

    def __init__(self, collection_name: str):
        self.collection_name = collection_name
        self.highlight_field = TEXT_FIELD_NAME
        qdrant_connection = QdrantConnection()
        qdrant_connection.initialize_client()
        self.client = qdrant_connection.client

    def highlight(self, record, text) -> dict:
        text = record[self.highlight_field]

        for word in text.lower().split():
            if len(word) > 4:
                pattern = re.compile(
                    rf"(\b{re.escape(word)}?.?\b)", flags=re.IGNORECASE
                )
            else:
                pattern = re.compile(rf"(\b{re.escape(word)}\b)", flags=re.IGNORECASE)
            text = re.sub(pattern, r"<b>\1</b>", text)

        record[self.highlight_field] = text
        return record

    def search(self, text: str, search_limit: int = 10) -> List[dict]:
        start_time = time.time()
        query_response = self.client.scroll(
            collection_name=self.collection_name,
            scroll_filter=Filter(
                must=[
                    FieldCondition(
                        key=TEXT_FIELD_NAME,
                        match=MatchText(text=text),
                    )
                ]
            ),
            with_payload=True,
            with_vectors=False,
            limit=int(search_limit),
        )
        hits = [
            {k: v for k, v in hit.payload.items() if k != "document"}
            for hit in query_response[0]
        ]
        if not hits:
            logger.info("No hits found for query: %s", text)
        return hits, start_time
