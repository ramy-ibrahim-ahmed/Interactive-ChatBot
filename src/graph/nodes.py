from .state import State
from ..core.enums.chat_roles import OpenAIRolesEnum
from ..core.schemas.guide import SearchResult, ManySearchResults, SearchQueries
from ..store.nlp import NLPInterface, PromptFactory
from ..store.vectordb import VectorDBInterface
import json
from pinecone import Pinecone
import pyarabic.araby as araby
from pinecone_text.sparse import BM25Encoder
from nltk.stem.isri import ISRIStemmer
import nltk

nltk.download("stopwords")

PINECONE_API_KEY = (
    "pcsk_5Ho56W_T3c3KLAQZBEVoqBueWma8j2C7MjfWrgzUrT3mHmGgxKAihEX4kGgtbp9RErcqot"
)
PINECONE_HOST = "https://onyx-sparse-bxkmeye.svc.aped-4627-b74a.pinecone.io"
pc = Pinecone(api_key=PINECONE_API_KEY, host=PINECONE_HOST)
index = pc.Index(host=PINECONE_HOST)


def preprocess_arabic(text):
    """Normalizes and cleans Arabic text."""
    text = araby.strip_tashkeel(text)
    text = araby.normalize_alef(text)
    text = araby.normalize_hamza(text)
    text = araby.strip_tatweel(text)
    return text


def arabic_tokenizer(text):
    """
    Tokenizes, stems, and removes stopwords from Arabic text.
    Uses ISRIStemmer for stemming.
    """
    tokens = araby.tokenize(text)
    stemmer = ISRIStemmer()
    arabic_stopwords = set(nltk.corpus.stopwords.words("arabic"))
    return [stemmer.stem(t) for t in tokens if t not in arabic_stopwords and len(t) > 1]


# # --- Load the BM25 Encoder ---

# print("Loading BM25 model from file...")
# # **FIX:** The error indicates 'bm25_values.json' might be malformed or from an
# # older version. This code robustly loads it by manually checking for and
# # adding missing required parameters before initializing the encoder.
# try:
#     with open("bm25_values_v2.json", "r", encoding="utf-8") as f:
#         params = json.load(f)

#     # Ensure required keys exist to prevent TypeError.
#     # This is a workaround for a malformed model file.
#     params.setdefault("remove_punctuation", False)
#     params.setdefault("remove_stopwords", False)
#     params.setdefault("stem", False)

#     # Manually create the encoder and set its parameters
#     bm25 = BM25Encoder()
#     bm25.set_params(**params)

#     # After loading, you MUST re-assign the custom tokenizer function.
#     # The JSON file saves the *parameters* but cannot save the function object itself.
#     bm25._tokenizer = arabic_tokenizer
#     print("BM25 model loaded successfully.")
# except FileNotFoundError:
#     print(
#         "Error: 'bm25_values.json' not found. Please run 'create_bm25_model.py' first."
#     )
#     exit()
# except Exception as e:
#     print(f"An error occurred while loading the BM25 model: {e}")
#     exit()


class ArabicBM25Encoder(BM25Encoder):
    def __init__(self, *args, **kwargs):
        # Initialize parent with your original params (tokenizer will be overridden)
        super().__init__(
            lower_case=False,
            remove_punctuation=False,
            remove_stopwords=False,
            stem=False,
            language="arabic",
            *args,
            **kwargs,
        )
        # Override with custom tokenizer
        self._tokenizer = arabic_tokenizer

    @classmethod
    def load(cls, path):
        with open(path, "r") as f:
            params = json.load(f)

        # Create instance with custom tokenizer
        encoder = cls()

        # Restore fitted params (these are public/protected attributes)
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
        namespace="customers-sparse-v2",
    )
    keywords = list()
    for match in result["matches"]:
        keywords.append(
            {"topic_id": "dummy_keyword", "text": match["metadata"]["text"]}
        )

    return keywords


