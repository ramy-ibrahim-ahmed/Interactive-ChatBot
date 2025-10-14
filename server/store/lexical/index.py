import json
from pinecone import Pinecone
from pinecone_text.sparse import BM25Encoder
from tqdm import tqdm
from .utils import arabic_tokenizer, preprocess_arabic


class LexicalTrainer:
    def __init__(self, api_key: str, host: str):
        pc = Pinecone(api_key=api_key)
        self.index = pc.Index(host=host)
        self.bm25 = self._create_bm25_encoder()

    def _create_bm25_encoder(self) -> BM25Encoder:
        encoder = BM25Encoder(
            lower_case=False,
            remove_punctuation=False,
            remove_stopwords=False,
            stem=False,
            language="arabic",
        )
        encoder._tokenizer = arabic_tokenizer
        return encoder

    def _save_model_params(self, filepath: str):
        params = {
            "avgdl": self.bm25.avgdl,
            "n_docs": self.bm25.n_docs,
            "doc_freq": {
                "indices": [int(idx) for idx in self.bm25.doc_freq.keys()],
                "values": [float(val) for val in self.bm25.doc_freq.values()],
            },
            "b": self.bm25.b,
            "k1": self.bm25.k1,
        }
        with open(filepath, "w") as f:
            json.dump(params, f)

    def train_and_index(self, corpus: list[str], namespace: str, model_save_path: str):
        processed_docs = [preprocess_arabic(doc) for doc in tqdm(corpus)]
        self.bm25.fit(processed_docs)
        self._save_model_params(model_save_path)

        vectors_to_upsert = []
        for i, doc in enumerate(tqdm(processed_docs, desc="Encoding documents")):
            sparse_vector = self.bm25.encode_documents(doc)
            vectors_to_upsert.append(
                {
                    "id": str(i),
                    "sparse_values": sparse_vector,
                    "metadata": {"text": corpus[i]},
                }
            )

        for i in tqdm(
            range(0, len(vectors_to_upsert), 100), desc="Upserting to Pinecone"
        ):
            self.index.upsert(
                vectors=vectors_to_upsert[i : i + 100], namespace=namespace
            )


# # --- Example Usage ---
# if __name__ == "__main__":
#     # --- Configuration ---
#     PINECONE_API_KEY = "YOUR_PINECONE_API_KEY"
#     PINECONE_HOST = "YOUR_PINECONE_HOST_URL"
#     DATA_FILE = r"output\customers_v3.json"
#     MODEL_FILE = "bm25_model_v3.json"
#     NAMESPACE = "customers_v3"

#     # --- Load Data ---
#     with open(DATA_FILE, "r", encoding="utf-8") as f:
#         data = json.load(f)
#     texts = [chunk for item in data for chunk in item["chunks"]]

#     # --- Run Training and Indexing ---
#     trainer = LexicalSearchTrainer(api_key=PINECONE_API_KEY, host=PINECONE_HOST)
#     trainer.train_and_index(
#         corpus=texts, namespace=NAMESPACE, model_save_path=MODEL_FILE
#     )
