import csv
from pathlib import Path
from typing import Optional

from engines.rag_engine import RAGEngine


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_ISO_PATH = PROJECT_ROOT / "data" / "governance" / "ISO"


def load_governance_csv(
    rag_engine: RAGEngine,
    path: Path = DEFAULT_ISO_PATH,
    collection: str = "governance",
) -> int:
    """Load governance rows into the shared collection before workflows run."""
    if not path.exists():
        return 0

    loaded = 0
    csv_paths = [path] if path.is_file() else sorted(path.glob("*.csv"))
    for csv_path in csv_paths:
        with csv_path.open("r", encoding="utf-8-sig", newline="") as source:
            rows = csv.DictReader(source)
            for row_number, row in enumerate(rows, start=2):
                requirement = (row.get("Requirement Text") or "").strip()
                title = (row.get("Clause Title") or "").strip()
                note = (row.get("Note") or "").strip()
                if not any((requirement, title, note)):
                    continue

                content_parts = [
                    f"ISO clause {row.get('ISO Clause', '').strip()}: {title}".strip(),
                    f"Note: {note}" if note else "",
                    f"Requirement: {requirement}" if requirement else "",
                ]
                content = "\n".join(part for part in content_parts if part)
                metadata = {
                    "source": csv_path.name,
                    "source_row": str(row_number),
                    "scope": "global",
                    "knowledge_type": "governance",
                    "iso_clause": (row.get("ISO Clause") or "").strip() or "unknown",
                }
                rag_engine.add_document(content, collection, metadata)
                loaded += 1

    return loaded
