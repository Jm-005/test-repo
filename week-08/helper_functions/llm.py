import io
import os
from pathlib import Path
import requests
import tiktoken
import streamlit as st
import pandas as pd
from bs4 import BeautifulSoup
from openai import OpenAI
from dotenv import load_dotenv

__import__('pysqlite3')
import sys
sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')

import chromadb
from chromadb.config import Settings
from chromadb.utils import embedding_functions
from pypdf import PdfReader

def pdf_bytes_to_text(pdf_bytes: bytes) -> str:
    """Extracts text content from PDF byte data."""
    pdf_file = io.BytesIO(pdf_bytes)
    reader = PdfReader(pdf_file)
    text = ""
    for page in reader.pages:
        extracted = page.extract_text()
        if extracted:
            text += extracted + "\n"
    return text

if load_dotenv('.env'):
    # for local development
    OPENAI_KEY = os.getenv('OPENAI_API_KEY')
else:
    OPENAI_KEY = st.secrets['OPENAI_API_KEY']

client = OpenAI(api_key=OPENAI_KEY)

EMBED_MODEL = "text-embedding-3-large"
CHAT_MODEL = "gpt-4o-mini"
CHROMA_DIR = Path(__file__).resolve().parents[1] / "chromadb"
CHROMA_DIR.mkdir(parents=True, exist_ok=True)

chroma_client = chromadb.PersistentClient(
    path="./chroma_db",
    settings=Settings(anonymized_telemetry=False)
)

embedding_function = embedding_functions.OpenAIEmbeddingFunction(
    api_key=OPENAI_KEY,
    model_name=EMBED_MODEL,
)

collection = chroma_client.get_or_create_collection(
    name="rag_docs",
    embedding_function=embedding_function,
)


def get_completion(messages, model=CHAT_MODEL, temperature=0):
    response = client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=temperature,
    )
    return response.choices[0].message.content


def get_completion_stream(messages, model=CHAT_MODEL, temperature=0):
    """Returns a streaming generator for use with st.write_stream()."""
    stream = client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=temperature,
        stream=True,
    )
    for chunk in stream:
        delta = chunk.choices[0].delta
        if delta.content:
            yield delta.content


def count_tokens(text, model=CHAT_MODEL):
    """Estimate the number of tokens in a string."""
    try:
        encoding = tiktoken.encoding_for_model(model)
    except KeyError:
        encoding = tiktoken.get_encoding("cl100k_base")
    return len(encoding.encode(text))


def add_documents_to_vectorstore(docs, ids, metadatas=None):
    collection.add(documents=docs, ids=ids, metadatas=metadatas)
    chroma_client.persist()


def collection_count() -> int:
    return collection.count()


def get_all_documents():
    try:
        data = collection.get(include=["documents", "metadatas", "ids"])
    except Exception:
        # Some chromadb versions validate include values differently;
        # fall back to a plain get() and extract available keys.
        data = collection.get()
    docs = data.get("documents", [])
    metas = data.get("metadatas", [])
    ids = data.get("ids", [])
    if docs and isinstance(docs[0], list):
        return list(zip(ids[0], metas[0], docs[0]))
    if docs:
        return list(zip(ids, metas, docs))
    return []


def reset_vectorstore():
    global collection
    try:
        chroma_client.delete_collection(name="rag_docs")
    except Exception:
        pass
    collection = chroma_client.get_or_create_collection(
        name="rag_docs",
        embedding_function=embedding_function,
    )
    return collection


def _load_text_file(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _load_pdf_bytes(buffer: bytes) -> str:
    reader = PdfReader(io.BytesIO(buffer))
    pages = []
    for page in reader.pages:
        try:
            pages.append(page.extract_text() or "")
        except Exception:
            pages.append("")
    return "\n\n".join(pages).strip()


def _load_excel_file(path: Path) -> str:
    try:
        sheets = pd.read_excel(path, sheet_name=None)
    except Exception:
        return ""

    sections = []
    for sheet_name, df in sheets.items():
        if df.empty:
            continue
        table_text = df.astype(str).fillna("").to_csv(index=False)
        sections.append(f"Sheet: {sheet_name}\n{table_text}")

    return "\n\n".join(sections).strip()


def _get_existing_ids() -> set:
    existing_ids = set()
    try:
        data = collection.get(include=["ids"])
    except Exception:
        # fall back if the chromadb version rejects the include parameter
        data = collection.get()
    if data and data.get("ids"):
        raw_ids = data["ids"]
        if isinstance(raw_ids, list) and raw_ids and isinstance(raw_ids[0], list):
            existing_ids.update(raw_ids[0])
        else:
            existing_ids.update(raw_ids)
    return existing_ids

REMOTE_PDFS = {
    "etaxguide_gst_invoicenow_requirement.pdf": "https://www.iras.gov.sg/media/docs/default-source/uploadedfiles/gst/etaxguide_gst_invoicenow_requirement.pdf?sfvrsn=d2828aad_35",
    "invoicenow-brochure.pdf": "https://file.go.gov.sg/invoicenow-brochure.pdf",
    "invoicenow-faq.pdf": "https://file.go.gov.sg/invoicenow-faq.pdf",
}

REMOTE_HTML_PAGES = {
    "iras-invoicenow-requirement.txt": "https://www.iras.gov.sg/taxes/goods-services-tax-(gst)/gst-invoicenow-requirement",
    "imda-invoicenow.txt": "https://www.imda.gov.sg/how-we-can-help/nationwide-e-invoicing-framework/invoicenow",
}


def _extract_text_from_html(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "nav", "footer", "header", "button", "svg"]):
        tag.decompose()
    text = soup.get_text(separator="\n")
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    return "\n".join(lines)


