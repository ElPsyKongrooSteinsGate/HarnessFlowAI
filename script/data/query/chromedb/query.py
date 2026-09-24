"""Query the local HarnessFlowAI ChromaDB store.

Examples:
    python script/data/query/chromedb/query.py --list
    python script/data/query/chromedb/query.py --collection finance-governance --query "invoice approval"
    python script/data/query/chromedb/query.py --collection finance-governance --get
"""

import argparse
import json
from pathlib import Path
from typing import Any, Dict

import chromadb


PROJECT_ROOT = Path(__file__).resolve().parents[4]
DEFAULT_STORE = PROJECT_ROOT / "data" / "chroma"


def create_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Query HarnessFlowAI ChromaDB data.")
    parser.add_argument(
        "--store",
        type=Path,
        default=DEFAULT_STORE,
        help="ChromaDB persistence directory.",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        dest="list_collections",
        help="List available collections.",
    )
    parser.add_argument(
        "--collection",
        help="Collection to query or inspect.",
    )
    parser.add_argument(
        "--query",
        help="Semantic query text.",
    )
    parser.add_argument(
        "--get",
        action="store_true",
        help="Print all records in the selected collection.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=5,
        help="Maximum semantic query results. Default: 5.",
    )
    return parser


def print_json(value: Any) -> None:
    print(json.dumps(value, indent=2, ensure_ascii=True))


def main() -> int:
    args = create_parser().parse_args()
    client = chromadb.PersistentClient(path=str(args.store))

    if args.list_collections:
        print_json({"collections": [collection.name for collection in client.list_collections()]})
        return 0

    if not args.collection:
        raise SystemExit("--collection is required with --query or --get.")

    try:
        collection = client.get_collection(args.collection)
    except Exception as exc:
        raise SystemExit(f"Collection not found: {args.collection}") from exc

    if args.query:
        results: Dict[str, Any] = collection.query(
            query_texts=[args.query],
            n_results=args.limit,
        )
        print_json(results)
        return 0

    if args.get:
        print_json(collection.get())
        return 0

    raise SystemExit("Provide --list, --query, or --get.")


if __name__ == "__main__":
    raise SystemExit(main())
