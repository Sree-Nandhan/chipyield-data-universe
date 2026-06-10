#!/usr/bin/env python3
"""Interactive semantic search CLI for the ChipYield data catalog."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from importlib import import_module

rag = import_module("04_rag_catalog")


def main() -> None:
    print("ChipYield Data Catalog — semantic search (type 'exit' to quit)\n")
    while True:
        try:
            query = input("Ask about models/columns: ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break

        if not query:
            continue
        if query.lower() in {"exit", "quit"}:
            break

        hits = rag.search(query, top_k=3)
        print()
        for i, hit in enumerate(hits, 1):
            meta = hit["metadata"]
            label = meta.get("type", "doc")
            print(f"{i}. [{label}] {hit['document'][:220]}...")
            print(f"   source={hit['id']}  distance={hit['distance']:.4f}\n")


if __name__ == "__main__":
    main()
