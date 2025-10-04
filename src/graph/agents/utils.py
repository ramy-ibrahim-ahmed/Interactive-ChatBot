import json
import nltk
import pyarabic.araby as araby
from pinecone import Pinecone
from pinecone_text.sparse import BM25Encoder
from nltk.stem.isri import ISRIStemmer
from ...core.config import get_settings

SETTINGS = get_settings()
pc = Pinecone(api_key=SETTINGS.PINECONE_API_KEY, host=SETTINGS.PINECONE_HOST_SPARSE)
index = pc.Index(host=SETTINGS.PINECONE_HOST_SPARSE)


def preprocess_arabic(text):
    text = araby.strip_tashkeel(text)
    text = araby.normalize_alef(text)
    text = araby.normalize_hamza(text)
    text = araby.strip_tatweel(text)
    return text


def arabic_tokenizer(text):
    tokens = araby.tokenize(text)
    stemmer = ISRIStemmer()
    arabic_stopwords = set(nltk.corpus.stopwords.words("arabic"))
    return [stemmer.stem(t) for t in tokens if t not in arabic_stopwords and len(t) > 1]


class ArabicBM25Encoder(BM25Encoder):
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
    def load(cls, path):
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


bm25 = ArabicBM25Encoder.load("bm25_values_v2.json")


def search_keywords(query, top_k):
    processed_query = preprocess_arabic(query)
    sparse_qv = bm25.encode_queries(processed_query)
    result = index.query(
        sparse_vector=sparse_qv,
        top_k=top_k,
        include_metadata=True,
        namespace="customers_v2",  # customers-sparse-v2
    )
    keywords = [match["metadata"] for match in result["matches"]]
    return keywords
