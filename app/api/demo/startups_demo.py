from sentence_transformers import SentenceTransformer
import numpy as np
import json
import pandas as pd
from tqdm import tqdm
from api.utils.qdrant_connection import QdrantConnection
import os

if __name__ == '__main__':
    model = SentenceTransformer(
        "all-MiniLM-L6-v2", device="cuda"
    )  # or device="cpu" if you don't have a GPU

    df = pd.read_json("../startups_demo.json", lines=True)

    vectors = model.encode(
        [row.alt + ". " + row.description for row in df.itertuples()],
        show_progress_bar=True,
    )

    vectors.shape
    np.save("../startup_vectors.npy", vectors, allow_pickle=False)

    fd = open("../startups_demo.json")

    # payload is now an iterator over startup data
    payload = map(json.loads, fd)

    # Load all vectors into memory, numpy array works as iterable for itself.
    # Other option would be to use Mmap, if you don't want to load all data into RAM
    vectors = np.load("../startup_vectors.npy")

    qdrant = QdrantConnection()
    collection_name = "1_SearchEngineGP"  # You might want to dynamically set this based on your requirements
    qdrant.insert_vector(collection_name, vectors, payload)
