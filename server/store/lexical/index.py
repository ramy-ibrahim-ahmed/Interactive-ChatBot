import json
import structlog
from pinecone import Pinecone
from pinecone_text.sparse import BM25Encoder
from .utils import arabic_tokenizer, preprocess_arabic

LOGGER = structlog.get_logger(__name__)


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
        processed_docs = [preprocess_arabic(doc) for doc in corpus]
        self.bm25.fit(processed_docs)
        self._save_model_params(model_save_path)
        LOGGER.info(f"Trained bm25 and saved in {model_save_path}")

        vectors_to_upsert = []
        for i, doc in enumerate(processed_docs):
            sparse_vector = self.bm25.encode_documents(doc)
            vectors_to_upsert.append(
                {
                    "id": str(i),
                    "sparse_values": sparse_vector,
                    "metadata": {"text": corpus[i]},
                }
            )

        for i in range(0, len(vectors_to_upsert), 100):
            self.index.upsert(
                vectors=vectors_to_upsert[i : i + 100], namespace=namespace
            )
