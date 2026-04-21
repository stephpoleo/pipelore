from pathlib import Path

from langchain_text_splitters import MarkdownHeaderTextSplitter
from sentence_transformers import SentenceTransformer
import chromadb
import ollama

from pipelore.constants import COLLECTION_NAME, LLM_MODEL
from pipelore.config import (
    TOP_K,
    DISTANCE_THRESHOLD,
    TEMPERATURE,
    MAX_TOKENS,
    NORMALIZE_EMBEDDINGS,
)


def cargar_documentos(folder: Path, excluidos: set[str]) -> list[dict]:
    """
    Lee todos los archivos .md de una carpeta, excluyendo los archivos en `excluidos`.

    Returns:
        Lista de dicts con keys: 'filename', 'content'
    """
    documents = []
    for file in folder.glob("**/*.md"):
        if file.name in excluidos:
            continue
        content = file.read_text(encoding="utf-8")
        documents.append({"filename": file.name, "content": content})
    return documents


def chunkear_documentos(documents: list[dict]) -> list:
    """
    Fragmenta los documentos usando MarkdownHeaderTextSplitter.
    Cada chunk = una sección del .md, con header y filename en metadata.
    """
    headers_to_split_on = [
        ("#", "Header 1"),
        ("##", "Header 2"),
        ("###", "Header 3"),
    ]
    splitter = MarkdownHeaderTextSplitter(
        headers_to_split_on=headers_to_split_on,
        strip_headers=False,
    )
    all_chunks = []
    for doc in documents:
        chunks = splitter.split_text(doc["content"])
        for chunk in chunks:
            chunk.metadata["filename"] = doc["filename"]
        all_chunks.extend(chunks)
    return all_chunks


def generar_embeddings(
    chunks: list,
    model: SentenceTransformer,
    normalize: bool = NORMALIZE_EMBEDDINGS,
) -> list:
    """
    Genera un vector de embedding para cada chunk.

    Returns:
        Lista de vectores (floats), uno por cada chunk.
    """
    texts = [chunk.page_content for chunk in chunks]
    embeddings = model.encode(texts, show_progress_bar=True, normalize_embeddings=normalize)
    return embeddings.tolist()


def indexar_en_chromadb(collection, chunks: list, embeddings: list) -> None:
    """Indexa los chunks con sus embeddings en ChromaDB."""
    ids = [f"doc_{i:03d}" for i in range(len(chunks))]
    documents = [chunk.page_content for chunk in chunks]
    metadatas = [chunk.metadata for chunk in chunks]
    collection.add(
        ids=ids,
        documents=documents,
        embeddings=embeddings,
        metadatas=metadatas,
    )


def buscar(
    question: str,
    collection,
    model: SentenceTransformer,
    k: int = TOP_K,
    distance_threshold: float = DISTANCE_THRESHOLD,
) -> list[dict]:
    """Devuelve los k chunks más cercanos a la pregunta según distancia coseno.
    Si ninguno pasa el umbral, devuelve el mejor igual — para no dejar la respuesta vacía.
    """
    query_emb = model.encode(question, normalize_embeddings=NORMALIZE_EMBEDDINGS).tolist()
    results = collection.query(
        query_embeddings=[query_emb],
        n_results=k,
    )
    candidates = [
        {"text": doc, "metadata": meta, "distance": dist}
        for doc, meta, dist in zip(
            results["documents"][0],
            results["metadatas"][0],
            results["distances"][0],
        )
    ]
    relevant = [c for c in candidates if c["distance"] <= distance_threshold]
    if not relevant:
        relevant = candidates[:1]
    return relevant


def generar_respuesta(
    question: str,
    chunks: list[dict],
    llm_model: str = LLM_MODEL,
    temperature: float = TEMPERATURE,
    max_tokens: int = MAX_TOKENS,
) -> str:
    """Genera una respuesta en lenguaje natural usando LLaMA."""
    parts = []
    for c in chunks:
        file = c["metadata"].get("filename", "")
        section = c["metadata"].get("Header 2", "")
        parts.append(f"[Fuente: {file} — {section}]\n{c['text']}")
    context = "\n\n---\n\n".join(parts)

    prompt = (
        "Eres un asistente técnico del equipo de datos. "
        "Responde la pregunta usando únicamente la información del contexto proporcionado. "
        "Si la información no está en el contexto, dilo explícitamente.\n\n"
        f"CONTEXTO:\n{context}\n\n"
        f"PREGUNTA:\n{question}\n\n"
        "RESPUESTA:"
    )

    response = ollama.chat(
        model=llm_model,
        messages=[{"role": "user", "content": prompt}],
        options={"temperature": temperature, "num_predict": max_tokens},
    )
    return response["message"]["content"]


def rag(
    question: str,
    collection,
    model: SentenceTransformer,
    k: int = TOP_K,
    distance_threshold: float = DISTANCE_THRESHOLD,
    temperature: float = TEMPERATURE,
    max_tokens: int = MAX_TOKENS,
) -> dict:
    """Orquesta el pipeline completo: busca chunks relevantes y genera la respuesta."""
    chunks = buscar(question, collection, model, k=k, distance_threshold=distance_threshold)
    response_text = generar_respuesta(
        question, chunks, temperature=temperature, max_tokens=max_tokens
    )
    sources = set()
    for c in chunks:
        file = c["metadata"].get("filename", "")
        section = c["metadata"].get("Header 2", "")
        sources.add(f"{file} — {section}")
    return {"response": response_text, "sources": list(sources)}
