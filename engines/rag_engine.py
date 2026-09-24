import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class GovernanceDocument:
    content: str
    collection: str
    metadata: Dict[str, str] = field(default_factory=dict)


class RAGEngine:
    """Small dependency-free retriever for workflow governance knowledge."""

    def __init__(self):
        self._documents: List[GovernanceDocument] = []

    def add_document(
        self,
        content: str,
        collection: str,
        metadata: Optional[Dict[str, str]] = None,
    ) -> None:
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

    @staticmethod
    def _terms(text: str) -> set[str]:
        return set(re.findall(r"[a-z0-9_]+", text.lower()))
