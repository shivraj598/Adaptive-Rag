"""
Document upload and processing module.
"""

import os
from pathlib import Path

from fastapi import UploadFile, File
from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

from src.rag.retriever_setup import retriever_chain
from src.tools.common_tools import enhance_description_with_llm

UPLOADS_DIR = Path(__file__).parent.parent.parent / "uploads"


def documents(description: str, session_id: str, file: UploadFile = File(...)):
    """
    Process and upload a document for RAG.

    Validates file type, saves file to disk, loads content, enhances description,
    chunks documents, and stores them in the vector database.

    Args:
        description: User-provided document description.
        session_id: Session ID to scope the document to.
        file: The uploaded file (PDF or TXT).

    Returns:
        Boolean indicating success of the upload process.

    Raises:
        HTTPException: If file type is not supported or loading fails.
    """
    filename = file.filename
    print(filename)
    if not filename.endswith(".pdf") and not filename.endswith(".txt"):
        from fastapi import HTTPException
        raise HTTPException(
            status_code=400,
            detail="Only PDF and TXT files are supported"
        )

    # Persist file to uploads/{session_id}/
    session_dir = UPLOADS_DIR / session_id
    session_dir.mkdir(parents=True, exist_ok=True)
    file_path = session_dir / filename

    file_bytes = file.file.read()
    with open(file_path, "wb") as f:
        f.write(file_bytes)

    print(f"Saved file to {file_path}")

    # Load document from saved file
    if filename.endswith(".pdf"):
        loader = PyPDFLoader(str(file_path))
    else:
        loader = TextLoader(str(file_path), encoding="utf-8")

    try:
        docs = loader.load()
    except Exception as e:
        from fastapi import HTTPException
        raise HTTPException(
            status_code=500,
            detail=f"Error loading file: {e}"
        )

    # Enhance description using LLM
    description_llm = enhance_description_with_llm(description)

    # Save enhanced description
    with open("description.txt", "w", encoding="utf-8") as f:
        f.write(description_llm)

    with open("description.txt", "r", encoding="utf-8") as f:
        print("Document description from storage:")
        print(f.read())

    # Split documents into chunks
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=150
    )
    chunks = splitter.split_documents(docs)

    # Tag each chunk with the session_id
    for chunk in chunks:
        chunk.metadata["session_id"] = session_id

    return retriever_chain(chunks)
