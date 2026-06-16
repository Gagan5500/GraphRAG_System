from typing import List, Dict, Any
import chromadb
from sentence_transformers import SentenceTransformer
from app.config import settings

_client = None
_collection = None
_embedder = None

def get_embedder():
    global _embedder
    if _embedder is None:
        _embedder = SentenceTransformer(settings.EMBED_MODEL)
    return _embedder

def get_collection():
    global _client, _collection
    if _client is None:
        _client = chromadb.HttpClient(host=settings.CHROMA_HOST, port=settings.CHROMA_PORT)
    if _collection is None:
        _collection = _client.get_or_create_collection(
            name=settings.CHROMA_COLLECTION,
            metadata={"hnsw:space": "cosine"}
        )
    return _collection

def add_chunks(chunks: List[str], doc_id: str, metadata: Dict[str, Any] = None):
    col = get_collection()
    embedder = get_embedder()
    embeddings = embedder.encode(chunks).tolist()
    ids = [f"{doc_id}_chunk_{i}" for i in range(len(chunks))]
    metas = [{**(metadata or {}), "doc_id": doc_id, "chunk_index": i} for i in range(len(chunks))]
    col.add(documents=chunks, embeddings=embeddings, ids=ids, metadatas=metas)
    return len(chunks)

def search(query: str, n_results: int = 5) -> List[Dict]:
    col = get_collection()
    embedder = get_embedder()
    q_emb = embedder.encode([query]).tolist()
    results = col.query(query_embeddings=q_emb, n_results=n_results, include=["documents", "metadatas", "distances"])
    out = []
    for doc, meta, dist in zip(results["documents"][0], results["metadatas"][0], results["distances"][0]):
        out.append({"text": doc, "metadata": meta, "score": round(1 - dist, 4)})
    return out

def get_stats() -> Dict:
    try:
        col = get_collection()
        return {"total_chunks": col.count(), "collection": settings.CHROMA_COLLECTION}
    except Exception as e:
        return {"error": str(e)}
