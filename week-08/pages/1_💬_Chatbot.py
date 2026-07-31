import uuid
from pathlib import Path

import streamlit as st
from helper_functions.llm import (
    add_documents_to_vectorstore,
    collection_count,
    download_remote_documents,
    get_all_documents,
    pdf_bytes_to_text,
    populate_sample_documents,
    query_with_rag,
    reset_vectorstore,
    summarize_text,
)
from helper_functions.utility import check_password

# region <--------- Streamlit Page Configuration --------->

st.set_page_config(
    layout="wide",
    page_title="RAG Chatbot",
    page_icon="💬",
)

# Do not continue if check_password is not True.
if not check_password():
    st.stop()

# endregion <--------- Streamlit Page Configuration --------->

st.title("💬 RAG Chatbot")
st.write(
    "This prototype supports role-based document management and retrieval-augmented generation using a Chroma vector store."
)

if "query_history" not in st.session_state:
    st.session_state.query_history = []

if "last_answer" not in st.session_state:
    st.session_state.last_answer = ""

role = st.sidebar.radio("Role", ["User", "Admin"], index=0)

st.sidebar.markdown("---")
if st.sidebar.button("Load sample documents"):
    count = populate_sample_documents()
    if count > 0:
        st.sidebar.success(f"Loaded {count} sample documents into the vector store.")
    else:
        st.sidebar.info("Sample documents are already loaded or missing.")

if st.sidebar.button("Reset document store"):
    reset_vectorstore()
    st.sidebar.warning("Document store reset. Upload files or load sample documents again.")

if st.sidebar.button("Fetch remote InvoiceNow sources"):
    downloaded, errors = download_remote_documents()
    for filename, status in downloaded:
        if status == "downloaded":
            st.sidebar.success(f"Downloaded {filename}")
        else:
            st.sidebar.info(f"Skipped existing {filename}")
    for filename, error in errors:
        st.sidebar.error(f"Failed {filename}: {error}")
    st.sidebar.info("Then click 'Load sample documents' to index the fetched sources.")

st.sidebar.markdown(f"**Documents indexed:** {collection_count()}")

# ── Admin panel ─────────────────────────────────────────────────────────────
if role == "Admin":
    st.header("📄 Admin — Document Management")
    st.write(
        "Upload `.txt` documents to index them in the vector store. This enables the User role to ask context-aware questions."
    )

    uploaded_files = st.file_uploader(
        "Upload documents",
        type=["txt", "pdf"],
        accept_multiple_files=True,
        help="Each file is stored as a separate document in the vector store.",
    )

    if uploaded_files:
        if st.button("Add uploaded documents"):
            docs, ids, metadatas = [], [], []
            for uploaded_file in uploaded_files:
                file_bytes = uploaded_file.getvalue()
                if uploaded_file.name.lower().endswith(".pdf"):
                    content = pdf_bytes_to_text(file_bytes)
                else:
                    content = file_bytes.decode("utf-8", errors="ignore").strip()
                if not content:
                    continue
                doc_id = f"uploaded-{uuid.uuid4()}"
                docs.append(content)
                ids.append(doc_id)
                metadatas.append({"source": uploaded_file.name})

            if docs:
                add_documents_to_vectorstore(docs, ids, metadatas=metadatas)
                st.success(f"Indexed {len(docs)} document(s) into the vector store.")
            else:
                st.error("No valid text content found in uploaded files.")

    st.markdown("### Current indexed documents")
    docs = get_all_documents()
    if docs:
        for doc_id, metadata, content in docs:
            st.write(f"**{metadata.get('source', doc_id)}**")
            st.caption(f"ID: {doc_id}")
            st.write(content[:250] + ("..." if len(content) > 250 else ""))
            st.markdown("---")
    else:
        st.info("No documents are currently indexed. Upload files or load sample documents.")

# ── User panel ──────────────────────────────────────────────────────────────
else:
    st.header("🔍 User — RAG Query")
    st.write(
        "Ask a question and the app will retrieve relevant passages from the indexed documents before answering."
    )

    if collection_count() == 0:
        st.warning("No documents are currently indexed. Ask an Admin to upload documents or load sample documents.")

    query = st.text_input("Enter your question", placeholder="What can this document set tell me?")
    top_k = st.slider("Number of retrieved documents", min_value=1, max_value=5, value=3)
    summarize = st.checkbox("Provide a short summary for the answer", value=False)

    if query and st.button("Get Answer"):
        answer, sources = query_with_rag(query, top_k=top_k)
        st.session_state.last_answer = answer
        st.session_state.query_history.append({
            "question": query,
            "answer": answer,
            "sources": sources,
        })

    if st.session_state.last_answer:
        st.subheader("Answer")
        st.write(st.session_state.last_answer)

        if summarize:
            summary = summarize_text(st.session_state.last_answer)
            st.markdown("**Summary:**")
            st.write(summary)

        if st.download_button(
            "Download answer",
            st.session_state.last_answer,
            file_name="rag_answer.txt",
            mime="text/plain",
        ):
            st.success("Answer downloaded.")

        if st.session_state.query_history[-1]["sources"]:
            st.markdown("**Source documents:**")
            for source in st.session_state.query_history[-1]["sources"]:
                st.write(f"- {source}")

    if st.session_state.query_history:
        st.markdown("---")
        st.subheader("Recent query history")
        for item in reversed(st.session_state.query_history[-5:]):
            st.markdown(f"**Q:** {item['question']}")
            st.markdown(f"**A:** {item['answer']}" )
            if item["sources"]:
                st.markdown(f"**Sources:** {', '.join(item['sources'])}")
            st.markdown("---")
