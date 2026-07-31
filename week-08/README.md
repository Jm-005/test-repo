# RAG AI Assistant Prototype

This Streamlit app demonstrates a simple retrieval-augmented generation prototype with role-based document management.

## Features

- Admin upload flow for `.txt` and `.pdf` documents
- Chroma vector store for document retrieval
- User query interface with RAG-based answers
- Optional summarization and download of responses
- About Us and Methodology pages

## Data sources for InvoiceNow

The app is designed to ingest these sources as documents:

- GIN Queries Tracker_wef Nov25 "Responded" tab
- IRAS InvoiceNow webpage: `https://www.iras.gov.sg/taxes/goods-services-tax-(gst)/gst-invoicenow-requirement`
- eTax guide PDF: `https://www.iras.gov.sg/media/docs/default-source/uploadedfiles/gst/etaxguide_gst_invoicenow_requirement.pdf?sfvrsn=d2828aad_35`
- IMDA InvoiceNow webpage: `https://www.imda.gov.sg/how-we-can-help/nationwide-e-invoicing-framework/invoicenow`
- Brochure PDF: `https://file.go.gov.sg/invoicenow-brochure.pdf`
- FAQ PDF: `https://file.go.gov.sg/invoicenow-faq.pdf`

## Web scraping support

The app can fetch and scrape the IRAS and IMDA webpages directly, convert them to text, and index them in the vector store along with the PDF documents.
- IRAS InvoiceNow webpage: `https://www.iras.gov.sg/taxes/goods-services-tax-(gst)/gst-invoicenow-requirement`
- IMDA InvoiceNow webpage: `https://www.imda.gov.sg/how-we-can-help/nationwide-e-invoicing-framework/invoicenow`

## Setup

1. Create a Python environment, for example:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

2. Install dependencies:

```powershell
pip install -r requirements.txt
```

3. Create a `.env` file in `assignment/week-08` with:

```text
OPENAI_API_KEY=your_openai_api_key
```

4. Download the remote InvoiceNow data sources and web pages:

```powershell
python download_remote_docs.py
```

5. Run the app:

```powershell
streamlit run main.py
```

## Deployment

- This app can be deployed to Streamlit Cloud by connecting the GitHub repository.
- Use `requirements.txt` and the `main.py` entrypoint.
- If your repository root is not the `assignment/week-08` folder, set the app path to `assignment/week-08/main.py`.
- Add secrets in Streamlit Cloud for `OPENAI_API_KEY`.
- The password is configured locally in `.streamlit/secrets.toml`, but do not push that file to GitHub.

### Streamlit Cloud setup

1. Commit and push your app folder to GitHub.
2. In Streamlit Cloud, click "New app".
3. Select your GitHub repository and branch.
4. Set the main file to `assignment/week-08/main.py` (or `main.py` if you deploy from the `assignment/week-08` folder directly).
5. Add a secret named `OPENAI_API_KEY` with your value.
6. Deploy.

## Notes

- The app stores embeddings locally in `chromadb/`.
- Use the Admin role to upload documents or fetch remote InvoiceNow sources first, then switch to User to ask queries.
- For production, add better access control, database-backed persistence, and richer file ingest handling.
