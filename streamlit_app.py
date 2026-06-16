import streamlit as st
import requests
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import os

API_URL = os.getenv("API_URL", "http://localhost:8001")

st.set_page_config(
    page_title="GraphRAG Knowledge System",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
[data-testid="stAppViewContainer"] { background: #0f1117; }
[data-testid="stSidebar"] { background: #1a1d27; border-right: 1px solid #2d2f3e; }
.main-title { font-size: 2rem; font-weight: 700; background: linear-gradient(90deg, #7c6fcd, #56b4d3); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
.metric-card { background: #1a1d27; border: 1px solid #2d2f3e; border-radius: 12px; padding: 1.2rem; text-align: center; }
.metric-val { font-size: 2rem; font-weight: 700; color: #7c6fcd; }
.metric-lbl { font-size: 0.8rem; color: #888; margin-top: 4px; }
.answer-box { background: #1a1d27; border-left: 4px solid #7c6fcd; border-radius: 8px; padding: 1.2rem; line-height: 1.7; }
.chunk-card { background: #1a1d27; border: 1px solid #2d2f3e; border-radius: 8px; padding: 1rem; margin-bottom: 8px; }
.score-badge { background: #7c6fcd22; color: #9d8fe8; border-radius: 20px; padding: 2px 10px; font-size: 0.75rem; font-weight: 600; }
.entity-badge { display: inline-block; background: #56b4d322; color: #56b4d3; border-radius: 20px; padding: 2px 10px; font-size: 0.75rem; margin: 2px; }
</style>
""", unsafe_allow_html=True)

def api_health():
    try:
        return requests.get(f"{API_URL}/health", timeout=5).json()
    except Exception:
        return None

def upload_doc(file):
    try:
        r = requests.post(f"{API_URL}/api/v1/documents/upload",
                          files={"file": (file.name, file.getvalue(), file.type)}, timeout=120)
        return r.json()
    except Exception as e:
        return {"error": str(e)}

def run_query(question):
    try:
        r = requests.post(f"{API_URL}/api/v1/query",
                          json={"question": question}, timeout=60)
        return r.json()
    except Exception as e:
        return {"error": str(e)}

def get_entities():
    try:
        return requests.get(f"{API_URL}/api/v1/graph/entities", timeout=10).json()
    except Exception:
        return []

def get_relations():
    try:
        return requests.get(f"{API_URL}/api/v1/graph/relations", timeout=10).json()
    except Exception:
        return []

with st.sidebar:
    st.markdown('<div class="main-title">🧠 GraphRAG</div>', unsafe_allow_html=True)
    st.caption("Enterprise Knowledge Graph + RAG System")
    st.divider()
    health = api_health()
    if health:
        st.success("API Online", icon="✅")
        chroma = health.get("chroma", {})
        neo4j = health.get("neo4j", {})
        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f'<div class="metric-card"><div class="metric-val">{chroma.get("total_chunks", "—")}</div><div class="metric-lbl">Chunks</div></div>', unsafe_allow_html=True)
        with col2:
            st.markdown(f'<div class="metric-card"><div class="metric-val">{neo4j.get("nodes", "—")}</div><div class="metric-lbl">Entities</div></div>', unsafe_allow_html=True)
        st.markdown(f'<div style="margin-top:8px" class="metric-card"><div class="metric-val">{neo4j.get("relationships", "—")}</div><div class="metric-lbl">Graph Relations</div></div>', unsafe_allow_html=True)
    else:
        st.error("API Offline — is Docker running?")
    st.divider()
    st.markdown("**Pipeline:**")
    st.markdown("📄 Upload → ✂️ Chunk → 🔍 Embed → 🕸️ Extract → 💬 Query")
    st.divider()
    st.caption("Powered by Gemini API + ChromaDB + Neo4j")

tab1, tab2, tab3, tab4 = st.tabs(["💬 Query", "📄 Upload Documents", "🕸️ Knowledge Graph", "📊 Analytics"])

with tab1:
    st.markdown("### Ask anything from your knowledge base")
    st.markdown("The agent searches both your document vectors **and** the entity graph to answer.")
    question = st.text_area("Your question", placeholder="What are the key technologies used by [Company]? How are [Entity A] and [Entity B] related?", height=100)
    col1, col2 = st.columns([1, 5])
    with col1:
        ask_btn = st.button("Ask →", type="primary", use_container_width=True)

    if ask_btn and question.strip():
        with st.spinner("Agent is searching vectors + graph..."):
            result = run_query(question)

        if "error" in result:
            st.error(f"Error: {result['error']}")
        else:
            st.markdown("#### Answer")
            st.markdown(f'<div class="answer-box">{result.get("answer","")}</div>', unsafe_allow_html=True)

            entities = result.get("query_entities", [])
            if entities:
                st.markdown("**Detected query entities:** " + " ".join(f'<span class="entity-badge">{e}</span>' for e in entities), unsafe_allow_html=True)

            col_v, col_g = st.columns(2)
            with col_v:
                st.markdown("##### Vector search results")
                for r in result.get("vector_results", []):
                    st.markdown(f'<div class="chunk-card"><div style="margin-bottom:6px"><span class="score-badge">Score: {r["score"]}</span> <span style="color:#888;font-size:0.75rem">Doc: {r["metadata"].get("doc_id","?")}</span></div><div style="font-size:0.85rem;color:#ccc">{r["text"][:300]}...</div></div>', unsafe_allow_html=True)

            with col_g:
                st.markdown("##### Graph relationships found")
                graph_results = result.get("graph_results", [])
                if graph_results:
                    for r in graph_results[:10]:
                        if r.get("relation"):
                            st.markdown(f'`{r["source"]}` ──[**{r["relation"]}**]──→ `{r["target"]}`')
                        else:
                            st.markdown(f'📍 `{r["source"]}`')
                else:
                    st.info("No graph relationships found for this query.")

with tab2:
    st.markdown("### Upload documents to the knowledge base")
    st.info("Supported formats: **PDF**, **DOCX**, **TXT**. Each document is chunked, embedded into ChromaDB, and entities/relations are extracted into Neo4j.")
    uploaded = st.file_uploader("Drag & drop or browse", type=["pdf", "docx", "txt"], accept_multiple_files=True)

    if uploaded:
        if st.button("🚀 Process All Documents", type="primary"):
            for f in uploaded:
                with st.spinner(f"Processing **{f.name}**..."):
                    result = upload_doc(f)
                if "error" in result:
                    st.error(f"❌ {f.name}: {result['error']}")
                else:
                    st.success(f"✅ **{f.name}** — {result['chunks_indexed']} chunks | {result['entities_extracted']} entities | {result['relations_extracted']} relations")

with tab3:
    st.markdown("### Knowledge Graph Explorer")
    col1, col2 = st.columns([1, 1])
    with col1:
        if st.button("🔄 Load Graph", use_container_width=True):
            with st.spinner("Loading entities and relations..."):
                st.session_state["entities"] = get_entities()
                st.session_state["relations"] = get_relations()
                st.success(f"Loaded {len(st.session_state['entities'])} entities and {len(st.session_state['relations'])} relations")

    entities = st.session_state.get("entities", [])
    relations = st.session_state.get("relations", [])

    if entities:
        st.markdown(f"**{len(entities)} entities** · **{len(relations)} relationships**")

        if relations:
            import math, random
            random.seed(42)
            unique_nodes = list({e["name"] for e in entities})[:60]
            pos = {n: (math.cos(2*math.pi*i/len(unique_nodes)), math.sin(2*math.pi*i/len(unique_nodes))) for i, n in enumerate(unique_nodes)}

            edge_x, edge_y = [], []
            for r in relations[:150]:
                if r["source"] in pos and r["target"] in pos:
                    x0, y0 = pos[r["source"]]
                    x1, y1 = pos[r["target"]]
                    edge_x += [x0, x1, None]; edge_y += [y0, y1, None]

            node_x = [pos[n][0] for n in unique_nodes]
            node_y = [pos[n][1] for n in unique_nodes]

            fig = go.Figure()
            fig.add_trace(go.Scatter(x=edge_x, y=edge_y, mode="lines",
                line=dict(color="#7c6fcd44", width=1), hoverinfo="none"))
            fig.add_trace(go.Scatter(x=node_x, y=node_y, mode="markers+text",
                text=unique_nodes, textposition="top center",
                textfont=dict(size=9, color="#ccc"),
                marker=dict(size=10, color="#7c6fcd", line=dict(color="#56b4d3", width=1)),
                hovertext=unique_nodes, hoverinfo="text"))
            fig.update_layout(
                showlegend=False, height=520,
                paper_bgcolor="#0f1117", plot_bgcolor="#0f1117",
                xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                margin=dict(l=10, r=10, t=10, b=10)
            )
            st.plotly_chart(fig, use_container_width=True)

        with st.expander("Entity table"):
            if entities:
                df = pd.DataFrame(entities)
                st.dataframe(df, use_container_width=True, height=300)

        with st.expander("Relationships table"):
            if relations:
                df = pd.DataFrame(relations)
                st.dataframe(df, use_container_width=True, height=300)
    else:
        st.info("Click 'Load Graph' to visualise the knowledge graph after uploading documents.")

with tab4:
    st.markdown("### System Analytics")
    health = api_health()
    if health:
        chroma = health.get("chroma", {})
        neo4j = health.get("neo4j", {})
        c1, c2, c3 = st.columns(3)
        with c1:
            st.markdown(f'<div class="metric-card"><div class="metric-val">{chroma.get("total_chunks","—")}</div><div class="metric-lbl">Total vector chunks</div></div>', unsafe_allow_html=True)
        with c2:
            st.markdown(f'<div class="metric-card"><div class="metric-val">{neo4j.get("nodes","—")}</div><div class="metric-lbl">Knowledge graph nodes</div></div>', unsafe_allow_html=True)
        with c3:
            st.markdown(f'<div class="metric-card"><div class="metric-val">{neo4j.get("relationships","—")}</div><div class="metric-lbl">Graph relationships</div></div>', unsafe_allow_html=True)
        st.divider()
        st.markdown("#### Architecture")
        arch = {
            "Component": ["Streamlit UI", "FastAPI Backend", "ChromaDB", "Neo4j", "Gemini API", "SentenceTransformers"],
            "Role": ["Frontend / User interface", "REST API + orchestration", "Vector similarity search", "Knowledge graph storage", "LLM: extraction + generation", "Document embeddings"],
            "Status": ["✅ Running", "✅ Running", "✅ Connected", "✅ Connected", "✅ Active", "✅ Loaded"]
        }
        st.dataframe(pd.DataFrame(arch), use_container_width=True, hide_index=True)
    else:
        st.warning("Cannot connect to API. Make sure Docker containers are running.")
