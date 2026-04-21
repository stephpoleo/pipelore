import json
from pathlib import Path

import chromadb
from sentence_transformers import SentenceTransformer

from pipelore.constants import (
    DOCS_PATH,
    DOCS_EXCLUIDOS,
    EMBEDDING_MODEL,
    COLLECTION_NAME,
)
from pipelore.config import TOP_K, DISTANCE_THRESHOLD, TEMPERATURE, MAX_TOKENS
from pipelore.pipeline import (
    cargar_documentos,
    chunkear_documentos,
    generar_embeddings,
    indexar_en_chromadb,
    rag,
)
from pipelore.safety import is_safe

_FINGERPRINT_PATH = Path("./chroma_db/docs_fingerprint.json")


def _compute_fingerprint(folder: Path, excluidos: set[str]) -> dict:
    """Devuelve {filename: mtime} para cada .md indexable en folder."""
    return {
        f.name: f.stat().st_mtime
        for f in folder.glob("**/*.md")
        if f.name not in excluidos
    }


def _load_fingerprint() -> dict:
    if _FINGERPRINT_PATH.exists():
        return json.loads(_FINGERPRINT_PATH.read_text(encoding="utf-8"))
    return {}


def _save_fingerprint(fingerprint: dict) -> None:
    _FINGERPRINT_PATH.parent.mkdir(parents=True, exist_ok=True)
    _FINGERPRINT_PATH.write_text(json.dumps(fingerprint, indent=2), encoding="utf-8")

_REJECTION_MESSAGES = {
    "prompt_too_long": (
        "Tu mensaje es demasiado largo. "
        "Por favor, reformulá tu pregunta en menos de 2000 caracteres."
    ),
    "injection_pattern": (
        "Tu mensaje contiene patrones no permitidos. "
        "Por favor, hacé una pregunta técnica sobre los pipelines."
    ),
    "content_policy": (
        "Tu mensaje no cumple con las políticas de uso. "
        "Por favor, hacé una pregunta técnica sobre los pipelines."
    ),
}


class RAGService:
    def __init__(self) -> None:
        print("Cargando modelo de embeddings...")
        self._model = SentenceTransformer(EMBEDDING_MODEL, trust_remote_code=True)

        self._chroma = chromadb.PersistentClient(path="./chroma_db")

        try:
            self._collection = self._chroma.get_collection(COLLECTION_NAME)
            print(f"Colección '{COLLECTION_NAME}' encontrada — {self._collection.count()} chunks.")
        except Exception:
            self._collection = self._chroma.create_collection(
                name=COLLECTION_NAME,
                metadata={"hnsw:space": "cosine"},
            )

        current = _compute_fingerprint(DOCS_PATH, DOCS_EXCLUIDOS)
        stored = _load_fingerprint()

        if self._collection.count() == 0:
            print("Colección vacía — indexando documentos...")
            self._reindex(current)
        elif current != stored:
            added = set(current) - set(stored)
            modified = {f for f in current if f in stored and current[f] != stored[f]}
            removed = set(stored) - set(current)
            changes = ", ".join(
                [f"+{f}" for f in sorted(added)]
                + [f"~{f}" for f in sorted(modified)]
                + [f"-{f}" for f in sorted(removed)]
            )
            print(f"Cambios detectados en docs/ ({changes}) — reindexando...")
            self._reindex(current)

    def _reindex(self, fingerprint: dict) -> None:
        # Limpiar colección antes de reindexar para evitar duplicados
        self._chroma.delete_collection(COLLECTION_NAME)
        self._collection = self._chroma.create_collection(
            name=COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"},
        )
        docs = cargar_documentos(DOCS_PATH, DOCS_EXCLUIDOS)
        chunks = chunkear_documentos(docs)
        embeddings = generar_embeddings(chunks, self._model)
        indexar_en_chromadb(self._collection, chunks, embeddings)
        _save_fingerprint(fingerprint)
        print(f"Indexación completa — {self._collection.count()} chunks.")

    def query(self, question: str) -> dict:
        """
        Ejecuta el pipeline RAG con safety check previo.

        Returns:
            {"response": str, "sources": list[str], "safe": bool, "reason": str | None}
        """
        classification = is_safe(question)
        if not classification["safe"]:
            reason = classification["reason"]
            return {
                "response": _REJECTION_MESSAGES.get(reason, "No puedo responder esa pregunta."),
                "sources": [],
                "safe": False,
                "reason": reason,
            }

        result = rag(
            question,
            self._collection,
            self._model,
            k=TOP_K,
            distance_threshold=DISTANCE_THRESHOLD,
            temperature=TEMPERATURE,
            max_tokens=MAX_TOKENS,
        )
        return {
            "response": result["response"],
            "sources": result["sources"],
            "safe": True,
            "reason": None,
        }

    def sources(self) -> list[str]:
        """Retorna la lista de filenames únicos indexados en ChromaDB."""
        results = self._collection.get(include=["metadatas"])
        filenames = {
            meta.get("filename", "")
            for meta in results["metadatas"]
            if meta.get("filename")
        }
        return sorted(filenames)
