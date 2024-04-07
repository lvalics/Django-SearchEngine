from sentence_transformers import SentenceTransformer
import numpy as np
import json
import pandas as pd
from tqdm import tqdm
from api.utils.qdrant_connection import QdrantConnection
from qdrant_client import QdrantClient, models
from qdrant_client.models import VectorParams, Distance
import os

if __name__ == "__main__":
    DATA_DIR = "../../"
    qdrant = QdrantClient("http://localhost:6333")

    qdrant.set_model("sentence-transformers/all-MiniLM-L6-v2")
    collection_name = (
        "startups"  # You might want to dynamically set this based on your requirements
    )
    qdrant.recreate_collection(
        collection_name=collection_name,
        vectors_config=qdrant.get_fastembed_vector_params(),
    )

    payload_path = os.path.join(DATA_DIR, "startups_demo_large.json")
    metadata = []
    documents = []

    with open(payload_path) as fd:
        for line in fd:
            obj = json.loads(line)
            documents.append(obj.pop("description"))
            metadata.append(obj)

    qdrant.add(
        collection_name=collection_name,
        documents=documents,
        metadata=metadata,
        parallel=1,  # Use all available CPU cores to encode data
        ids=tqdm(range(len(documents))),
    )