def intent_node(state: State, nlp_openai: NLPInterface):
    user_message = state.get("user_message")
    intent_prompt = PromptFactory().get_prompt("user_intent")

    messages = [
        {"role": OpenAIRolesEnum.SYSTEM.value, "content": intent_prompt},
        {"role": OpenAIRolesEnum.USER.value, "content": user_message},
    ]
    intent = nlp_openai.chat(messages, "gpt-4.1", temperature=0.0, top_p=1.0)
    return {"intent": intent}


def query_node(state: State, nlp_openai: NLPInterface) -> State:
    prompt_query = PromptFactory().get_prompt("query_write")
    user_message = state.get("user_message")

    messages = [
        {"role": OpenAIRolesEnum.SYSTEM.value, "content": prompt_query},
        {"role": OpenAIRolesEnum.USER.value, "content": user_message},
    ]

    enhanced_query = nlp_openai.structured_chat(SearchQueries, "gpt-4.1", messages)
    return {"enhanced_query": enhanced_query}


def system_node(state: State, nlp_openai: NLPInterface) -> State:
    return {"system_name": "customers_v1"}


def search_node(
    state: State,
    nlp_openai: NLPInterface,
    nlp_cohere: NLPInterface,
    vectordb: VectorDBInterface,
) -> State:
    enhanced_query = state.get("enhanced_query")
    system_name = state.get("system_name")
    embeddings = nlp_cohere.embed(enhanced_query.semantic_queries)

    nearest = vectordb.query_chunks(embeddings, system_name, max_retrieved=10)
    nearest_unique = [dict(t) for t in {tuple(sorted(d.items())) for d in nearest}]
    keywords = search_keywords(enhanced_query.lexical_search_query, 10)

    for_rerank = list()
    for keyword in keywords:
        for_rerank.append(keyword)
    for n in nearest_unique:
        for_rerank.append(n)
    reranked_nearest = nlp_cohere.rerank(
        enhanced_query.reranker_query, for_rerank, "rerank-v3.5", 5
    )

    search_results = ManySearchResults(
        results=[
            SearchResult(
                score=float(item["score"]),
                topic=str(item["topic"]),
                text=item["text"],
            )
            for item in reranked_nearest
        ]
    )
    return {"search_results": search_results}


def formate_node(state: State) -> State:
    search_results: ManySearchResults = state.get("search_results", "")

    search_as_list = list()
    for result in search_results.results:
        search_as_list.append(result.text)

    search_as_text = "\n\n\n---\n\n\n".join(search_as_list)
    with open("output.txt", "w", encoding="utf-8") as f:
        f.write(search_as_text)
    return {"formated_search": search_as_text}


def analysis_node(state: State, nlp_openai: NLPInterface):
    user_message = state.get("user_message")
    formated_search: ManySearchResults = state.get("formated_search", "")
    analysis_prompt = PromptFactory().get_prompt("analysis")

    messages = [
        {"role": OpenAIRolesEnum.SYSTEM.value, "content": analysis_prompt},
        {"role": OpenAIRolesEnum.USER.value, "content": user_message},
        {"role": OpenAIRolesEnum.ASSISTANT.value, "content": formated_search},
    ]

    analysis = nlp_openai.chat(messages, "gpt-4.1", temperature=0.0, top_p=1.0)
    return {"analysis": analysis}


def chat_node(state: State, nlp_openai: NLPInterface) -> State:
    prompt_chat = PromptFactory().get_prompt("chat")
    enhanced_query = state.get("enhanced_query")
    user_message = state.get("user_message", "")
    analysis: ManySearchResults = state.get("analysis", "")

    messages = [
        {"role": OpenAIRolesEnum.SYSTEM.value, "content": prompt_chat},
        {"role": OpenAIRolesEnum.USER.value, "content": user_message},
        {
            "role": OpenAIRolesEnum.ASSISTANT.value,
            "content": "Enhanced query: " + enhanced_query.reranker_query,
        },
        {"role": OpenAIRolesEnum.ASSISTANT.value, "content": analysis},
    ]

    response = nlp_openai.chat(messages, "gpt-4.1", temperature=0.0, top_p=1.0)
    return {"response": response}
