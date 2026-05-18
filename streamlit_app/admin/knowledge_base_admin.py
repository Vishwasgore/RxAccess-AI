"""
Knowledge Base Manager — Upload documents to expand RAG knowledge
"""
import streamlit as st
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

st.set_page_config(page_title="Knowledge Base - RxAccess AI", page_icon="📚", layout="wide")

st.title("📚 Knowledge Base Manager")
st.markdown("Expand the AI's medical knowledge by uploading documents. "
            "Uploaded content is instantly searchable by the Medical Assistant.")

# ── Stats bar ────────────────────────────────────────────────────────────────
@st.cache_resource
def get_ingester():
    from src.rag.document_ingester import DocumentIngester
    return DocumentIngester()

ingester = get_ingester()

stats = ingester.vector_store.get_collection_stats()
col1, col2, col3 = st.columns(3)
col1.metric("Total Documents in KB", stats["document_count"])
col2.metric("Vector Store", "ChromaDB")
col3.metric("Embedding Model", "all-MiniLM-L6-v2")

st.markdown("---")

# ── Tabs ─────────────────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4 = st.tabs([
    "📄 Upload File",
    "✏️ Paste Text",
    "📋 View Knowledge Base",
    "🔍 Test Retrieval"
])

# ── TAB 1: Upload File ───────────────────────────────────────────────────────
with tab1:
    st.markdown("### 📄 Upload a Document")
    st.markdown("Supported formats: **PDF**, **TXT**, **MD**, **DOCX**")

    col_up, col_cfg = st.columns([2, 1])

    with col_up:
        uploaded_doc = st.file_uploader(
            "Choose a file",
            type=["pdf", "txt", "md", "docx"],
            help="Drug guides, clinical protocols, formularies, research papers, etc."
        )

    with col_cfg:
        doc_type = st.selectbox(
            "Document Category",
            ["drug_guide", "clinical_protocol", "formulary", "research_paper",
             "patient_education", "drug_interaction", "treatment_guideline", "custom"],
            help="Helps organize and filter the knowledge base"
        )
        chunk_size = st.slider(
            "Chunk Size (chars)",
            min_value=200, max_value=1000, value=500, step=50,
            help="Smaller = more precise retrieval. Larger = more context per chunk."
        )

    if uploaded_doc:
        st.info(f"📄 **{uploaded_doc.name}** ({uploaded_doc.size / 1024:.1f} KB)")

        if st.button("📥 Add to Knowledge Base", type="primary", use_container_width=True):
            with st.spinner(f"Processing {uploaded_doc.name}..."):
                result = ingester.ingest_file(
                    file_bytes=uploaded_doc.getvalue(),
                    filename=uploaded_doc.name,
                    doc_type=doc_type,
                    chunk_size=chunk_size
                )

            if result["status"] == "success":
                st.success(
                    f"✅ **{uploaded_doc.name}** added successfully!\n\n"
                    f"- Chunks created: **{result['chunks_added']}**\n"
                    f"- Total KB documents: **{result['total_docs']}**"
                )
                st.cache_resource.clear()  # Refresh ingester stats
            else:
                st.error(f"❌ Failed: {result['error']}")

                # Helpful tips based on error
                if "PDF" in result.get("error", ""):
                    st.info("💡 **Tip:** If your PDF is scanned (image-based), "
                            "the text extractor can't read it directly. "
                            "Try copying the text and using the 'Paste Text' tab instead.")

