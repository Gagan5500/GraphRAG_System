import json
import re
import google.generativeai as genai
from typing import List, Dict, Tuple
from app.config import settings

genai.configure(api_key=settings.GEMINI_API_KEY)
_model = None

def get_model():
    global _model
    if _model is None:
        _model = genai.GenerativeModel(settings.GEMINI_MODEL)
    return _model

EXTRACT_PROMPT = """Extract entities and relationships from the text below.

Return ONLY valid JSON in this exact format:
{{
  "entities": [
    {{"name": "entity name", "type": "PERSON|ORGANIZATION|LOCATION|CONCEPT|TECHNOLOGY|EVENT|OTHER"}}
  ],
  "relations": [
    {{"source": "entity1", "relation": "RELATION_TYPE", "target": "entity2"}}
  ]
}}

Rules:
- Extract 3-15 meaningful entities per chunk
- Extract 2-10 meaningful relationships
- Relation types should be verbs like WORKS_AT, FOUNDED, USES, PART_OF, RELATED_TO
- Only include entities that actually appear in the text
- Return ONLY the JSON, no explanation

TEXT:
{text}"""

def extract_entities_and_relations(text: str) -> Tuple[List[Dict], List[Dict]]:
    model = get_model()
    try:
        prompt = EXTRACT_PROMPT.format(text=text[:3000])
        response = model.generate_content(prompt)
        raw = response.text.strip()
        raw = re.sub(r"```json|```", "", raw).strip()
        data = json.loads(raw)
        entities = data.get("entities", [])
        relations = data.get("relations", [])
        entity_names = {e["name"] for e in entities}
        relations = [r for r in relations if r["source"] in entity_names and r["target"] in entity_names]
        return entities, relations
    except Exception as e:
        return [], []

def extract_query_entities(query: str) -> List[str]:
    model = get_model()
    try:
        prompt = f"""Extract key entities from this search query for a knowledge graph lookup.
Return ONLY a JSON array of entity name strings. Example: ["Apple", "Tim Cook"]
Query: {query}"""
        response = model.generate_content(prompt)
        raw = response.text.strip()
        raw = re.sub(r"```json|```", "", raw).strip()
        return json.loads(raw)
    except Exception:
        return query.split()[:5]
