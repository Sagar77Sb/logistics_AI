from qdrant_client import QdrantClient
# from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI
from config import QDRANT_LOCAL_PATH, QDRANT_COLLECTION

def get_qdrant_client():
    return QdrantClient(path=QDRANT_LOCAL_PATH)

def build_prompt(context, question):
    return f"""
You are a logistics RAG assistant.

Rules:
1. Answer only from the provided context.
2. Do not guess.
3. If answer is not available, say:
"I could not find this information in the uploaded logistics documents."
4. Keep the answer simple and practical.

Context:
{context}

Question:
{question}
"""

def ask_rag(question):
    client = get_qdrant_client()

    if not client.collection_exists(collection_name=QDRANT_COLLECTION):
        return {
            "question": question,
            "answer": "RAG collection not found. Please run ingestion first.",
            "sources": []
        }

    # embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
    # llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    embeddings = GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-001")
    # embeddings = GoogleGenerativeAIEmbeddings(model="models/text-embedding-004")
    llm = ChatGoogleGenerativeAI(model='gemini-2.5-flash', temperature=0)

    query_vector = embeddings.embed_query(question)

    results = client.query_points(
        collection_name=QDRANT_COLLECTION,
        query=query_vector,
        limit=5,
        with_payload=True
    )

    context = ""
    sources = []

    for point in results.points:
        payload = point.payload or {}

        context += payload.get("text", "") + "\n\n"

        sources.append({
            "file_name": payload.get("file_name"),
            "page_no": payload.get("page_no"),
            "score": point.score
        })

    if not context.strip():
        return {
            "question": question,
            "answer": "I could not find this information in the uploaded logistics documents.",
            "sources": []
        }

    prompt = build_prompt(context, question)
    response = llm.invoke(prompt)

    return {
        "question": question,
        "answer": response.content,
        "sources": sources
    }