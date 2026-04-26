import os

from app.rag.loaders import load_guideline_pdfs
from app.rag.chunking import chunk_documents
from app.rag.vectorstore import build_faiss_index, save_faiss_index
from dotenv import load_dotenv

load_dotenv()


def main() -> None:

    print("Loading guideline PDFs...")
    docs = load_guideline_pdfs()
    print(f"Loaded {len(docs)} page-level documents.")

    print("Chunking documents...")
    chunks = chunk_documents(docs)
    print(f"Created {len(chunks)} chunks.")

    print("Building FAISS index...")
    vectorstore = build_faiss_index(chunks)

    print("Saving FAISS index...")
    save_faiss_index(vectorstore)

    print("Done. Guideline FAISS index created successfully.")


if __name__ == "__main__":
    main()