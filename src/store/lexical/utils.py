import nltk
import pyarabic.araby as araby
from nltk.stem.isri import ISRIStemmer


def preprocess_arabic(text: str) -> str:
    text = araby.strip_tashkeel(text)
    text = araby.normalize_alef(text)
    text = araby.normalize_hamza(text)
    text = araby.strip_tatweel(text)
    return text


def arabic_tokenizer(text: str) -> list[str]:
    tokens = araby.tokenize(text)
    stemmer = ISRIStemmer()
    try:
        arabic_stopwords = set(nltk.corpus.stopwords.words("arabic"))
    except LookupError:
        nltk.download("stopwords")
        arabic_stopwords = set(nltk.corpus.stopwords.words("arabic"))

    return [stemmer.stem(t) for t in tokens if t not in arabic_stopwords and len(t) > 1]
