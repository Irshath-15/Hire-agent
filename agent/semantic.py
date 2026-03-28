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
    # Use OpenAI embeddings if available, fallback to simple hash
    if OpenAI and os.getenv('OPENAI_API_KEY'):
        try:
            return openai_embed_text(text)
        except Exception:
            pass
    # fallback to simple deterministic embedding
    key = hashlib.sha256(text.encode("utf-8")).hexdigest()
    return key


def similarity(text_a: str, text_b: str) -> float:
    # Use OpenAI embeddings for better similarity if available
    if OpenAI and os.getenv('OPENAI_API_KEY'):
        try:
            emb_a = openai_embed_text(text_a)
            emb_b = openai_embed_text(text_b)
            return vector_similarity(emb_a, emb_b)
        except Exception:
            pass
    # fallback to TF-IDF
    vec_a = _text_to_vector(text_a)
    vec_b = _text_to_vector(text_b)
    return cosine_similarity(vec_a, vec_b)


def vector_similarity(embedding_a: str, embedding_b: str) -> float:
    # Cosine similarity for OpenAI embeddings
    if not embedding_a or not embedding_b:
        return 0.0
    try:
        vec_a = [float(x) for x in embedding_a.split(',')]
        vec_b = [float(x) for x in embedding_b.split(',')]
        if len(vec_a) != len(vec_b):
            return 0.0
        numerator = sum(a * b for a, b in zip(vec_a, vec_b))
        sum_a = sum(x * x for x in vec_a)
        sum_b = sum(x * x for x in vec_b)
        denominator = math.sqrt(sum_a) * math.sqrt(sum_b)
        return float(numerator / denominator) if denominator else 0.0
    except:
        # If not vectors, treat as hashes
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
