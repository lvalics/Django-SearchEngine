from qdrant_client import QdrantClient
from qdrant_client.models import Filter

collection_name = "startups"


class NeuralSearcher:
    def __init__(self, collection_name):
        self.collection_name = collection_name
        # initialize Qdrant client
        self.qdrant_client = QdrantClient("http://localhost:6333")
        self.qdrant_client.set_model("sentence-transformers/all-MiniLM-L6-v2")


def search(self, text: str):

    city_of_interest = "Chicago"
    city_filter = Filter(
        **{
            "must": [
                {
                    "key": "city",
                    "match": {"value": city_of_interest},
                }
            ]
        }
    )

    search_result = self.qdrant_client.query(
        collection_name=self.collection_name,
        query_text=text,
        # query_filter=None,  # If you don't want any filters for now
        query_filter=city_filter,
        limit=5,  # 5 the closest results are enough
    )
    # `search_result` contains found vector ids with similarity scores along with the stored payload
    # In this function you are interested in payload only
    metadata = [hit.metadata for hit in search_result]
    print(f"Result: {metadata}")
    return metadata
