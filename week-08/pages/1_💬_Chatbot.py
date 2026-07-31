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
    "This prototype automatically ingests InvoiceNow web pages, PDFs, and Excel sources in the backend so users can ask questions without uploading files."
)

if "query_history" not in st.session_state:
    st.session_state.query_history = []

if "last_answer" not in st.session_state:
    st.session_state.last_answer = ""

st.sidebar.markdown("---")
if st.sidebar.button("Reset document store"):
    reset_vectorstore()
    st.sidebar.warning("Document store reset. The app will reload backend sources on the next query.")

st.sidebar.markdown(f"**Documents indexed:** {collection_count()}")

st.header("🔍 RAG Query")
st.write(
    "Ask a question and the app will retrieve relevant passages from the automatically ingested backend documents."
)

if collection_count() == 0:
    st.warning("No documents are currently indexed. Fetching backend sources and indexing now...")
    downloaded, errors = download_remote_documents()
    for filename, status in downloaded:
        if status == "downloaded":
            st.sidebar.success(f"Downloaded {filename}")
        else:
            st.sidebar.info(f"Skipped existing {filename}")
    for filename, error in errors:
        st.sidebar.error(f"Failed {filename}: {error}")

    count = populate_sample_documents()
    if count > 0:
        st.success(f"Indexed {count} backend document(s) into the vector store.")
    else:
        st.info("No new backend documents were indexed.")

query = st.text_input("Enter your question", placeholder="Ask about InvoiceNow requirements, FAQs, or GIN tracker details.")
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
