"""
This function establishes a connection to the Qdrant server. 
and do all the jobs with Qdrant Vector Search Engine.

Raises:
    ConnectionError: If the connection to the Qdrant server cannot be established.

Returns:
    Connection: A connection object to the Qdrant server.
"""
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


    # def insert_vector(self, collection_name, documents, payload, ids):
    def insert_vector(self, collection_name, documents, payload):
        # print(f"Inserting into collection {collection_name} with documents: {documents} and payload: {payload}")
        self.client.add(
            collection_name=collection_name,
            documents=documents,
            metadata=payload,
            parallel=1,
            # ids=ids
        )
        print(f"Inserted {len(documents)} vectors into collection {collection_name}")
        
        
    def update_vector(self, collection_name, id, id_key):
        
        records, point_ids = self.client.scroll(
        collection_name=collection_name,
        scroll_filter=models.Filter(
            must=[
                models.FieldCondition(key=id_key, match=models.MatchValue(value=id)),
            ]
        ),
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
            print(f"Deleted points with IDs {point_ids} from collection '{collection_name}'.")
        else:
            print(f"No points found for the source '{id}'")
        
      
class NeuralSearcher:

    def __init__(self, collection_name: str, url="localhost", port=6333):
        self.collection_name = collection_name
        self.client = QdrantClient(
            url=url,
            port=port,
            prefer_grpc=True, 
        )
        self.client.set_model(EMBEDDINGS_MODEL) 


    def search(self, text: str, filter_: dict = None) -> List[dict]:
        start_time = time.time()
        hits = self.client.query(
            collection_name=self.collection_name,
            query_text=text,
            query_filter=Filter(**filter_) if filter_ else None,
            limit=5
        )
        print(f"Search completed in {time.time() - start_time} seconds. Hits found: {len(hits)}")
        return [hit.metadata for hit in hits]
