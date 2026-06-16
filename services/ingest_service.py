import os
import uuid
from pypdf import PdfReader
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
# from langchain_openai import OpenAIEmbeddings
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from config import QDRANT_LOCAL_PATH, QDRANT_COLLECTION, RAG_FILES_DIR

def get_qdrant_client():
    return QdrantClient(path=QDRANT_LOCAL_PATH)

def extract_pdf_pages(file_path):
    reader = PdfReader(file_path)
    pages = []

    for page_no, page in enumerate(reader.pages, start=1):
        text = page.extract_text() or ""

        if text.strip():
            pages.append({
                "page_no": page_no,
                "text": text
            })
    # print("pages: ", pages)
    return pages

def create_collection_if_not_exists(client, vector_size):
    exists = client.collection_exists(collection_name=QDRANT_COLLECTION)

    if not exists:
        client.create_collection(
            collection_name=QDRANT_COLLECTION,
            vectors_config=VectorParams(
                size=vector_size,
                distance=Distance.COSINE
            )
        )

def ingest_documents():
    client = get_qdrant_client()
    # embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
    embeddings = GoogleGenerativeAIEmbeddings(
    model="models/gemini-embedding-001"
)
    sample_vector = embeddings.embed_query("sample logistics text")
    create_collection_if_not_exists(client, len(sample_vector))

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=150
    )

    points = []

    if not os.path.exists(RAG_FILES_DIR):
        os.makedirs(RAG_FILES_DIR)

    for file_name in os.listdir(RAG_FILES_DIR):
        if not file_name.lower().endswith(".pdf"):
            continue

        file_path = os.path.join(RAG_FILES_DIR, file_name)
        pages = extract_pdf_pages(file_path)

        for page in pages:
            chunks = splitter.split_text(page["text"])

            for chunk in chunks:
                vector = embeddings.embed_query(chunk)

                points.append(
                    PointStruct(
                        id=str(uuid.uuid4()),
                        vector=vector,
                        payload={
                            "text": chunk,
                            "file_name": file_name,
                            "page_no": page["page_no"],
                            "document_type": "logistics_pdf"
                        }
                    )
                )

    if not points:
        return {
            "message": "No PDF content found for ingestion",
            "total_chunks": 0
        }

    client.upsert(
        collection_name=QDRANT_COLLECTION,
        points=points
    )

    return {
        "message": "Documents ingested successfully",
        "total_chunks": len(points),
        "collection": QDRANT_COLLECTION
    }

def reset_collection():
    client = get_qdrant_client()

    if client.collection_exists(collection_name=QDRANT_COLLECTION):
        client.delete_collection(collection_name=QDRANT_COLLECTION)

    return {
        "message": "Collection reset successfully",
        "collection": QDRANT_COLLECTION
    }