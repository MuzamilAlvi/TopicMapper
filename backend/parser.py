from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

from backend.utils import normalize_whitespace, extract_topic_number


@dataclass(frozen=True)
class TopicEntry:
    number: str
    title: str


def parse_topics_txt(path: str) -> Dict[str, str]:
    """Parse a topics text file into mapping: topic_number -> official_title.

    Supported formats (line-based):
    - 84-Creating New Features from Existing Data
    - 84 - Creating New Features from Existing Data
    - 84: Creating New Features from Existing Data
    - Topic 84: Creating ...

    The parser is lenient: it extracts the first integer from each non-empty line.
    """
    mapping: Dict[str, str] = {}

    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        lines = f.readlines()

    for raw in lines:
        line = normalize_whitespace(raw)
        if not line:
            continue

        # extract first integer token
        num = None
        title = None

        # patterns like: 84-Title  / 84 - Title / 84: Title
        # We'll capture the first 1-6 digit group and treat remaining as title.
        import re

        m = re.match(r"^\s*(?:topic\s*)?(\d{1,6})\s*[-:–—]?\s*(.*)$", line, flags=re.IGNORECASE)
        if m:
            num = m.group(1)
            title = m.group(2).strip()

        if num and title:
            mapping[str(num)] = title

    return mapping


def parse_video_folder(folder: str) -> List[str]:
    files: List[str] = []
    for name in os.listdir(folder):
        full = os.path.join(folder, name)
        if os.path.isfile(full):
            files.append(full)
    return files

