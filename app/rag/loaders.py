from pathlib import Path
from typing import List

from langchain_community.document_loaders import PyPDFLoader
from langchain_core.documents import Document


GUIDELINES_DIR = Path("data/guidelines")


def load_guideline_pdfs(guidelines_dir: Path = GUIDELINES_DIR) -> List[Document]:
    """
    Load all PDF guidelines from the guidelines directory.

    Returns LangChain Document objects with cleaned metadata.
    """
    if not guidelines_dir.exists():
        raise FileNotFoundError(f"Guidelines directory not found: {guidelines_dir}")

    pdf_paths = sorted(guidelines_dir.glob("*.pdf"))
    if not pdf_paths:
        raise FileNotFoundError(f"No PDF files found in: {guidelines_dir}")

    all_docs: List[Document] = []

    for pdf_path in pdf_paths:
        loader = PyPDFLoader(str(pdf_path))
        docs = loader.load()

        for doc in docs:
            doc.metadata["source_title"] = pdf_path.stem
            doc.metadata["source_path"] = str(pdf_path)

            # PyPDFLoader often stores page index as 0-based "page"
            page_index = doc.metadata.get("page")
            if page_index is not None:
                doc.metadata["page_number"] = int(page_index) + 1
            else:
                doc.metadata["page_number"] = None

        all_docs.extend(docs)

    return all_docs