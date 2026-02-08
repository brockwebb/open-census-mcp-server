#!/usr/bin/env python3
"""Migrate staging JSON from old `source` field to new `provenance` field.

Old format:
    "source": {"document": "ACS-GEN-001", "section": "Ch. 7", "extraction_method": "manual"}

New format:
    "provenance": {
        "sources": [{"document": "ACS-GEN-001", "section": "Ch. 7", "page": null, "extraction_method": "manual"}],
        "synthesis_note": null,
        "confidence": "grounded",
        "limitations": null
    }

Also parses page numbers from section strings like "Ch. 3, p. 13" → section="Ch. 3", page=13
"""

import json
import re
import sys
from pathlib import Path


def parse_section_page(section_str: str | None) -> tuple[str | None, int | str | None]:
    """Extract page number from section string if embedded."""
    if section_str is None:
        return None, None

    # Pattern: "Ch. 3, p. 13" or "Ch. 7, pp. 53-57"
    match = re.match(r'^(.+?),\s*pp?\.\s*(.+)$', section_str)
    if match:
        section = match.group(1).strip()
        page_str = match.group(2).strip()
        # Try int first, fall back to string for ranges
        try:
            return section, int(page_str)
        except ValueError:
            return section, page_str

    return section_str, None


def migrate_item(item: dict) -> dict:
    """Migrate a single context item from source to provenance."""
    old_source = item.pop("source", None)

    if old_source is None:
        # No source at all — create minimal provenance flagged for review
        item["provenance"] = {
            "sources": [{
                "document": "NEEDS-CITATION",
                "section": None,
                "page": None,
                "extraction_method": "manual"
            }],
            "synthesis_note": None,
            "confidence": "grounded",
            "limitations": "MIGRATION: No source existed. Needs citation."
        }
    else:
        section, page = parse_section_page(old_source.get("section"))
        item["provenance"] = {
            "sources": [{
                "document": old_source["document"],
                "section": section,
                "page": page,
                "extraction_method": old_source.get("extraction_method", "manual")
            }],
            "synthesis_note": None,
            "confidence": "grounded",
            "limitations": None
        }

    return item


def migrate_file(filepath: Path) -> int:
    """Migrate a single JSON staging file. Returns count of items migrated."""
    with open(filepath, 'r') as f:
        items = json.load(f)

    if not isinstance(items, list):
        return 0

    # Check if already migrated
    if items and "provenance" in items[0]:
        print(f"  SKIP (already migrated): {filepath.name}")
        return 0

    migrated = [migrate_item(item) for item in items]

    with open(filepath, 'w') as f:
        json.dump(migrated, f, indent=2, ensure_ascii=False)

    return len(migrated)


def main():
    staging_root = Path(__file__).parent.parent / "staging"

    if not staging_root.exists():
        print(f"ERROR: staging directory not found at {staging_root}")
        sys.exit(1)

    total = 0
    for json_file in sorted(staging_root.rglob("*.json")):
        if json_file.name == "manifest.json":
            continue
        count = migrate_file(json_file)
        if count > 0:
            print(f"  ✓ {json_file.relative_to(staging_root)}: {count} items")
            total += count

    print(f"\n✅ Migrated {total} items total.")


if __name__ == "__main__":
    main()
