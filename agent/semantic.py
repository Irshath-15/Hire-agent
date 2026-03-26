import os
import math
import hashlib

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None


def _text_to_vector(text: str) -> dict:
    words = [w.strip().lower() for w in text.split() if w.isalnum() or w.isalpha()]
    vec = {}
    for w in words:
        vec[w] = vec.get(w, 0) + 1
    return vec


def cosine_similarity(a: dict, b: dict) -> float:
    if not a or not b:
        return 0.0
    intersection = set(a.keys()) & set(b.keys())
    numerator = sum(a[x] * b[x] for x in intersection)
    sum1 = sum(v * v for v in a.values())
    sum2 = sum(v * v for v in b.values())
    denominator = math.sqrt(sum1) * math.sqrt(sum2)
    return float(numerator / denominator) if denominator else 0.0


def embed_text(text: str) -> str:
    # simple deterministic embedding for prototyping
    key = hashlib.sha256(text.encode("utf-8")).hexdigest()
    return key


def similarity(text_a: str, text_b: str) -> float:
    vec_a = _text_to_vector(text_a)
    vec_b = _text_to_vector(text_b)
    return cosine_similarity(vec_a, vec_b)


def vector_similarity(embedding_a: str, embedding_b: str) -> float:
    # stubs cannot compare hashes, so use 0 or 1 if equal
    return 1.0 if embedding_a == embedding_b and embedding_a else 0.0


def openai_embed_text(text: str) -> str:
    if OpenAI is None:
        raise RuntimeError('openai package not installed')
    key = os.getenv('OPENAI_API_KEY')
    if not key:
        raise RuntimeError('OPENAI_API_KEY not configured')
    client = OpenAI(api_key=key)
    response = client.embeddings.create(model='text-embedding-3-small', input=text)
    vector = response.data[0].embedding
    return ",".join(str(x) for x in vector)
