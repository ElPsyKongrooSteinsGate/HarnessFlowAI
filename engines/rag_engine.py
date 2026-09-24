import re
import hashlib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

import chromadb


@dataclass
class GovernanceDocument:
    content: str
    collection: str
    metadata: Dict[str, str] = field(default_factory=dict)


class RAGEngine:
    """Workflow-scoped governance retriever backed by persistent ChromaDB."""

    def __init__(self, persist_path: str = "data/chroma", use_chromadb: bool = True):
        self._documents: List[GovernanceDocument] = []
        self.use_chromadb = use_chromadb
        self._client = None
        if use_chromadb:
            Path(persist_path).parent.mkdir(parents=True, exist_ok=True)
            self._client = chromadb.PersistentClient(path=persist_path)

    def add_document(
        self,
        content: str,
        collection: str,
        metadata: Optional[Dict[str, str]] = None,
    ) -> None:
        if self.use_chromadb:
            collection_handle = self._get_collection(collection)
            document_id = hashlib.sha256(
                f"{collection}:{content}".encode("utf-8")
            ).hexdigest()
            chroma_metadata = dict(metadata or {})
            chroma_metadata.setdefault("collection", collection)
            collection_handle.upsert(
                ids=[document_id],
                documents=[content],
                metadatas=[chroma_metadata],
            )
            return

        self._documents.append(
            GovernanceDocument(
                content=content,
                collection=collection,
                metadata=metadata or {},
            )
        )

    async def retrieve(
        self,
        query: str,
        collection: str,
        limit: int = 5,
    ) -> List[str]:
        if self.use_chromadb:
            collection_handle = self._get_collection(collection)
            result = collection_handle.query(
                query_texts=[query],
                n_results=limit,
            )
            documents = result.get("documents", [[]])[0]
            return [document for document in documents if document]

        query_terms = self._terms(query)
        candidates = [
            document
            for document in self._documents
            if document.collection == collection
        ]
        ranked = sorted(
            candidates,
            key=lambda document: len(query_terms.intersection(self._terms(document.content))),
            reverse=True,
        )
        return [document.content for document in ranked[:limit]]

    def _get_collection(self, collection: str):
        if self._client is None:
            raise RuntimeError("ChromaDB is not configured.")
        return self._client.get_or_create_collection(name=collection)

    @staticmethod
    def _terms(text: str) -> set[str]:
        return set(re.findall(r"[a-z0-9_]+", text.lower()))
