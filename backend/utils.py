from __future__ import annotations

import os
import re
from dataclasses import dataclass
from typing import Optional


VIDEO_EXTENSIONS = {".mp4", ".mkv", ".avi", ".mov", ".webm", ".m4v"}


def normalize_whitespace(s: str) -> str:
    return re.sub(r"\s+", " ", s).strip()


def ensure_dir_exists(path: str) -> None:
    os.makedirs(path, exist_ok=True)


def is_video_file(path: str) -> bool:
    ext = os.path.splitext(path)[1].lower()
    return ext in VIDEO_EXTENSIONS


def extract_topic_number(filename: str) -> Optional[str]:
    """Extract topic number from a downloaded filename.

    Examples:
    - AIP301_Topic084_DigiSkills 3.0.mp4 -> "084"
    - ..._Topic001_... -> "001"
    - Topic 01.mp4 -> "01"

    Returns the digits as-is (may include leading zeros).
    """
    base = os.path.basename(filename)
    base_no_ext = os.path.splitext(base)[0]

    # Prefer explicit 'Topic' token.
    # Examples:
    # - AIP301_Topic019_... -> Topic019
    # - Topic 19 - ... -> Topic 19
    m = re.search(r"(?i)\btopic\b\s*([0-9]{1,6})", base_no_ext)
    if m:
        return m.group(1)

    # Also handle cases like 'Topic019' where there is no word boundary after Topic.
    m = re.search(r"(?i)topic([0-9]{1,6})", base_no_ext)
    if m:
        return m.group(1)


    # Fallback: look for a compact pattern like _<number>_ (common in filenames)
    # and avoid matching course/session ids like "AIP301".
    m2 = re.search(r"(?:^|[^0-9])([0-9]{1,6})(?:[^0-9]|$)", base_no_ext)
    if m2:
        return m2.group(1)


    return None


def normalize_topic_number(num: str) -> str:
    """Normalize topic numbers for matching.

    Matching should be tolerant:
    - "01" should equal "1"
    - "001" should equal "1"

    Returns the number without leading zeros (keeps "0" as "0").
    """
    n = str(num).strip()
    if not n:
        return n
    # int() drops leading zeros
    try:
        return str(int(n))
    except ValueError:
        # If not numeric, return trimmed
        return n



@dataclass(frozen=True)
class ParsedFile:
    original_path: str
    original_filename: str
    topic_number: Optional[str]
    extension: str

