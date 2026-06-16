import google.generativeai as genai
from typing import Dict, Any
from app.config import settings
from app import chroma_store, neo4j_store, extractor

genai.configure(api_key=settings.GEMINI_API_KEY)
_model = None

def get_model():
    global _model
    if _model is None:
        _model = genai.GenerativeModel(settings.GEMINI_MODEL)
    return _model

ANSWER_PROMPT = """You are an expert knowledge assistant. Use the retrieved context to answer the question.

VECTOR SEARCH RESULTS (semantic similarity from documents):
{vector_context}

GRAPH SEARCH RESULTS (entity relationships from knowledge graph):
{graph_context}

QUESTION: {question}

Instructions:
- Answer thoroughly based on the provided context
- Cite sources when referencing specific document chunks
- If the graph reveals relationships between entities, explain them
- If context is insufficient, say so clearly
- Be concise but complete

ANSWER:"""

def run_query(question: str) -> Dict[str, Any]:
    query_entities = extractor.extract_query_entities(question)
    vector_results = chroma_store.search(question, n_results=5)
    graph_results = neo4j_store.search_graph(query_entities, depth=2)
    vector_context = "\n\n".join([
        f"[Chunk {i+1} | Score: {r['score']} | Doc: {r['metadata'].get('doc_id','?')}]\n{r['text']}"
        for i, r in enumerate(vector_results)
    ]) or "No vector results found."
    graph_context = "\n".join([
        f"- {r['source']} --[{r['relation']}]--> {r['target']}" if r.get("relation")
        else f"- Entity: {r['source']} (type: {r.get('entity_type','?')})"
        for r in graph_results[:20]
    ]) or "No graph results found."
    prompt = ANSWER_PROMPT.format(
        vector_context=vector_context,
        graph_context=graph_context,
        question=question
    )
    model = get_model()
    response = model.generate_content(prompt)
    return {
        "answer": response.text,
        "vector_results": vector_results,
        "graph_results": graph_results,
        "query_entities": query_entities
    }
