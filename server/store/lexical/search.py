import json
from pathlib import Path
from pinecone import Pinecone
from pinecone_text.sparse import BM25Encoder
from .utils import arabic_tokenizer, preprocess_arabic


class LexicalSearch:

    class _ArabicBM25Encoder(BM25Encoder):

        def __init__(self, *args, **kwargs):
            super().__init__(
                lower_case=False,
                remove_punctuation=False,
                remove_stopwords=False,
                stem=False,
                language="arabic",
                *args,
                **kwargs,
            )
            self._tokenizer = arabic_tokenizer

        @classmethod
        def load(cls, path: str):
            with open(path, "r") as f:
                params = json.load(f)
            encoder = cls()
            encoder.avgdl = params["avgdl"]
            encoder.n_docs = params["n_docs"]
            doc_freq = dict(
                zip(params["doc_freq"]["indices"], params["doc_freq"]["values"])
            )
            encoder.doc_freq = doc_freq
            encoder.b = params["b"]
            encoder.k1 = params["k1"]
            return encoder

    def __init__(self, api_key: str, host: str, model_path: str):
        pc = Pinecone(api_key=api_key)
        self.index = pc.Index(host=host)

        BASE_DIR = Path(__file__).resolve().parent.parent.parent
        model_path = (BASE_DIR / "models" / model_path).resolve()

        self.prob_model = self._ArabicBM25Encoder.load(model_path)

    def search(self, query: str, top_k: int, namespace: str) -> list[dict]:
        processed_query = preprocess_arabic(query)
        sparse_qv = self.prob_model.encode_queries(processed_query)

        result = self.index.query(
            sparse_vector=sparse_qv,
            top_k=top_k,
            include_metadata=True,
            namespace=namespace,
        )

        matches = [
            {
                "id": match["id"],
                "score": match["score"],
                "text": match["metadata"]["text"],
            }
            for match in result["matches"]
        ]
        return matches
