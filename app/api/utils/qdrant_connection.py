import os
import logging
import time
from typing import List
from qdrant_client import QdrantClient, models
from qdrant_client.models import VectorParams, Distance
from qdrant_client.http.models.models import Filter
from app.settings import EMBEDDINGS_MODEL, TEXT_FIELD_NAME

logger = logging.getLogger(__name__)

class QdrantConnection:
    def __init__(self, url="localhost", port=6333):
        self.client = QdrantClient(
            url=url,
            port=port,
            prefer_grpc=True, # Use gRPC for better performance
            # api_key=os.environ.get("QDRANT_API_KEY"),
        )
        self.model = None
        self.client.set_model(EMBEDDINGS_MODEL)

    def create_collection(self, collection_name: str, vector_size):
        
        try:
            self.client.recreate_collection(
                collection_name=collection_name,
                vectors_config=self.client.get_fastembed_vector_params(on_disk=True),
                # Quantization is optional, but it can significantly reduce the memory usage
                quantization_config=models.ScalarQuantization(
                    scalar=models.ScalarQuantizationConfig(
                        type=models.ScalarType.INT8,
                        quantile=0.99,
                        always_ram=True
                    )
                )
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
            logger.info(f"Collection {collection_name} created successfully.")
        except Exception as e:
            logger.error(f"Failed to create collection {collection_name}: {e}")
            raise e


    def insert_vector(self, collection_name, documents, payload):
        # print(f"Inserting into collection {collection_name} with documents: {documents} and payload: {payload}")
        self.client.add(
            collection_name=collection_name,
            documents=documents,
            metadata=payload,
            parallel=1,
        )
        logger.info("Data successfully inserted.")
      
class NeuralSearcher:

    def __init__(self, collection_name: str, url="localhost", port=6333):
        self.collection_name = collection_name
        self.client = QdrantClient(
            url=url,
            port=port,
            prefer_grpc=True, 
        )
        self.client.set_model(EMBEDDINGS_MODEL) 

    def search(self, text: str, filter_: dict = None) -> dict:
        start_time = time.time()
        hits = self.client.query(
            collection_name=self.collection_name,
            query_text=text,
            query_filter=Filter(**filter_) if filter_ else None,
            limit=5
        )
        search_time = time.time() - start_time
        return {
            "results": [hit.metadata for hit in hits],
            "search_time": search_time,
            "hits_found": len(hits)
        }
