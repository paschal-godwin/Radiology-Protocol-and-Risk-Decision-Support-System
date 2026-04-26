from pathlib import Path
from typing import List

from langchain_core.documents import Document
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings


INDEX_DIR = Path("data/vectorstore/faiss_index")


def get_embeddings() -> OpenAIEmbeddings:
    """
    Create the embeddings client.
    """
    return OpenAIEmbeddings(model="text-embedding-3-small")


def build_faiss_index(documents: List[Document]) -> FAISS:
    """
    Build a FAISS index from chunked documents.
    """
    embeddings = get_embeddings()
    return FAISS.from_documents(documents, embeddings)


def save_faiss_index(vectorstore: FAISS, index_dir: Path = INDEX_DIR) -> None:
    """
    Persist the FAISS index locally.
    """
    index_dir.parent.mkdir(parents=True, exist_ok=True)
    vectorstore.save_local(str(index_dir))


def load_faiss_index(index_dir: Path = INDEX_DIR) -> FAISS:
    """
    Load a persisted FAISS index.
    """
    embeddings = get_embeddings()

    if not index_dir.exists():
        raise FileNotFoundError(
            f"FAISS index directory not found: {index_dir}. "
            f"Run the ingestion script first."
        )

    return FAISS.load_local(
        str(index_dir),
        embeddings,
        allow_dangerous_deserialization=True,
    )