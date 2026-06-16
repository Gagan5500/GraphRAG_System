from typing import List, Dict, Any
from neo4j import GraphDatabase
from app.config import settings

_driver = None

def get_driver():
    global _driver
    if _driver is None:
        _driver = GraphDatabase.driver(
            settings.NEO4J_URI,
            auth=(settings.NEO4J_USER, settings.NEO4J_PASSWORD)
        )
    return _driver

def add_entities_and_relations(entities: List[Dict], relations: List[Dict], doc_id: str):
    driver = get_driver()
    with driver.session() as session:
        for entity in entities:
            session.run(
                "MERGE (e:Entity {name: $name}) "
                "ON CREATE SET e.type = $type, e.doc_id = $doc_id "
                "ON MATCH SET e.doc_id = $doc_id",
                name=entity["name"], type=entity.get("type", "UNKNOWN"), doc_id=doc_id
            )
        for rel in relations:
            session.run(
                "MATCH (a:Entity {name: $source}), (b:Entity {name: $target}) "
                "MERGE (a)-[r:RELATES_TO {type: $rel_type}]->(b) "
                "ON CREATE SET r.doc_id = $doc_id",
                source=rel["source"], target=rel["target"],
                rel_type=rel.get("relation", "RELATED"), doc_id=doc_id
            )

def search_graph(query_entities: List[str], depth: int = 2) -> List[Dict]:
    driver = get_driver()
    results = []
    with driver.session() as session:
        for entity in query_entities[:5]:
            records = session.run(
                "MATCH (e:Entity) WHERE toLower(e.name) CONTAINS toLower($name) "
                "OPTIONAL MATCH (e)-[r]->(n) "
                "RETURN e.name AS source, type(r) AS rel, n.name AS target, e.type AS etype LIMIT 20",
                name=entity
            )
            for record in records:
                results.append({
                    "source": record["source"],
                    "relation": record["rel"],
                    "target": record["target"],
                    "entity_type": record["etype"]
                })
    return results

def get_all_entities(limit: int = 200) -> List[Dict]:
    driver = get_driver()
    with driver.session() as session:
        records = session.run(
            "MATCH (e:Entity) RETURN e.name AS name, e.type AS type, e.doc_id AS doc_id LIMIT $limit",
            limit=limit
        )
        return [{"name": r["name"], "type": r["type"], "doc_id": r["doc_id"]} for r in records]

def get_all_relations(limit: int = 300) -> List[Dict]:
    driver = get_driver()
    with driver.session() as session:
        records = session.run(
            "MATCH (a:Entity)-[r]->(b:Entity) "
            "RETURN a.name AS source, type(r) AS relation, b.name AS target LIMIT $limit",
            limit=limit
        )
        return [{"source": r["source"], "relation": r["relation"], "target": r["target"]} for r in records]

def get_stats() -> Dict:
    try:
        driver = get_driver()
        with driver.session() as session:
            nodes = session.run("MATCH (n:Entity) RETURN count(n) AS c").single()["c"]
            rels = session.run("MATCH ()-[r]->() RETURN count(r) AS c").single()["c"]
            return {"nodes": nodes, "relationships": rels}
    except Exception as e:
        return {"error": str(e)}
