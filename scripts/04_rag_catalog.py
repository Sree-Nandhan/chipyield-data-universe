#!/usr/bin/env python3
"""Build semantic search index over dbt model docs and column glossary."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import chromadb
import yaml
from chromadb.utils import embedding_functions
from sentence_transformers import SentenceTransformer

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SCHEMA_PATH = PROJECT_ROOT / "models" / "schema.yml"
GLOSSARY_PATH = PROJECT_ROOT / "docs" / "data_catalog_glossary.md"
RAG_STORE = PROJECT_ROOT / "rag_store"
COLLECTION_NAME = "chipyield_data_catalog"


def load_schema_docs(path: Path) -> list[dict]:
    content = yaml.safe_load(path.read_text())
    documents: list[dict] = []

    for model in content.get("models", []):
        model_name = model["name"]
        model_desc = model.get("description", "").strip()
        documents.append(
            {
                "id": f"model::{model_name}",
                "text": f"Model {model_name}: {model_desc}",
                "metadata": {"type": "model", "name": model_name},
            }
        )

        for col in model.get("columns", []):
            col_name = col["name"]
            col_desc = col.get("description", "").strip()
            documents.append(
                {
                    "id": f"column::{model_name}.{col_name}",
                    "text": f"Column {col_name} in model {model_name}: {col_desc}",
                    "metadata": {
                        "type": "column",
                        "model": model_name,
                        "column": col_name,
                    },
                }
            )

    return documents


def load_glossary_docs(path: Path) -> list[dict]:
    if not path.exists():
        return []

    text = path.read_text()
    chunks = [chunk.strip() for chunk in text.split("\n## ") if chunk.strip()]
    documents = []
    for i, chunk in enumerate(chunks):
        title = chunk.split("\n", 1)[0]
        documents.append(
            {
                "id": f"glossary::{i}",
                "text": chunk,
                "metadata": {"type": "glossary", "title": title},
            }
        )
    return documents


def build_index(model_name: str = "all-MiniLM-L6-v2") -> int:
    RAG_STORE.mkdir(exist_ok=True)

    docs = load_schema_docs(SCHEMA_PATH) + load_glossary_docs(GLOSSARY_PATH)
    if not docs:
        raise RuntimeError("No documents found for RAG index.")

    embedder = SentenceTransformer(model_name)
    client = chromadb.PersistentClient(path=str(RAG_STORE))
    ef = embedding_functions.SentenceTransformerEmbeddingFunction(model_name=model_name)

    # Reset collection for idempotent rebuilds
    try:
        client.delete_collection(COLLECTION_NAME)
    except Exception:
        pass

    collection = client.create_collection(name=COLLECTION_NAME, embedding_function=ef)

    collection.add(
        ids=[d["id"] for d in docs],
        documents=[d["text"] for d in docs],
        metadatas=[d["metadata"] for d in docs],
    )

    manifest = {
        "collection": COLLECTION_NAME,
        "document_count": len(docs),
        "embedding_model": model_name,
    }
    (RAG_STORE / "manifest.json").write_text(json.dumps(manifest, indent=2))

    print(f"RAG index built: {len(docs)} documents -> {RAG_STORE}")
    return len(docs)


def search(query: str, top_k: int = 5, model_name: str = "all-MiniLM-L6-v2") -> list[dict]:
    client = chromadb.PersistentClient(path=str(RAG_STORE))
    ef = embedding_functions.SentenceTransformerEmbeddingFunction(model_name=model_name)
    collection = client.get_collection(name=COLLECTION_NAME, embedding_function=ef)

    results = collection.query(query_texts=[query], n_results=top_k)
    hits = []
    for i in range(len(results["ids"][0])):
        hits.append(
            {
                "id": results["ids"][0][i],
                "document": results["documents"][0][i],
                "metadata": results["metadatas"][0][i],
                "distance": results["distances"][0][i],
            }
        )
    return hits


def main() -> None:
    parser = argparse.ArgumentParser(description="Build or query ChipYield data catalog RAG index")
    parser.add_argument("--build", action="store_true", help="Build/rebuild the index")
    parser.add_argument("--query", type=str, help="Semantic search query")
    parser.add_argument("--top-k", type=int, default=5)
    args = parser.parse_args()

    if args.build:
        build_index()
    elif args.query:
        hits = search(args.query, top_k=args.top_k)
        print(json.dumps(hits, indent=2))
    else:
        parser.error("Provide --build or --query")


if __name__ == "__main__":
    main()