# ── TAB 2: Paste Text ────────────────────────────────────────────────────────
with tab2:
    st.markdown("### ✏️ Paste Text Directly")
    st.markdown("Copy-paste drug information, guidelines, or any medical text.")

    col_t1, col_t2 = st.columns([3, 1])

    with col_t1:
        source_name = st.text_input(
            "Document Name / Title",
            placeholder="e.g. Amoxicillin Drug Guide, Diabetes Treatment Protocol 2024"
        )
        pasted_text = st.text_area(
            "Paste your text here",
            height=300,
            placeholder="""Example:
Drug: Amoxicillin
Class: Penicillin Antibiotic
Uses: Bacterial infections including ear infections, pneumonia, UTIs, skin infections
Dosage: 250-500mg every 8 hours or 500-875mg every 12 hours
Side Effects: Diarrhea, nausea, rash, allergic reactions
Precautions: Avoid if penicillin allergy. Complete full course even if feeling better.
Interactions: Warfarin (increased bleeding risk), oral contraceptives (reduced effectiveness)"""
        )

    with col_t2:
        st.markdown("**Settings**")
        text_doc_type = st.selectbox(
            "Category",
            ["drug_guide", "clinical_protocol", "formulary", "research_paper",
             "patient_education", "drug_interaction", "treatment_guideline", "custom"],
            key="text_doc_type"
        )
        text_chunk_size = st.slider(
            "Chunk Size",
            min_value=200, max_value=1000, value=500, step=50,
            key="text_chunk_size"
        )

        if pasted_text:
            word_count = len(pasted_text.split())
            char_count = len(pasted_text)
            estimated_chunks = max(1, char_count // text_chunk_size)
            st.markdown("**Preview:**")
            st.caption(f"Words: {word_count}")
            st.caption(f"Characters: {char_count}")
            st.caption(f"Est. chunks: ~{estimated_chunks}")

    if st.button("📥 Add Text to Knowledge Base", type="primary",
                 use_container_width=True, disabled=not (source_name and pasted_text)):
        if not source_name:
            st.warning("Please enter a document name.")
        elif not pasted_text.strip():
            st.warning("Please paste some text.")
        else:
            with st.spinner("Processing text..."):
                result = ingester.ingest_text(
                    text=pasted_text,
                    source_name=source_name,
                    doc_type=text_doc_type,
                    chunk_size=text_chunk_size
                )

            if result["status"] == "success":
                st.success(
                    f"✅ **{source_name}** added!\n\n"
                    f"- Chunks: **{result['chunks_added']}**\n"
                    f"- Total KB: **{result['total_docs']}** documents"
                )
            else:
                st.error(f"❌ Failed: {result['error']}")

# ── TAB 3: View Knowledge Base ───────────────────────────────────────────────
with tab3:
    st.markdown("### 📋 Current Knowledge Base Contents")

    if st.button("🔄 Refresh", key="refresh_kb"):
        st.rerun()

    sources = ingester.list_sources()

    if not sources:
        st.info("Knowledge base is empty. Upload documents to get started.")
    else:
        # Group by type
        type_groups: dict = {}
        for src in sources:
            t = src["type"]
            if t not in type_groups:
                type_groups[t] = []
            type_groups[t].append(src)

        total_chunks = sum(s["chunks"] for s in sources)
        st.caption(f"**{len(sources)} sources** | **{total_chunks} total chunks**")

        for doc_type_group, group_sources in type_groups.items():
            with st.expander(
                f"📁 {doc_type_group.replace('_', ' ').title()} ({len(group_sources)} sources)",
                expanded=True
            ):
                for src in group_sources:
                    col_s, col_c, col_d = st.columns([4, 1, 1])
                    col_s.write(f"📄 **{src['source']}**")
                    col_c.caption(f"{src['chunks']} chunks")

                    # Only allow deleting custom/uploaded sources
                    built_in = ["drug_info", "interactions", "side_effects", "conditions"]
                    if src["source"] not in built_in:
                        if col_d.button("🗑️", key=f"del_{src['source']}", help="Delete this source"):
                            result = ingester.delete_source(src["source"])
                            if result["status"] == "success":
                                st.success(f"Deleted '{src['source']}' ({result['deleted_chunks']} chunks)")
                                st.rerun()
                            else:
                                st.error(result["error"])
                    else:
                        col_d.caption("built-in")

# ── TAB 4: Test Retrieval ────────────────────────────────────────────────────
with tab4:
    st.markdown("### 🔍 Test RAG Retrieval")
    st.markdown("See exactly which documents get retrieved for a given question.")

    test_query = st.text_input(
        "Enter a test question",
        placeholder="e.g. What are the side effects of Metformin?"
    )
    n_results = st.slider("Number of results to retrieve", 1, 10, 3)

    if st.button("🔍 Search Knowledge Base", type="primary") and test_query:
        with st.spinner("Searching..."):
            results = ingester.vector_store.query(test_query, n_results=n_results)

        if results["documents"]:
            st.success(f"Found **{len(results['documents'])}** relevant chunks")

            for i, (doc, meta, dist) in enumerate(
                zip(results["documents"], results["metadatas"], results["distances"]), 1
            ):
                relevance = max(0, 1 - dist) * 100
                with st.expander(
                    f"[{i}] {meta.get('source', 'Unknown')} — "
                    f"Type: {meta.get('type', '?')} — "
                    f"Relevance: {relevance:.1f}%",
                    expanded=(i == 1)
                ):
                    st.markdown(f"**Source:** `{meta.get('source')}`")
                    st.markdown(f"**Type:** `{meta.get('type')}`")
                    st.markdown(f"**Relevance Score:** {relevance:.1f}%")
                    st.progress(min(relevance / 100, 1.0))
                    st.markdown("**Content:**")
                    st.text(doc)
        else:
            st.warning("No results found. Try a different query or add more documents.")

    # Show example queries
    st.markdown("---")
    st.markdown("**Example queries to try:**")
    examples = [
        "What are the side effects of Metformin?",
        "Drug interactions with Warfarin",
        "How to manage hypertension lifestyle",
        "Atorvastatin precautions",
        "Diabetes monitoring guidelines",
    ]
    cols = st.columns(len(examples))
    for i, ex in enumerate(examples):
        if cols[i].button(ex, key=f"ex_{i}", use_container_width=True):
            st.session_state["test_query_prefill"] = ex
            st.rerun()
