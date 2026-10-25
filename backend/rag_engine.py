"""Local Ollama-backed retrieval-augmented answer generation."""

import os

import httpx
from dotenv import load_dotenv

import database as db

load_dotenv()

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434").rstrip("/")
OLLAMA_CHAT_MODEL = os.getenv("OLLAMA_CHAT_MODEL", "llama3:latest")
OLLAMA_EMBED_MODEL = os.getenv("OLLAMA_EMBED_MODEL", "nomic-embed-text:latest")


def get_embedding(text: str) -> list[float]:
    """Generate a text embedding using the local Ollama embedding model."""
    try:
        response = httpx.post(
            f"{OLLAMA_BASE_URL}/api/embed",
            json={"model": OLLAMA_EMBED_MODEL, "input": text},
            timeout=120.0,
        )
        response.raise_for_status()
        data = response.json()
        embeddings = data.get("embeddings", [])
        if embeddings and embeddings[0]:
            return embeddings[0]
        print(f"[Ollama Embed] Empty embedding response: {str(data)[:300]}")
    except Exception as e:
        print(f"[Ollama Embed Error] {e}")

    return []


def sync_all_notes(notes):
    # Avoid regenerating every embedding at server startup.
    pass


def add_note_to_vector_store(note):
    try:
        content_block = f"Title: {note['title']}\nTags: {', '.join(note.get('tags', []))}\nContent: {note['content']}"
        embedding = get_embedding(content_block)
        if embedding:
            db.update_note_embedding(note["id"], embedding)
    except Exception as e:
        print(f"[RAG Engine Error] Failed to embed note {note['id']}: {e}")


def delete_note_from_vector_store(note_id):
    # Deletion is natively handled by the database calls.
    pass


def generate_smart_answer(question, document_id=None, image_data=None, user_id=None):
    if image_data:
        return {
            "answer": "Image questions are not supported by the local Llama 3 text model. Ask a text question or use a local vision model.",
            "matched_note": None,
            "keywords": [],
            "related_notes": [],
        }

    # Retrieve relevant note chunks using embeddings from the same local model.
    try:
        query_embedding = get_embedding(question)
        if not query_embedding:
            raise Exception("Ollama could not generate an embedding. Check that Ollama is running and the embedding model is installed.")

        results = db.match_study_notes(
            query_embedding=query_embedding,
            match_threshold=0.3,
            match_count=3,
            filter_document_id=document_id,
            user_id=user_id,
        )
    except Exception as e:
        return {
            "answer": f"Vector search error: {e}",
            "matched_note": None,
            "keywords": [],
            "related_notes": [],
        }

    if not results:
        return {
            "answer": "No relevant notes found for this document." if document_id else "No relevant notes found.",
            "matched_note": None,
            "keywords": [],
            "related_notes": [],
        }

    docs = []
    meta = []
    for result in results:
        content_block = f"Title: {result['title']}\nTags: {', '.join(result.get('tags', []))}\nContent: {result['content']}"
        docs.append(content_block)
        meta.append({
            "id": result["id"],
            "title": result["title"],
            "document_id": result.get("document_id"),
        })

    context = "\n\n---\n\n".join(docs)

    try:
        response = httpx.post(
            f"{OLLAMA_BASE_URL}/api/chat",
            json={
                "model": OLLAMA_CHAT_MODEL,
                "messages": [
                    {
                        "role": "system",
                        "content": "You are a study assistant. Answer clearly using the supplied study context. If the answer is not in the context, say so. Do not invent facts.",
                    },
                    {
                        "role": "user",
                        "content": f"Study context:\n{context}\n\nQuestion: {question}",
                    },
                ],
                "stream": False,
                "options": {"temperature": 0.3, "num_predict": 300},
            },
            timeout=300.0,
        )
        response.raise_for_status()
        answer_text = response.json().get("message", {}).get("content", "").strip()
        if not answer_text:
            raise ValueError("Ollama returned an empty answer.")
    except Exception as e:
        return {
            "answer": f"Local Ollama error: {e}",
            "matched_note": meta[0] if meta else None,
            "keywords": [],
            "related_notes": meta[1:] if len(meta) > 1 else [],
        }

    return {
        "answer": answer_text,
        "matched_note": meta[0] if meta else None,
        "keywords": [],
        "related_notes": meta[1:3] if len(meta) > 1 else [],
    }
