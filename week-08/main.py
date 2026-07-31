__import__('pysqlite3')
import sys
sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')

import streamlit as st
from helper_functions.utility import check_password

# region <--------- Streamlit Page Configuration --------->

st.set_page_config(
    layout="centered",
    page_title="RAG AI Assistant",
    page_icon="🤖",
)

# Do not continue if check_password is not True.
if not check_password():
    st.stop()

# endregion <--------- Streamlit Page Configuration --------->

st.title("🤖 RAG AI Assistant")

st.write(
    """
Welcome to the RAG-enabled AI Assistant prototype.

This app automatically ingests InvoiceNow webpages, PDFs, and Excel sources as backend documents.
- 🔍 **RAG-based query** — Ask questions and the app retrieves relevant passages from the indexed sources.
- 📝 **Summarization and export** — Summarize and download answers.

Use the left sidebar to switch between the **Chatbot**, **About Us**, and **Methodology** pages.
"""
)
