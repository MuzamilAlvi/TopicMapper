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
    """Extract the topic number from a downloaded filename.

    Expected patterns (examples):
    - AIP301_Topic084_DigiSkills 3.0.mp4
    - Topic001.mp4
    - ..._Topic123_...

    Returns a string topic number without leading/trailing whitespace.
    """
    base = os.path.basename(filename)
    base_no_ext = os.path.splitext(base)[0]

    # Prefer explicit 'Topic' token
    m = re.search(r"(?i)\btopic\s*([0-9]{1,6})\b", base_no_ext)
    if m:
        return m.group(1)

    # Fallback: any standalone number group (not too aggressive)
    m2 = re.search(r"(^|[^0-9])([0-9]{1,6})([^0-9]|$)", base_no_ext)
    if m2:
        return m2.group(2)

    return None


@dataclass(frozen=True)
class ParsedFile:
    original_path: str
    original_filename: str
    topic_number: Optional[str]
    extension: str

