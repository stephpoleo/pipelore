from pathlib import Path

DOCS_PATH = Path("docs")
DOCS_EXCLUIDOS = {"ejemplo_proyecto.md", "guia_transformacion_docs.md"}
EMBEDDING_MODEL = "jinaai/jina-embeddings-v2-base-es"
COLLECTION_NAME = "pipelore_docs"
LLM_MODEL = "llama3.1:8b"
SAFETY_MODEL = "llama-guard3:8b"
