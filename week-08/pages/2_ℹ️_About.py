import streamlit as st
from helper_functions.utility import check_password

# region <--------- Streamlit Page Configuration --------->

st.set_page_config(
    layout="centered",
    page_title="About Us",
    page_icon="ℹ️",
)

# Do not continue if check_password is not True.
if not check_password():
    st.stop()

# endregion <--------- Streamlit Page Configuration --------->

st.title("ℹ️ About Us")

st.write(
    "This prototype is designed to demonstrate a simple role-based RAG web app built with Streamlit."
)

st.markdown("### What this app delivers")
st.write(
    "- **Admin upload flow**: an admin can upload documents that are indexed into a vector store."
)
st.write("- **Query experience**: users ask questions and receive answers grounded in the uploaded documents.")
st.write("- **Results export**: answers can be downloaded as text for later use.")

st.markdown("### Who is this for?")
st.write(
    "This project is suitable for an educational AI prototype, product demos, and early-stage research into document-based retrieval systems."
)

st.markdown("### Contact")
st.write(
    "If you want to extend this app, add richer file format support (PDF, DOCX), deploy to Streamlit Cloud, or connect a real database for user sessions."
)
