import os
import logging
from qdrant_client import QdrantClient, models
from qdrant_client.models import VectorParams, Distance
from app.settings import EMBEDDINGS_MODEL, TEXT_FIELD_NAME

vector_size = int(os.getenv("VECTOR_SIZE", "1536"))

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

    def set_model(self, model_name):
        # This is a placeholder for setting the model.
        # Depending on the use case, this method might need to actually load a model or perform other setup tasks.
        self.model = model_name
        logger.info(f"Model {model_name} set successfully.")

    def create_collection(self, collection_name, vector_size):
        try:
            self.client.recreate_collection(
                collection_name=collection_name,
                vectors_config=self.client.get_fastembed_vector_params(on_disk=True),
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
            logger.info(f"Collection {collection_name} created successfully.")
        except Exception as e:
            logger.error(f"Failed to create collection {collection_name}: {e}")
            raise e

    # def collection_exists(self, collection_name):
    #     try:
    #         return (
    #             self.client.http.collections_api.get_collection(
    #                 collection_name=collection_name
    #             )
    #             is not None
    #         )
    #     except Exception:
    #         return False

    def insert_vector(self, collection_name, documents, payload):
        self.client.add(
            collection_name=collection_name,
            documents=documents,
            metadata=payload,
            # ids=tqdm(range(len(payload))),
            parallel=0,
        )

    # def insert_vector_fastembed(self, collection_name):
    #     self.client.recreate_collection(
    #         collection_name=collection_name,
    #         vectors_config=self.client.get_fastembed_vector_params(),
    #     )

    # def search_vector(self, collection_name, vectors, top=10):
    #     search_params = models.SearchRequest(
    #         collection_name=collection_name,
    #         query_vector=vectors,
    #         top=top,
    #         params=models.SearchParams(k=top),
    #     )
    #     result = self.client.http.points_api.search_points(search_params)
    #     return result.result
