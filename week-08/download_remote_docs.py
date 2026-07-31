import os
from pathlib import Path

import requests
from bs4 import BeautifulSoup

REMOTE_PDFS = {
    "etaxguide_gst_invoicenow_requirement.pdf": "https://www.iras.gov.sg/media/docs/default-source/uploadedfiles/gst/etaxguide_gst_invoicenow_requirement.pdf?sfvrsn=d2828aad_35",
    "invoicenow-brochure.pdf": "https://file.go.gov.sg/invoicenow-brochure.pdf",
    "invoicenow-faq.pdf": "https://file.go.gov.sg/invoicenow-faq.pdf",
}

REMOTE_HTML_PAGES = {
    "iras-invoicenow-requirement.txt": "https://www.iras.gov.sg/taxes/goods-services-tax-(gst)/gst-invoicenow-requirement",
    "imda-invoicenow.txt": "https://www.imda.gov.sg/how-we-can-help/nationwide-e-invoicing-framework/invoicenow",
}

DOWNLOAD_DIR = Path(__file__).resolve().parent / "sample_docs"


def _extract_text_from_html(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "nav", "footer", "header", "button", "svg"]):
        tag.decompose()
    text = soup.get_text(separator="\n")
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    return "\n".join(lines)


def download_file(url: str, dest: Path, is_html: bool = False) -> bool:
    try:
        response = requests.get(
            url,
            stream=not is_html,
            timeout=30,
            headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"},
        )
        response.raise_for_status()
        dest.parent.mkdir(parents=True, exist_ok=True)
        if is_html:
            dest.write_text(_extract_text_from_html(response.text), encoding="utf-8")
        else:
            with dest.open("wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
        return True
    except Exception as exc:
        print(f"Failed to download {url}: {exc}")
        return False


def main() -> None:
    print(f"Downloading remote documents into: {DOWNLOAD_DIR}")
    for filename, url in REMOTE_PDFS.items():
        dest = DOWNLOAD_DIR / filename
        if dest.exists():
            print(f"Skipping existing file: {filename}")
            continue
        print(f"Downloading {filename}...")
        success = download_file(url, dest)
        print("Done." if success else "Failed.")

    for filename, url in REMOTE_HTML_PAGES.items():
        dest = DOWNLOAD_DIR / filename
        if dest.exists():
            print(f"Skipping existing file: {filename}")
            continue
        print(f"Fetching and scraping {filename}...")
        success = download_file(url, dest, is_html=True)
        print("Done." if success else "Failed.")

    print("\nCompleted. Add local GIN tracker content manually if needed.")


if __name__ == "__main__":
    main()
