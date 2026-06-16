from fastapi import FastAPI, UploadFile, File, HTTPException
from pydantic import BaseModel
from typing import List
from app import loader, chunker, chroma_store, neo4j_store, extractor, agent

app = FastAPI(title="GraphRAG API", version="1.0.0")

class QueryRequest(BaseModel):
    question: str

@app.get("/health")
def health():
    return {
        "status": "ok",
        "chroma": chroma_store.get_stats(),
        "neo4j": neo4j_store.get_stats()
    }

@app.post("/api/v1/documents/upload")
async def upload_document(file: UploadFile = File(...)):
    content = await file.read()
    try:
        text = loader.load_document(content, file.filename)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    chunks = chunker.chunk_text(text)
    doc_id = file.filename.replace(" ", "_")
    chroma_store.add_chunks(chunks, doc_id=doc_id, metadata={"filename": file.filename})
    total_entities, total_relations = 0, 0
    for chunk in chunks[:20]:
        entities, relations = extractor.extract_entities_and_relations(chunk)
        if entities:
            neo4j_store.add_entities_and_relations(entities, relations, doc_id=doc_id)
            total_entities += len(entities)
            total_relations += len(relations)
    return {
        "doc_id": doc_id,
        "chunks_indexed": len(chunks),
        "entities_extracted": total_entities,
        "relations_extracted": total_relations
    }

@app.post("/api/v1/query")
def query(request: QueryRequest):
    result = agent.run_query(request.question)
    return result

@app.get("/api/v1/graph/entities")
def get_entities():
    return neo4j_store.get_all_entities()

@app.get("/api/v1/graph/relations")
def get_relations():
    return neo4j_store.get_all_relations()
