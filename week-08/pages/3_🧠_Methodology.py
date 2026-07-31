import streamlit as st
from helper_functions.utility import check_password

# region <--------- Streamlit Page Configuration --------->

st.set_page_config(
    layout="centered",
    page_title="Methodology",
    page_icon="🧠",
)

# Do not continue if check_password is not True.
if not check_password():
    st.stop()

# endregion <--------- Streamlit Page Configuration --------->

st.title("🧠 Methodology")

st.write(
    "This page explains how the retrieval-augmented generation prototype works."
)

st.markdown("### App architecture")
st.write(
    "1. **Document ingestion**: Admins upload `.txt` files, which are converted into embeddings and stored in a Chroma vector database."
)
st.write(
    "2. **Vector search**: When a user asks a question, the app encodes the question and retrieves the most relevant document passages from the vector store."
)
st.write(
    "3. **Generative answer**: The retrieved passages are included in a prompt that is sent to the OpenAI chat model, producing an answer grounded in the source documents."
)

st.markdown("### Features")
st.write("- Document management with Admin uploads")
st.write("- RAG-based query with context-aware retrieval")
st.write("- Optional answer summarization")
st.write("- Answer export as a text download")

st.markdown("### Deployment notes")
st.write(
    "This prototype can be deployed with Streamlit Cloud or any Python-compatible hosting service. "
    "In production, add access control, persistent API keys, and support for richer document formats."
)
