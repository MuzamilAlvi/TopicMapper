from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import List, Dict, Any, Optional


@dataclass
class FilePlan:
    original_path: str
    original_filename: str
    topic_number: Optional[str]
    official_title: Optional[str]
    new_filename: Optional[str]
    status: str  # matched | unmatched | duplicate | error
    reason: str = ""


def build_report(plans: List[FilePlan]) -> Dict[str, Any]:
    renamed = [p for p in plans if p.status == "matched"]
    skipped_unmatched = [p for p in plans if p.status == "unmatched"]
    duplicates = [p for p in plans if p.status == "duplicate"]
    errors = [p for p in plans if p.status == "error"]

    def to_list(items):
        return [asdict(p) for p in items]

    return {
        "counts": {
            "matched": len(renamed),
            "unmatched": len(skipped_unmatched),
            "duplicates": len(duplicates),
            "errors": len(errors),
        },
        "files": to_list(plans),
        "renamed": to_list(renamed),
        "unmatched": to_list(skipped_unmatched),
        "duplicates": to_list(duplicates),
        "errors": to_list(errors),
    }