def _load_document_file(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix == ".pdf":
        return _load_pdf_bytes(path.read_bytes())
    if suffix == ".txt":
        return _load_text_file(path)
    if suffix in {".xls", ".xlsx"}:
        return _load_excel_file(path)
    return ""


def _save_html_text(dest: Path, html: str) -> None:
    dest.write_text(_extract_text_from_html(html), encoding="utf-8")


def download_remote_documents():
    sample_dir = Path(__file__).resolve().parents[1] / "sample_docs"
    sample_dir.mkdir(parents=True, exist_ok=True)

    downloaded = []
    errors = []
    for filename, url in REMOTE_PDFS.items():
        dest = sample_dir / filename
        if dest.exists():
            downloaded.append((filename, "exists"))
            continue
        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            dest.write_bytes(response.content)
            downloaded.append((filename, "downloaded"))
        except Exception as exc:
            errors.append((filename, str(exc)))

    for filename, url in REMOTE_HTML_PAGES.items():
        dest = sample_dir / filename
        if dest.exists():
            downloaded.append((filename, "exists"))
            continue
        try:
            response = requests.get(
                url,
                timeout=30,
                headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"},
            )
            response.raise_for_status()
            _save_html_text(dest, response.text)
            downloaded.append((filename, "downloaded"))
        except Exception as exc:
            errors.append((filename, str(exc)))

    return downloaded, errors


def _load_local_documents():
    sample_dir = Path(__file__).resolve().parents[1] / "sample_docs"
    if not sample_dir.exists():
        return []

    docs = []
    ids = []
    metadatas = []
    existing_ids = _get_existing_ids()

    candidate_paths = set()
    if sample_dir.exists():
        candidate_paths.update(sample_dir.glob("*"))

    # Also include any Excel files found in the parent assignment folder
    assignment_root = Path(__file__).resolve().parents[2]
    for p in assignment_root.glob("*.xls*"):
        if not p.name.startswith("~$"):
            candidate_paths.add(p)

    for doc_path in sorted(candidate_paths):
        if doc_path.suffix.lower() not in {".txt", ".pdf", ".xls", ".xlsx"}:
            continue
        text = _load_document_file(doc_path)
        if not text.strip():
            continue

        doc_id = f"sample-{doc_path.name}"
        if doc_id in existing_ids:
            continue

        docs.append(text)
        ids.append(doc_id)
        metadatas.append({"source": doc_path.name})

    return docs, ids, metadatas


def populate_sample_documents():
    docs, ids, metadatas = _load_local_documents()
    if docs:
        add_documents_to_vectorstore(docs, ids, metadatas=metadatas)
    return len(docs)


def query_with_rag(question, top_k=3):
    if collection.count() == 0:
        return "No documents are loaded yet. Upload files or refresh the app.", []

    try:
        results = collection.query(
            query_texts=[question],
            n_results=top_k,
            include=["documents", "metadatas"],
        )
    except Exception:
        # Some chromadb versions may validate the include list differently;
        # retry without include and parse whatever is returned.
        results = collection.query(
            query_texts=[question],
            n_results=top_k,
        )
    retrieved_docs = results.get("documents", [])
    retrieved_docs = retrieved_docs[0] if retrieved_docs else []
    retrieved_metas = results.get("metadatas", [])
    retrieved_metas = retrieved_metas[0] if retrieved_metas else []

    if not retrieved_docs:
        return "I could not find relevant information in the current document set.", []

    context_chunks = []
    sources = []
    for doc_text, meta in zip(retrieved_docs, retrieved_metas):
        source_label = meta.get("source", "unknown") if isinstance(meta, dict) else "unknown"
        sources.append(source_label)
        chunk = f"Source: {source_label}\n{doc_text.strip()}"
        context_chunks.append(chunk)

    context = "\n\n---\n\n".join(context_chunks)
    prompt = (
        "You are a helpful assistant that answers questions using the provided document excerpts. "
        "If the answer cannot be found in the excerpts, say you do not know. "
        "Cite the source file names in your response when possible.\n\n"
        f"{context}\n\nQuestion: {question}"
    )

    response = get_completion([
        {"role": "system", "content": "Use the retrieved document excerpts to answer the user's question."},
        {"role": "user", "content": prompt},
    ])
    return response, sources


def summarize_text(text, model=CHAT_MODEL, temperature=0):
    return get_completion([
        {"role": "system", "content": "You are a concise summarization assistant."},
        {"role": "user", "content": f"Summarize the following text in 2-3 sentences:\n\n{text}"},
    ], model=model, temperature=temperature)
